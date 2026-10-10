# Design Decisions

This document records what Engineer A and Engineer B agreed before writing code, so our two halves of CampusFlow fit together. If a decision changes, we update this file in a reviewed pull request.

## 1. Ownership

| | Engineer A (Terngu David Ayande) | Engineer B (Peace Onma Oigoga) |
|---|---|---|
| Features | F1 Create, F2 List/View, F7 JSON persistence | F3 Assign, F4 Workflow, F5 Work queue, F6 Reports |
| Modules | `tickets.py`, `storage.py`, `main.py` | `workflow.py`, `reports.py` |
| Tests | `test_tickets.py`, `test_storage.py` | `test_workflow.py` |
| GitHub Issues | #1, #2, #3 | #4, #5 |
| Shared | #6 documentation, reviewing each other's pull requests, AI learning logs, final demonstration | |

`main.py` (the menu) is created by Engineer A. Engineer B adds her own menu options to it in her pull request.

## 2. Ticket structure

A ticket is a dictionary with these keys: `id`, `title`, `category`, `urgency`, `affected_users`, `priority`, `status`, `assigned_to`.

- `id`: generated automatically (T001, T002, ...)
- `category`: Network, Hardware, Software or Other
- `urgency`: low, medium or high
- `affected_users`: a positive integer
- `priority`: critical, high, medium or low (calculated, never typed in)
- `status`: open, in_progress or resolved
- `assigned_to`: `None` until a staff name is assigned

The constants `CATEGORIES`, `URGENCIES`, `STATUSES` and `PRIORITIES` live in `campusflow/tickets.py`.

## 3. Shared function contracts

Every function takes the ticket list as its first parameter. Helper functions inside a module are the owner's choice; only these are shared.

| Module | Function | Returns | Raises `ValueError` when |
|---|---|---|---|
| `tickets.py` | `get_ticket(tickets, ticket_id)` | the ticket | the ID is unknown |
| `tickets.py` | `create_ticket(tickets, title, category, urgency, affected_users)` | the new ticket | any input is invalid |
| `storage.py` | `save_tickets(tickets, path=DEFAULT_PATH)` | nothing | |
| `storage.py` | `load_tickets(path=DEFAULT_PATH)` | list of tickets (empty if the file is missing) | the JSON is malformed |
| `workflow.py` | `assign_ticket(tickets, ticket_id, staff_name)` | the ticket | unknown ID, blank name, ticket is resolved |
| `workflow.py` | `change_status(tickets, ticket_id, new_status)` | the ticket | the transition is not allowed |
| `workflow.py` | `reopen_ticket(tickets, ticket_id)` | the ticket | the ticket is not resolved |
| `workflow.py` | `get_work_queue(tickets)` | list of tickets in order | |
| `reports.py` | `build_report(tickets)` | dictionary: `total`, `by_status`, `by_priority` | |

## 4. Decisions

**D1. One repository, separate branches.** Nobody works directly on `main`. Each feature is built on its own branch, opened as a pull request, reviewed by the other engineer, and merged only after approval. *Why: this is the required workflow and it keeps `main` working.*

**D2. Tickets are a list of dictionaries, passed as the first parameter.** No global variables. Functions change the list in place. *Why: functions can be tested with any list, and there is no hidden shared state.*

**D3. Errors are raised as `ValueError` with a clear message.** The menu in `main.py` catches it and prints the message. All checks happen before any change, so a rejected action never corrupts a ticket. *Why: one simple way to signal failure that tests can check with `assertRaises`.*

**D4. No `input()` or `print()` in logic functions.** Only `main.py` talks to the user. *Why: the logic can be tested without typing anything.*

**D5. Return values.** Functions that create or change a ticket return that ticket. *Why: callers and tests can see the result immediately.*

**D6. Input normalisation.** Spaces are stripped everywhere. Category is matched ignoring case and stored in its canonical form (`network` becomes `Network`). Urgency is stored in lowercase. Typed ticket IDs are stripped and uppercased (`t001` becomes `T001`). *Why: consistent stored data, friendly input.*

**D7. `affected_users` must be a positive whole number.** An integer or a string of digits is accepted. Zero, negatives, decimals, text, blanks and booleans are rejected. It is stored as an integer. *Why: it matches the specification and keeps the priority rules reliable.*

**D8. The next ID is the highest existing number plus one.** It is not the ticket count. *Why: IDs stay unique after a reload.*

**D9. The work queue contains only tickets with status `open`.** In-progress and resolved tickets are excluded. *Why: the specification calls it the "open-ticket queue". This is our interpretation and is easy to change in one place.*

**D10. Status workflow.**

| From | To | Allowed? |
|---|---|---|
| open | in_progress | only if `assigned_to` is not `None` |
| in_progress | resolved | yes |
| resolved | open | only through `reopen_ticket` (the assignee is kept) |
| anything else | | rejected |

A resolved ticket cannot be assigned or have its status changed until it is reopened. Assigning an open or in-progress ticket is allowed.

**D11. Persistence.** Tickets are stored in `data/tickets.json`, which is excluded from Git. A missing file means a fresh start. Malformed JSON raises a clear error, and the program then exits without saving, so existing data is never overwritten. The program loads on startup and saves after every successful change. Paths are parameters so tests can use temporary files. *Why: no silent data loss.*

**D12. Tests use `unittest`.** Run them with `python -m unittest discover -s tests -v`. Each test file builds its own ticket dictionaries by hand, so one engineer's tests do not depend on the other's code.

## 5. Priority rules

Checked in this order; the first match wins.

1. high urgency AND 10 or more affected users: critical
2. high urgency OR 10 or more affected users: high
3. medium urgency OR 3 or more affected users: medium
4. everything else: low

Work queue order: critical, then high, then medium, then low. Ties are broken by the earlier numeric ticket ID.

## 6. Assumptions to revisit

- D9 (queue contains open tickets only) is our reading of the specification.
- Staff names are free text; we do not keep a list of valid staff.