# Learning reflections

After the Engineering Knowledge Lab, each fellow picks one question they missed or found difficult and records what they believed, what they checked, and why their understanding changed.

---

## Offorbuzor Osinaka Divine — missed question Q1 (overdue boundary)

**I first believed** that a critical ticket created at 10:00 UTC would already be overdue at 11:00 UTC, so I answered C on the quiz — that it was overdue "only if assigned". I had the 60-minute window right, but I treated the moment the deadline arrives as the moment the ticket is already late.

**I checked** `campusflow/sla.py`. `SLA_MINUTES["critical"]` is 60 minutes, so a ticket created at 10:00 UTC has `due_at` of exactly 11:00 UTC, and `is_overdue` ends with `return now > parse_iso(ticket["due_at"])` — a strict comparison, not `>=`. At 11:00 that comparison is `11:00 > 11:00`, which is false. The suite already pins both sides of it: `test_critical_at_exactly_60_minutes_is_not_overdue` and `test_one_second_after_the_deadline_is_overdue` in `tests/test_sla.py`.

**I changed my understanding because** the boundary is exclusive. `due_at` is the instant the SLA window *closes*, not the instant the ticket becomes overdue: a ticket is overdue strictly after its deadline — one second past it, not at it. I was also wrong that assignment has anything to do with it. `is_overdue` reads only `status` and `due_at`, and the one status with a special rule is `resolved`, which is never overdue no matter how much time passes.

