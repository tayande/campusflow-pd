# AI Learning Log: Offorbuzor Osinaka Divine — Campus Flow Pro

**Fellow:** Offorbuzor Osinaka Divine
**AI assistant used:** Claude, as a tutor and reviewer.

## Part 1: Learning log entries

### Interaction #1: Writing the SLA attention queue and the metrics, and wiring all three options into the menu

**Problem:** The menu had eight options and no way to see a deadline. The SLA attention queue and the metrics did not exist yet, so I had to write them in `reports.py` as well as add the escalation option, then connect all three to the menu without losing the options that were already there.

**My initial understanding:** I knew the menu registers its options in the `ACTIONS` dictionary, because a new feature has to be added there to be reachable. I thought `sla.py` held all of the deadline work, and I did not know that the reporting side was still empty.

**Useful AI guidance:** `escalate_overdue` in `sla.py` already took `(tickets, events, now, actor)` and avoided duplicates by escalating only when `escalated_cycle` differed from `escalation_cycle`, so the escalation logic did not need rewriting. The queue and the metrics were new work in `reports.py`, not wiring.

**My independent experiment/test:** I read `campusflow/main.py`, `sla.py` and `reports.py` and compared the menu options against the functions that existed, then ran the suite after each new function.

**Verification source or result:** `reports.py` — `get_sla_attention_queue` (the unresolved tickets, overdue first, then the earliest `due_at`, then the numeric ticket ID), `format_sla_ticket` (the `[OVERDUE]` / `[on time]` line carrying the deadline) and `build_metrics` (counts by status and priority, the overdue unresolved total, and the escalations in the current cycle). `main.py` — `sla_escalation_action`, `sla_queue_action`, `metrics_action` and their `ACTIONS` entries.

**Decision:** Write the queue and the metrics as read-only functions in `reports.py`, keep `escalate_overdue` as it was, and add three menu actions that call them. The two read-only actions return `False`, so nothing is saved after them.

**Related file/commit:** `campusflow/reports.py` and `campusflow/main.py`, commit `de15610`. That commit also carried unrelated formatting changes to `sla.py`; the review asked for them to be reverted, and they are not in the merged branch.

**What I can now explain without AI:** A deadline that nothing reports on is invisible, so the queue is ordered by what a reader needs first: overdue tickets before the rest, then the soonest deadline. An action returns `True` only when ticket data actually changed, which is what tells `run()` to save; the queue and the metrics only read, so they return `False` and the file is left alone.

---

### Interaction #2: Extending the menu without losing the options that were already there

**Problem:** I extended `main.py` by working from a copy of the file, which is the change most likely to quietly drop something that already worked. `escalate_overdue` was also not importable where I first looked for it.

**My initial understanding:** I expected the SLA functions to be importable as they were, and the existing menu to stay exactly as it was.

**Useful AI guidance:** Add to the file rather than replacing it — keep the existing `ACTIONS` entries and append the new ones — and check what a module imports before overwriting it.

**My independent experiment/test:** I inspected the project files to find where `escalate_overdue` is defined and imported, and compared the menu before and after my change.

**Verification source or result:** The menu committed in `de15610` still registers keys 1 to 8 alongside the new options, so nothing was lost in what was committed. I could not find a commit where the old options were missing, and I cannot point to one: if it happened, it was in my working copy and never reached the branch. My first version of this entry described it as a loss in the repository, and the review was right to ask me for the evidence.

**Decision:** Keep the working code and add to it, instead of replacing the file. Check what a file depends on before overwriting it.

**Related file/commit:** `campusflow/main.py`, commits `de15610` and `cec55c6`

**What I can now explain without AI:** Replacing a whole file is risky, because a plausible-looking replacement can quietly drop behaviour that worked. Comparing the old and the new menu, and checking the imports a module actually needs, is cheaper than debugging afterwards.

---

### Interaction #3: Menu options, tests, and an honest PR description

**Problem:** Add the SLA escalation, SLA attention queue, and metrics options while keeping ticket history and the Engineering Knowledge Lab accessible.

**My initial understanding:** I assumed the new menu options would be assigned the next available numbers in sequence. However, I initially placed the quiz at option 10 and the new options at 9, 11, and 13. My original assumption did not fully account for the intended menu layout.

**Useful AI guidance:** Keep the menu actions connected to their correct functions, and make the commit message and PR description match the actual changes and test results.

**My independent experiment/test:** I checked the menu against the feature plan and ran the unit test suite.

**Verification source or result:** At the time, the test output showed `Ran 264 tests in 0.649s` — `OK`. The subsequent review confirmed that all 280 tests passed on the updated branch.

**Decision:** Use the commit message `feat: add SLA queue, metrics, and CLI options` and describe only the changes supported by the code and test results.

**Related file/commit:** `campusflow/main.py`, commit `de15610`, and the PR for `feat/27-queues-cli`.

**What I can now explain without AI:** Menu numbering should follow the intended interface, not an assumption that every option must be numbered consecutively. I should compare the planned menu with the actual implementation before claiming that the numbering is correct.

---

### Interaction #4: A suggestion I checked and corrected (REQUIRED ENTRY)

**Problem:** The event helper in `history.py` has to store the right fields, number its IDs in one fixed way, take `now` as an argument, and record an event only after the operation succeeded. That is the outline the AI gave me, and I kept it. Writing the helper made me look harder at three details inside it:

| AI outline | My implementation | Why | Evidence |
|---|---|---|---|
| History ordered by time | Sorted by the parsed instant, not the timestamp text | 10:00+01:00 is 09:00 UTC, so sorting on the text files it in the wrong place | `test_time_order_uses_real_instants_not_text` |
| `details` stored as it is given | `details` is copied with `dict(details)` | A caller who keeps the dictionary cannot change an event that is already recorded | `test_details_argument_is_copied_not_stored` |
| The ticket ID matched as typed | The ID is stripped and upper-cased before matching | Friendlier menu input | `test_ticket_id_typed_in_lowercase_still_matches` |

Three rows I first put in this table are not here any more. `now` being required with no default, the numeric tie-break between equal timestamps, and `get_history` returning a new list were all in the guide I was given, so they are not things I added.

**My independent experiment/test:** I read `campusflow/history.py` and checked each row against the code, then ran `tests/test_history.py` after each change. The `dict(details)` row did not survive that check the first time. The test I had cited for it, `test_details_default_is_a_fresh_dict_each_time`, only covers the `details=None` default, so it also passes with the copy removed — the pull request review showed that by deleting the copy and watching the suite stay green. I wrote `test_details_argument_is_copied_not_stored` in response: it passes a dictionary to `record_event`, changes that dictionary afterwards, and asserts that the recorded event did not change. That test fails without the copy.

**Verification source or result:** `campusflow/history.py` (`record_event`, `get_history`) and `tests/test_history.py`. Three rows, each with a named test that fails when the behaviour is removed.

**Decision:** Keep the copy and add the test that pins it, rather than dropping the copy or leaving the claim unsupported.

**Related file/commit:** `campusflow/history.py`, commit `a4f264f`; connected to the menu in commit `1300cf1`; the new test added on `feat/30-ai-learning-log-and-reflection`.

**What I can now explain without AI:** The sort key decides more than the order you can see: sorting on the timestamp text would file a `+01:00` event in the wrong place, so the key parses the instant first and only compares the numeric event ID when two instants are equal. `dict(details)` copies the caller's dictionary, so a caller who keeps that dictionary cannot reach back into the audit log, and `sorted()` builds a new list, so the events list itself is never reordered.

---

## Part 2: Use of AI statement

Claude assisted with the SLA, queue and metrics integration: reviewing the existing code, explaining how the SLA and reporting functions connect, drafting the integration, and helping to word this log and the pull request description. I ran the tests and the CLI myself, and each pull request that contains such code says so.

The first version of this log described the SLA reporting functions as already existing and left `reports.py` out of what I wrote. The review of the pull request caught that, and the entries above now describe what I wrote. Interaction #4 records one claim I could not support until I wrote the test for it.
