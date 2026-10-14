# CampusFlow
## Problem
- Learn2Earn campus staff who receive technical support requests: Wi-Fi outages, faulty laptops, broken dev environments, inaccessible platforms and several others find it difficult to track, record and attend to these complaints due to the multitasking nature of their work. This results to the loss of informal complaints leaving several fellows' needs unattended.

## Solution
- CampusFlow is a command line program that records each request as a ticket, calculates priority from urgency and the number of people affected, assigns it, tracks it through its stages, shows a work queue and reports, and saves data to a file so it survives a restart. This helps solve the loss of informal requests by making sure there is a proper platform for making requests, complaints for the coding mentors to be able to conveniently attend to.

## What makes it useful
- CampusFlow is very useful in the sense that its existence will make it much easier for mentors to attend to all requests and complaints from fellows at their given convenience without losing any one behind. The most interesting part of CampusFlow is that it arranges these requests by order of urgency, this helps the coding mentors to know which request requires more and quick attention and which one requires less attention. 

## Features
- **Create a ticket** with a title, category, urgency and number of affected users. The ID and the priority are worked out by the program.
- **List and view** tickets.
- **Assign** a ticket to a staff member.
- **Status workflow:** open, in progress, resolved, with rules about what may follow what, and a way to reopen a resolved ticket.
- **Work queue** of open tickets, most urgent first.
- **Report** with the total and the counts by status and priority.
- **SLA attention queue** of unresolved tickets, overdue first, with the deadline on each line.
- **Escalation** of overdue tickets, recorded once per SLA cycle and never changing a ticket's status, priority or assignee.
- **Metrics** with the counts by status and priority, the overdue unresolved total and the escalations in the current cycle.
- **History** of every change to a ticket, and an **Engineering Knowledge Lab** quiz.
- **Saved to a file**, so tickets and their history survive a restart.

## Requirements
Python 3 (written and tested with Python 3.13). There is nothing to install: the program uses only the Python standard library.

## How to run
From the project folder (the one that contains `campusflow/`):

```bash
python3 -m campusflow.main
```

(On some computers the command is `python` instead of `python3`.) Do not run `python3 campusflow/main.py`; the program must be started as a module so its imports work.

Tickets are saved in `data/tickets.json`, which the program creates on the first change. The file is listed in `.gitignore`, so it is never committed. Delete it to start with an empty list.

If `data/tickets.json` is damaged (for example, edited by hand into invalid JSON), the program prints a message and stops without changing the file, so no data is lost. Fix or move the file and start again.

## The menu
```
=== CampusFlow ===
1. Create a ticket
2. List all tickets
3. View one ticket
4. Assign a ticket
5. Change a ticket's status
6. Reopen a resolved ticket
7. Show the work queue
8. Show the report
9. Escalate overdue tickets
10. Show the SLA attention queue
11. Show ticket and SLA metrics
12. Show a ticket's history
13. Engineering Knowledge Lab
0. Exit
```
Wrong answers never crash the program: it shows an `Error: ...` message and carries on.

An example session (menu lines left out):
```
Title: Wi-Fi is down in Lab 2
Category (Network, Hardware, Software, Other): network
Urgency (low, medium, high): high
Affected users: 15
Created T001 with priority critical.

Ticket ID: t002
Assign to: Sam
T002 is now assigned to Sam.

Work queue (most urgent first):
1. T001 | Wi-Fi is down in Lab 2 | Network | critical | open | unassigned
```

## A ticket
Each ticket has: `id` (T001, T002, ...), `title`, `category` (Network, Hardware, Software or Other), `urgency` (low, medium or high), `affected_users` (a positive whole number), `priority` (worked out, never typed in), `status` and `assigned_to`.

## How priority is worked out
The first rule that matches wins:

1. high urgency **and** 10 or more affected users: **critical**
2. high urgency **or** 10 or more affected users: **high**
3. medium urgency **or** 3 or more affected users: **medium**
4. anything else: **low**

The work queue shows open tickets in the order critical, high, medium, low. Tickets with the same priority are ordered by their ticket number.

## Status rules
| From | To | Allowed? |
|---|---|---|
| open | in progress | only if the ticket is assigned |
| in progress | resolved | yes |
| resolved | open | only with "Reopen" (the assignee is kept) |
| anything else | | rejected |

A resolved ticket cannot be assigned or changed until it is reopened.

## SLA deadlines and escalation
Each ticket gets a deadline, `due_at`, worked out from its priority and the start of its current cycle (the creation time, or the reopen time after a reopen): critical 60 minutes, high 4 hours, medium 1 day, low 2 days. A ticket is overdue once the current time is strictly past its deadline; a resolved ticket is never overdue.

The SLA attention queue lists the unresolved tickets with overdue ones first, then by earliest deadline, then by ticket number. "Escalate overdue tickets" records one `ESCALATE` event per overdue ticket per cycle, so running it twice in the same cycle adds nothing the second time; a reopened ticket may be escalated again in its new cycle. Escalation never changes a ticket's status, priority or assignee.

## Project layout
```
campusflow/
  main.py       the menu (the only file that uses input() and print())
  tickets.py    ticket rules: constants, validation, priority, IDs, create
  storage.py    saving and loading data/tickets.json
  workflow.py   assign, change status, reopen, work queue
  reports.py    the summary report, the SLA attention queue and metrics
  sla.py        deadlines: how due_at is worked out and what "overdue" means
  history.py    the append-only event history
tests/          unit tests for every module (unittest)
docs/           design decisions
```
The design decisions (what we agreed before writing code, and why) are in [docs/design-decisions.md](docs/design-decisions.md).

## Running the tests
```bash
python3 -m unittest discover -s tests -v
```
The tests build their own tickets by hand and save only into temporary folders, so they never touch `data/tickets.json`.

## How we worked
- One repository, a separate branch for every feature, a pull request for each, and a review from the other engineer before merging. Nobody worked directly on `main`.
- Work was tracked in GitHub Issues #1 to #6.

## Use of AI
We used an AI assistant (Claude) as a tutor and reviewer, and for some of the code. Because we already understand what the project requires, the assistant supplied the code for several parts at our request; each pull request that contains such code says so in its description. We ran and tested the code, checked it by breaking it on purpose, and kept an AI learning log for each of us recording what we asked, what we were given, what we checked and what we can now explain ourselves. See the logs in `docs/`.

## Team
- Engineer A: Terngu David Ayande (GitHub: tayande). Built ticket creation and validation, the priority engine, JSON storage and the main menu
- Engineer B: Peace Onma Oigoga (GitHub: onma77). Built assignment, status workflow, work queue and reports.