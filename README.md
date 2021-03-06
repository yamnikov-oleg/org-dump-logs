# org-dump-logs

A small Python script to collect the log items from your org files and write them in chronological order in org-diary-like manner.

Given this file:

```org
* Project A

** DONE Task 1

:LOGBOOK:
- Note taken on [2018-01-01 Mon 20:00] \\
  Started working on the task.
- State "DONE" from "TODO" [2018-01-01 Mon 21:00] \\
  Wasn't that hard.
:END:

* Project B

** TODO Task 2

:LOGBOOK:
- Note taken on [2018-01-02 Tue 20:00] \\
  This task will have to wait.
:END:
```

This script produces this file:

```org
* 2018

** 2018-01 January

*** 2018-01-01 Monday

- =Task 1/Project A=
  Note taken on [2018-01-01 Mon 20:00] \\
  Started working on the task.
- =Task 1/Project A=
  State "DONE" from "TODO" [2018-01-01 Mon 21:00] \\
  Wasn't that hard.

*** 2018-01-02 Tuesday

- =Task 2/Project B=
  Note taken on [2018-01-02 Tue 20:00] \\
  This task will have to wait.
```

Or with `SMART_FORMAT` set to `True`:

```org
* 2018

** 2018-01 January

*** 2018-01-01 Monday

- [2018-01-01 Mon 20:00] Note =Task 1/Project A=
  Started working on the task.
- [2018-01-01 Mon 21:00] "DONE" =Task 1/Project A=
  Wasn't that hard.

*** 2018-01-02 Tuesday

- [2018-01-02 Tue 20:00] Note =Task 2/Project B=
  This task will have to wait.
```

## Usage

```
python org_dump_logs.py ./file1.org ./file2.org > ./out.org
```

There are some settings at the top the script for basic customization.

## Installation

Clone the repo:

```
git clone https://github.com/yamnikov-oleg/org-dump-logs
cd org-dump-logs
```

Setup virtualenv:

```
virtualenv -p python3 venv
source venv/bin/activate
```

Install [PyOrgMode](https://github.com/bjonnh/PyOrgMode):

```
git submodule update --init
cd PyOrgMode
python setup.py install
cd ..
```

Done!
