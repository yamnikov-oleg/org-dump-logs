import locale
import os
import re
import sys
import time
from datetime import date
from io import TextIOBase
from typing import List, Optional

from PyOrgMode import OrgDataStructure, OrgDate, OrgDrawer, OrgNode

# Settings

# The name of the drawer from which items will be read
LOGBOOK_DRAWER = 'LOGBOOK'

# The prefix for clock items, which will be ignored
CLOCK_PREFIX = 'CLOCK:'

# If True, item's location will be reversed
# from /Top Heading/Second Heading/Third Heading/
# to   /Third Heading/Second Heading/Top Heading/
REVERSE_ITEM_LOCATION = True

# If True, item's file name will be included in its location
# /tasks.org/Top Heading/Second Heading/Third Heading/
INCLUDE_FILE_NAME = False

# Character to put on the both sides of item's location. E.g. '*', '/' or '='
WRAP_ITEM_LOCATION_IN = '='

# Regex for timestamps on the first line of an item
TIMESTAMP_RE = re.compile('\[[^\]]+]')

# Locale, used for writing names of months and week days.
# E.g. ('en_US', 'UTF-8')
LOCALE = locale.getlocale()

# Org title template
TITLE = 'Logs from {filenames}'

# /Settings


class LogItem:
    """Struct class for a log item"""
    INDENT = '  '

    def __init__(self, lines: List[str], headings: List[OrgNode.Element],
                 filepath: str):
        # The timestamp of this item
        self.time = try_parse_datetime(lines[0])
        # The text of this item
        self.lines = list(lines)
        # The list of heading nodes of this item from top down
        self.headings = headings
        # The path to the file, where this item has been read
        self.filepath = filepath

        if not self.time:
            raise ValueError("No timestamp: {}".format(lines[0]))

    @property
    def location(self) -> List[str]:
        """Returns the file name of this item and all its headings from top down"""
        loc = [os.path.basename(self.filepath)]
        for h in self.headings:
            loc.append(h.heading.strip())

        return loc

    @property
    def date(self) -> date:
        return date(self.time.tm_year, self.time.tm_mon, self.time.tm_mday)

    def output(self) -> str:
        """Returns the string representation on this item as should be written
        to the stdout.
        """
        location = self.location
        if not INCLUDE_FILE_NAME:
            location = location[1:]
        if REVERSE_ITEM_LOCATION:
            location = list(reversed(location))
        location_str = '/'.join(location)

        output = '- ' + WRAP_ITEM_LOCATION_IN + location_str + WRAP_ITEM_LOCATION_IN + '\n'
        output += self.INDENT + self.lines[0][2:] + '\n'
        for line in self.lines[1:]:
            output += self.INDENT + line + '\n'

        return output


def try_parse_datetime(log_line: str) -> Optional[time.struct_time]:
    """Tries to find a timestamp in the given log line and returns its value
    when found. If timestamp was not found, returns None.
    """
    match = TIMESTAMP_RE.search(log_line)
    if not match:
        return None

    timestamp_str = match.group(0)
    try:
        timed, weekdayed, time_struct = OrgDate().parse_datetime(timestamp_str)
        return time_struct
    except AttributeError:
        # 'NoneType' object has no attribute 'group'
        return None


def parse_drawer(drawer: OrgDrawer.Element, headings: List[OrgNode.Element],
                 filepath: str) -> List[LogItem]:
    """Parses the logbook drawer and returns all the log items in it."""
    items = []
    current_item_lines = []
    for line in drawer.content:
        if line.startswith(CLOCK_PREFIX):
            continue

        if not line.startswith('- '):
            current_item_lines.append(line)
            continue

        time = try_parse_datetime(line)
        if not time:
            current_item_lines.append(line)
            continue

        if current_item_lines:
            item = LogItem(current_item_lines, headings, filepath)
            items.append(item)

        current_item_lines = [line]

    if current_item_lines:
        item = LogItem(current_item_lines, headings, filepath)
        items.append(item)

    return items


def traverse_node(node: OrgNode.Element, headings: List[OrgNode.Element],
                  filepath: str) -> List[LogItem]:
    """Parses the given heading node and returns all the log items in it."""
    headings_with_self = headings + [node]
    if node.heading == '':
        # The root element has not heading
        headings_with_self = headings

    log_items = []
    for item in node.content:
        if isinstance(item, OrgNode.Element):
            log_items += traverse_node(item, headings_with_self, filepath)

        if isinstance(item, OrgDrawer.Element) and item.name == LOGBOOK_DRAWER:
            log_items += parse_drawer(item, headings_with_self, filepath)

    return log_items


def traverse_file(path: str) -> List[LogItem]:
    """Parses the given org file and returns all the log items in it."""
    org_file = OrgDataStructure()
    org_file.load_from_file(path)
    return traverse_node(org_file.root, [], path)


def write_as_tree(log_items: List[LogItem], out: TextIOBase):
    def write_date_headings(d: date, upto: str):
        if upto == 'day':
            out.write('*** {}\n'.format(d.strftime('%Y-%m-%d %A')))
        elif upto == 'month':
            out.write('** {}\n'.format(d.strftime('%Y-%m %B')))
            out.write('*** {}\n'.format(d.strftime('%Y-%m-%d %A')))
        elif upto == 'year':
            out.write('* {}\n'.format(d.strftime('%Y')))
            out.write('** {}\n'.format(d.strftime('%Y-%m %B')))
            out.write('*** {}\n'.format(d.strftime('%Y-%m-%d %A')))
        else:
            raise ValueError(upto)

    last_date = None
    for item in log_items:
        if last_date is None:
            last_date = item.date
            write_date_headings(item.date, upto='year')

        if last_date != item.date:
            if last_date.year != item.date.year:
                write_date_headings(item.date, upto='year')
            elif last_date.month != item.date.month:
                write_date_headings(item.date, upto='month')
            elif last_date.day != item.date.day:
                write_date_headings(item.date, upto='day')
            last_date = item.date

        out.write(item.output())
        out.flush()


def main():
    locale.setlocale(locale.LC_ALL, LOCALE)
    filepaths = sys.argv[1:]

    log_items = []
    for path in filepaths:
        log_items += traverse_file(path)

    filenames = []
    for path in filepaths:
        name = os.path.basename(path)
        filenames.append(name)

    title = TITLE.format(filenames=', '.join(filenames))
    sys.stdout.write('#+TITLE: {}\n'.format(title))
    sys.stdout.write('#+DATE: {}\n'.format(date.today().strftime('%Y-%m-%d')))
    sys.stdout.write('\n')
    sys.stdout.flush()

    log_items.sort(key=lambda item: item.time)
    write_as_tree(log_items, sys.stdout)


if __name__ == '__main__':
    main()
