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

## 7. CampusFlow Pro

CampusFlow Pro builds on the finished first sprint. Sections 1 to 6 above still apply unchanged. This section records what Engineer A (Terngu David Ayande) and Engineer B (the Pro teammate) decided for the new features.

> **How this section was written.** It was drafted with the help of an AI assistant (Claude) by reading the merged code on `main` (commit `7e96773`, 279 tests passing) and our pull requests. The behaviour described here is what the code does. Each engineer reviews the decisions for their own modules in the pull request, and a decision that is wrong is corrected in a reviewed change.

### 7.1 Ownership

| | Engineer A | Engineer B |
|---|---|---|
| Features | UTC time helpers, SLA deadlines, reopen starts a new cycle, idempotent escalation, JSON v2 storage, regression tests | Event recording, history display, duplicate-ticket warning, SLA attention queue and metrics, menu wiring, Knowledge Lab |
| Modules | `timeutil.py`, `sla.py`, `storage.py` | `history.py`, `duplicates.py`, `reports.py`, `knowledge_lab.py`, the new parts of `main.py` |
| Tests | `test_sla.py`, `test_escalation.py`, `test_storage.py` | `test_history.py`, `test_duplicates.py`, `test_queues.py`, `test_knowledge_lab.py`, the new parts of `test_main.py` |
| GitHub Issues | #18 to #23 | #24 to #29 |
| Shared | #30 documentation, AI logs and reflections, #31 final integration check, reviewing each other's pull requests | |

### 7.2 Data

**A ticket** keeps the eight keys from section 2 and gains five:

- `created_at`, `updated_at`, `due_at`: ISO-8601 UTC text with an explicit offset (for example `2026-10-14T10:00:00+00:00`)
- `escalation_cycle`: whole number, starts at 0, goes up by 1 on every reopen
- `escalated_cycle`: `None`, or the `escalation_cycle` in which the ticket was last escalated

**An event** is a dictionary: `event_id` (`E001`, the highest existing number plus one), `ticket_id`, `event_type` (CREATE, ASSIGN, START, RESOLVE, REOPEN or ESCALATE), `actor`, `timestamp` (ISO-8601 UTC), `before_status` (`None` for CREATE), `after_status` and `details` (a dictionary).

**The data file** is `{"schema_version": 2, "tickets": [...], "events": [...]}`.

### 7.3 Shared function contracts

| Module | Function | Returns | Raises `ValueError` when |
|---|---|---|---|
| `timeutil.py` | `utc_now()` | the current time as an aware UTC datetime | |
| `timeutil.py` | `to_iso(moment)` / `parse_iso(text)` | ISO text / aware datetime | the datetime is naive, or the text is not a valid aware time |
| `sla.py` | `calculate_due_at(priority, cycle_start)` | the deadline (aware datetime) | the priority is unknown or the start time is naive |
| `sla.py` | `is_overdue(ticket, now)` | True or False | `now` is naive |
| `sla.py` | `escalate_overdue(tickets, events, now, actor)` | `{"newly_escalated": n, "already_escalated": m}` | `now` is naive or the actor is blank |
| `storage.py` | `save_data(path, tickets, events)` | nothing | the data is invalid (nothing is written) |
| `storage.py` | `load_data(path)` | `(tickets, events)`, both empty if the file is missing | the file is damaged, in the old format, or invalid |
| `history.py` | `record_event(events, ticket_id, event_type, actor, now, before_status, after_status, details=None)` | the new event | the type, actor or time is invalid |
| `history.py` | `get_history(events, ticket_id)` | that ticket's events, oldest first | |
| `duplicates.py` | `detect_duplicates(tickets, category, title)` | list of matching ticket IDs | |
| `reports.py` | `get_sla_attention_queue(tickets, now)` | a new list of unresolved tickets in attention order | |
| `reports.py` | `build_metrics(tickets, now)` | dictionary of counts | a ticket has an unknown status or priority |
| `knowledge_lab.py` | `run_quiz(ask, say, participant, session_path, now)` | the saved session record | the participant or time is invalid |
| `main.py` | `run(path, ask, say, clock)` | exit code | |

### 7.4 Decisions

**P1. All times are timezone-aware UTC.** Times are stored as ISO-8601 text with an explicit offset. A naive datetime is rejected by `to_iso` and `parse_iso`. *Why: local or naive time makes a deadline depend on the machine and on daylight saving.*

**P2. The clock is injected.** Functions take `now` as an argument, and `now=None` falls back to the real clock so the first sprint's calls still work. `run(..., clock=utc_now)` reads the clock once per menu action, and the same time is used for the ticket and for its event. *Why: tests and the demo can fix or move time without waiting.*

**P3. SLA minutes by priority:** critical 60, high 240, medium 1440, low 2880. `due_at` is the cycle start plus these minutes.

**P4. "Overdue" means strictly later than the deadline** (`now > due_at`). A ticket is not overdue at the exact deadline, and a resolved ticket is never overdue.

**P5. Reopening starts a new SLA cycle.** `due_at` restarts from the reopen time and `escalation_cycle` goes up by 1. `created_at` and the assignee are kept.

**P6. Escalation happens once per SLA cycle.** `escalate_overdue` skips a ticket when `escalated_cycle == escalation_cycle`, so running it twice adds nothing the second time. A reopen adds 1 to `escalation_cycle`, so the ticket can be escalated again. A blank actor is refused even when nothing is overdue. Escalation does not change a ticket's status, priority or assignee.

**P7. The history is append-only.** An event is recorded only after its operation succeeds, so a rejected operation changes neither the ticket nor the events. History is ordered by timestamp and then by the numeric part of the event ID, so `E1000` comes after `E999`.

**P8. Storage is JSON v2.** Everything is validated before data is returned or written. A save writes a temporary file and then uses `os.replace`, so a failed save keeps the old file. An old-format or damaged file raises `ValueError` and is never overwritten, and a missing file means a fresh start.

**P9. `timeutil.py` is separate from `sla.py`.** `history.py` only needs the time helpers and `sla.py` imports `history`, so keeping the helpers in their own module avoids a circular import.

**P10. A duplicate ticket is warned about, not blocked.** Two tickets are duplicates when their titles match after trimming, collapsing repeated spaces and ignoring case, they are in the same category, and the existing ticket is not resolved. The matching IDs are returned in list order. The menu names them and asks "Create it anyway? (yes/no)". `yes`, `y`, `no` and `n` are accepted in any letter case, and anything else asks again. Answering no, or running out of input at the prompt, creates neither a ticket nor an event. *Why: a person may have a good reason for a second ticket, but should not create one by accident.*

**P11. The actor is asked once per session.** The menu asks "Your name (recorded in the history)" at the start, asks again if it is blank, and records the trimmed name on every event. *Why: every change in the history needs to say who made it, and asking once keeps the menu quick.*

**P12. The SLA attention queue lists unresolved tickets in this order:** overdue tickets first, then the earliest `due_at`, then the lower numeric ticket number (so `T1000` follows `T999`). Open and in-progress tickets are included and resolved tickets are left out. Each line shows `[OVERDUE]` or `[on time]`, the ticket and its deadline. Building the queue does not change the tickets. This is separate from the first sprint's work queue (option 7), which is unchanged.

**P13. Metrics are read-only counts.** `build_metrics` returns the total, the number open, in progress and resolved, the overdue unresolved tickets, the unresolved tickets escalated in their current cycle (`escalated_cycle == escalation_cycle`), and the count for every priority. Each ticket is counted once by status and once by priority. A ticket with an unknown status or priority raises `ValueError` instead of being skipped. *Why: a wrong total that looks right is worse than an error.*

**P14. The Engineering Knowledge Lab is independent of ticket data.** It has ten scenario questions. The participant is A or B, and each answer must be exactly a capital A, B, C or D, with no forgiveness. Explanations for Q1, Q3 and Q5 are required and need at least three words, and the others are optional. The score is out of 10 from the selected answers only, and a missing answer counts as wrong. The quiz shows the score, the topics to revise, each answer marked correct or wrong, and the explanations. The session is saved as JSON in `data/knowledge_sessions/`, named with the participant and the UTC time, using a temporary file and `os.replace`. If saving fails, a warning is shown and the program continues. The quiz never receives tickets or events, so it cannot change them.

**P15. Menu structure.** The first-sprint options 1 to 8 are unchanged, and the new ones are 9 escalate overdue tickets, 10 SLA attention queue, 11 metrics, 12 a ticket's history and 13 the Knowledge Lab, with 0 to exit. Every action has the shape `action(ctx, ask, say)` and returns True if it changed the data, so the menu saves. `Context` bundles the tickets, the events, the actor and the time of the current action. The menu loads the data file at the start and refuses an old-format or damaged file with a clear message, without changing it.

### 7.5 Assumptions to revisit

- Duplicates are detected by an exact normalised title in the same category. Similar but differently worded titles are not caught.
- Escalation runs when someone chooses option 9. Nothing escalates automatically.
- A resolved ticket never counts as overdue or in the attention queue.
- The Knowledge Lab answer key lives in `knowledge_lab.py`, so a participant who reads the code can see the answers.
- The `data/knowledge_sessions/` files are not in `.gitignore`. Decide whether to commit them as evidence or ignore them.
- A data file from the first sprint (a plain list of tickets) must be moved or deleted before the program will start. It is deliberately not converted.
