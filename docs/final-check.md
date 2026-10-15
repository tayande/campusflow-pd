# CampusFlow Pro: final integration check

This file records the final check of the project (issue #31). Everything below was run by Engineer A on 2026-10-15 on a fresh start, and the outputs are copied from the terminal.

## 1. Code state that was checked

- Branch: `main`, commit `11ff1ee` (merge of PR #42). All code was already merged at this point. Later pull requests only change documentation.
- Command: `python3 -B -m unittest discover -s tests`
- Result: `Ran 280 tests in 0.143s` and `OK`.
- The data folder had no old `data/tickets.json`, so the program started with an empty list.

## 2. CLI walkthrough

Menu lines are left out. The name entered at the start was `Terngu`.

### 2.1 Create two tickets and reject a status change

```
Choose an option: 1
Title: wi-fi is down in lab 2
Category (Network, Hardware, Software, Other): network
Urgency (low, medium, high): high
Affected users: 15
Created T001 with priority critical.

Choose an option: 1
Title: printer jammed
Category (Network, Hardware, Software, Other): hardware
Urgency (low, medium, high): low
Affected users: 1
Created T002 with priority low.

Choose an option: 5
Ticket ID: t002
New status (open, in_progress, resolved): in_progress
Error: Assign the ticket to someone before starting work on it
```

T002 is unassigned, so moving it to `in_progress` is rejected. The program showed the error and carried on.

### 2.2 Backdating T001 so that it is overdue

The program uses the real clock, and a critical ticket takes 60 minutes to become overdue. To show an overdue escalation without waiting, `data/tickets.json` was edited by hand: the three time fields of T001 (`created_at`, `updated_at`, `due_at`) were moved back by 3 hours, using this script:

```python
import json
from datetime import datetime, timedelta
p = 'data/tickets.json'
data = json.load(open(p))
t = data['tickets'][0]
for k in ('created_at', 'updated_at', 'due_at'):
    t[k] = (datetime.fromisoformat(t[k]) - timedelta(hours=3)).isoformat()
json.dump(data, open(p, 'w'), indent=2)
```

Output: `T001 2026-10-15T08:15:17+00:00 2026-10-15T09:15:17+00:00`. The critical deadline is 60 minutes after the start, so `due_at` is now about two hours in the past. No program code was changed. Only the ticket's own times were edited, so the history still shows the real creation time of 11:15:17, because the history is append-only and was not touched.

### 2.3 Overdue escalation, run twice

```
Choose an option: 10
SLA attention queue (overdue tickets first):
1. [OVERDUE] T001 | wi-fi is down in lab 2 | Network | critical | open | unassigned | due 2026-10-15T09:15:17+00:00
2. [on time] T002 | printer jammed | Hardware | low | open | unassigned | due 2026-10-17T11:15:50+00:00

Choose an option: 9
Newly escalated: 1
Already escalated in this cycle: 0

Choose an option: 9
Newly escalated: 0
Already escalated in this cycle: 1

Choose an option: 12
Ticket ID: t001
History of T001 (oldest first):
E001 | 2026-10-15T11:15:17+00:00 | CREATE | Terngu | - -> open | priority=critical
E003 | 2026-10-15T11:22:10+00:00 | ESCALATE | Terngu | open -> open | cycle=0, due_at=2026-10-15T09:15:17+00:00

Choose an option: 11
Total tickets: 2
Open: 2
In progress: 0
Resolved: 0
Overdue unresolved: 1
Escalated in current cycle: 1
By priority:
  critical: 1
  high: 0
  medium: 0
  low: 1
```

What this shows:
- T001 is overdue because the time of the escalation (11:22:10) is later than its deadline (09:15:17), and T002 is not overdue.
- The first escalation recorded one `ESCALATE` event. The second run changed nothing, because the ticket was already escalated in cycle 0 (`escalated_cycle == escalation_cycle`). This is the once-per-cycle rule.
- The history of T001 has one `CREATE` and one `ESCALATE`. `E002` is T002's creation and belongs to a different ticket.
- The metrics agree: one overdue unresolved ticket and one ticket escalated in its current cycle.

## 3. Knowledge Lab scores

| Participant | Score | Evidence |
|---|---|---|
| Engineer A (Terngu David Ayande) | 8/10 | Terminal output after the quiz (Q1 and Q5 wrong). The program reported saving the session as `knowledge_session_A_20261015T020959Z.json`, but that file was later lost from the working folder and is not in the repository. |
| Engineer B (Offorbuzor Osinaka Divine) | 9/10 | `data/knowledge_sessions/knowledge_session_B_20261015T012957Z.json` |

Engineer A's two wrong answers were Q1 (overdue boundary) and Q5 (idempotent escalation). The reflections are in `docs/learning-reflections.md`.

## 4. Pull requests

CampusFlow Pro:

| PR | What | By |
|---|---|---|
| #32 | SLA engine (time helpers, deadlines, overdue, reopen cycle) | Engineer A |
| #33 | Audit history and menu actions | Engineer B |
| #34 | Escalation and JSON v2 storage | Engineer A |
| #35 | Duplicate warning and Knowledge Lab | Engineer B |
| #36 | SLA queue, metrics, menu and v2 storage wiring | Engineer B |
| #37 | AI learning log and reflection (Engineer B) | Engineer B |
| #38 | Pro design decisions and AI log entries 12 to 16 | Engineer A |
| #39 | Engineer B design mistake in the reflections file | Engineer B |
| #40 | Engineer A reflection and design mistake | Engineer A |
| #41 | README update for Pro | Engineer A |
| #42 | Corrections to Engineer A's AI log | Engineer A |
| #43 | Engineer B README and reflection corrections | Engineer B |

The first sprint's pull requests are #7 to #17 on GitHub. Each pull request was reviewed by the other engineer before it was merged.

## 5. Design mistakes

One design mistake from each engineer, with how it was found and fixed, is in [docs/learning-reflections.md](learning-reflections.md).

## 6. Issues

Issues #1 to #29 were closed by hand or by merged pull requests. This pull request closes #30 (documentation, logs and reflections) and #31 (this final check).
