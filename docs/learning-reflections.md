# Learning reflections

After the Engineering Knowledge Lab, each fellow picks one question they missed or found difficult and records what they believed, what they checked, and why their understanding changed.

---

## Offorbuzor Osinaka Divine — missed question Q1 (overdue boundary)

**I first believed** that a critical ticket created at 10:00 UTC would already be overdue at 11:00 UTC, so I answered C on the quiz — that it was overdue "only if assigned". I had the 60-minute window right, but I treated the moment the deadline arrives as the moment the ticket is already late.

**I checked** `campusflow/sla.py`. `SLA_MINUTES["critical"]` is 60 minutes, so a ticket created at 10:00 UTC has `due_at` of exactly 11:00 UTC, and `is_overdue` ends with `return now > parse_iso(ticket["due_at"])` — a strict comparison, not `>=`. At 11:00 that comparison is `11:00 > 11:00`, which is false. The suite already pins both sides of it: `test_critical_at_exactly_60_minutes_is_not_overdue` and `test_one_second_after_the_deadline_is_overdue` in `tests/test_sla.py`.

**I changed my understanding because** the boundary is exclusive. `due_at` is the instant the SLA window *closes*, not the instant the ticket becomes overdue: a ticket is overdue strictly after its deadline — one second past it, not at it. I was also wrong that assignment has anything to do with it. `is_overdue` reads only `status` and `due_at`, and the one status with a special rule is `resolved`, which is never overdue no matter how much time passes.


---

## Terngu David Ayande — missed questions Q1 (overdue boundary) and Q5 (idempotent escalation)

### Q1: overdue boundary

**I first believed** that once a ticket is created, any later time would definitely make it overdue.

**I checked** `campusflow/sla.py`: `SLA_MINUTES["critical"]` is 60, so a ticket created at 10:00 UTC has `due_at` of 11:00 UTC. `is_overdue` ends with `return now > parse_iso(ticket["due_at"])`. At 11:00 that is `11:00 > 11:00`, which is false. 

**I changed my understanding because** the deadline is the end of the SLA window, not the moment the ticket becomes late. A critical ticket created at 10:00 UTC is due at 11:00 UTC. At exactly 11:00 it is not overdue yet, and it becomes overdue only after 11:00, because the code compares `now > due_at` and does not use `>=`. I had believed that any time after creation would make the ticket overdue, and I now know that it must be strictly later than the deadline. The rule is the same for every priority; only the length of the window changes.

### Q5: idempotent escalation

**I first believed** that escalation depended on the number of times a ticket is checked.

**I checked** `escalate_overdue` in `campusflow/sla.py`: it skips a ticket when `escalated_cycle == escalation_cycle`. 

**I changed my understanding because** I now understand that the number of escalations does not depend on how many times a ticket is checked. Within one SLA cycle, the first check escalates the ticket and sets the marker, and the later checks see the marker and skip it.
### One Design mistake I made. (Engineer B)
**The Mistake** - I made a pull request and asserted that I'd written functions that were non-existent. I called clean_actor even when I had not declared the function. I also did not update main.py to match my changes.
**I originally assumed** I had written it although I hadn't. 
**How it was found out** - The PR reviewer found out the features did not tally with the PR description.

**How it was fixed** - I wrote the missing features and updated main.py. I also ran tests after updating the test file for history.py.

**What I would do differently next time** - I would pay more attention to detail and integrate tests that verify that every feature and function is working properly before asserting or including them in the PR description or even creating a PR request.


### Design mistake (Engineer A)

**1. A rule with no test: the blank actor in escalation**
**The mistake:** `escalate_overdue(tickets, events, now, actor)` in `campusflow/sla.py` is meant to refuse a blank actor, because every event must say who made it. The design said this, but no test enforced it. When the AI's mutation check removed the blank-actor check, every test still passed.

**How it was found:** by a mutation check, which breaks the code on purpose to see whether the tests notice. The check on PR #34 showed that removing the blank-actor refusal made no test fail.
**How it was fixed:** `test_blank_actor_is_refused_even_when_nothing_is_overdue` was added in `tests/test_escalation.py`. With the check removed again, that test fails, as it should.

**2. A design rule not carried through: the injected clock**
**The mistake:** The design said time is injected, so `run(..., clock=...)` reads the clock and passes it on. In the first menu  integration, events used the injected clock but the ticket functions did not get `now=ctx.now`. So `created_at` and `due_at` came from the real clock.
**How it was found:** a fixed-clock check in Interaction #15: the AI found it, and I repeated it myself with the clock set to 2026-01-01 09:00 UTC.
**How it was fixed:** in PR #36, `main.py` now passes `now=ctx.now` to the ticket actions. After the fix, `created_at` and `updated_at` were `2026-01-01T09:00:00+00:00` and `due_at` was `2026-01-01T10:00:00+00:00` for a critical ticket.
