import os
import re
import sys
import time
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
REVERSE_ITEM_LOCATION = False

# If True, item's file name will be included in its location
# /tasks.org/Top Heading/Second Heading/Third Heading/
INCLUDE_FILE_NAME = False

# Regex for timestamps on the first line of an item
TIMESTAMP_RE = re.compile('\[[^\]]+]')

# /Settings

class LogItem:
    """Struct class for a log item"""
    INDENT = '  '

    def __init__(self, time: time.struct_time, lines: List[str],
                 headings: List[OrgNode.Element], filepath: str):
        # The timestamp of this item
        self.time = time
        # The text of this item
        self.lines = lines
        # The list of heading nodes of this item from top down
        self.headings = headings
        # The path to the file, where this item has been read
        self.filepath = filepath

    @property
    def location(self) -> List[str]:
        """Returns the file name of this item and all its headings from top down"""
        loc = [os.path.basename(self.filepath)]
        for h in self.headings:
            loc.append(h.heading.strip())

        return loc

    def output(self) -> str:
        """Returns the string representation on this item as should be written
        to the stdout.
        """
        output = self.lines[0] + '\n'
        for line in self.lines[1:]:
            output += self.INDENT + line + '\n'

        location = self.location
        if not INCLUDE_FILE_NAME:
            location = location[1:]
        if REVERSE_ITEM_LOCATION:
            location = list(reversed(location))

        output += self.INDENT + '/' + '/'.join(location) + '/\n'
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


def parse_drawer(drawer: OrgDrawer.Element,
                 headings: List[OrgNode.Element], filepath: str) -> List[LogItem]:
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
            item = LogItem(time, current_item_lines, headings, filepath)
            items.append(item)

        current_item_lines = [line]

    if current_item_lines:
        item = LogItem(time, current_item_lines, headings, filepath)
        items.append(item)

    return items


def traverse_node(node: OrgNode.Element,
                  headings: List[OrgNode.Element], filepath: str) -> List[LogItem]:
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


def main():
    log_items = []
    for arg in sys.argv:
        log_items += traverse_file(arg)

    log_items.sort(key=lambda item: item.time)
    for item in log_items:
        print(item.output(), end='')

if __name__ == '__main__':
    main()
