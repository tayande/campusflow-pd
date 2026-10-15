# AI Learning Log: Engineer B

**Fellow:** Peace Onma Oigoga (GitHub: onma77)
**AI assistant used:** Claude. I did not use a separate chatbot for this project.

---

## Part 1: Learning log entries

### Interaction #1: Reading the handoff and the shared decisions (D1 to D12)
**Problem:** I joined a project where Engineer A and I write separate modules. I needed to understand the shared decisions (tickets as a list of dictionaries passed first, `ValueError` for errors, no `input()` or `print()` in the logic, the workflow table, the queue rule) before writing any code.
**My initial understanding:** i thought my part was to build seperately with a different repository then adding my team member just as he did. but he explained that it's a team work were we get to share the work.
**Prompt to AI:** Engineer A asked Claude to divide the work and write a handoff file for me: "so go ahead and divide the work as the project suggests, then give me or hand me the relevant part of the project for my other member, so that she wuold understand everything we are doing here..." He gave me the handoff file and I read it myself before writing any code.
**Useful AI guidance:** The handoff file divided the work: I take assign/status workflow (issue #4), work queue and reports (issue #5) and the menu options for those features. The decisions say errors are raised as `ValueError` and caught only in the menu, and that logic functions never read or print.
**My independent experiment/test:** I read `campusflow/tickets.py` to see how `get_ticket` finds a ticket and raises `ValueError`, because my functions call it.
**Verification source or result:** `docs/design-decisions.md` sections 3 and 5. AI run: if `get_ticket` returns `None` instead of raising, 5 tests in the workflow and menu files fail, which shows my functions depend on it raising.
**Decision:** Accepted. I followed the decisions as written.
**Related file/commit:** `docs/design-decisions.md`, PR #7
**What I can now explain without AI:** Logic functions raise `ValueError` instead of printing so the menu decides how to show the message and tests can check it with `assertRaises`. Passing the tickets list as the first parameter means every function works on the same data and can be tested without a file.

---

### Interaction #2: The status workflow (`assign_ticket`, `change_status`, `reopen_ticket`)
**Problem:** Tickets must move open -> in_progress -> resolved, with rules: a ticket must be assigned before it starts, open cannot jump to resolved, and a resolved ticket can only be reopened.
**My initial understanding:** my ai made it clear from when i prompted it.
**Prompt to AI:** Engineer A asked on my behalf: "can you give me the codes for her own part?, then i will send to her and then walk us through on how to make the necessary additions to the repo?" For my first pull request he also asked: "while she is trying to create the first pull request, give me the discreptinog that she is going to write there first". I received the code, tests and instructions from him, committed them myself on `feat/4-status-workflow`, and opened PR #10.
**Useful AI guidance:** The allowed moves are stored in one dictionary, `ALLOWED_MOVES`, instead of repeated `if` statements. `change_status` runs all its checks first and changes `ticket["status"]` as the last step, so a rejected change leaves the ticket untouched. `reopen_ticket` keeps the assignee. **This code was supplied by the AI, and I committed it myself.**
**My independent experiment/test:** AI run on the merged code (all 104 tests pass normally):
- Letting `open` move straight to `resolved` in `ALLOWED_MOVES` makes `test_open_cannot_jump_to_resolved` fail.
- Removing the "must be assigned" check makes `test_unassigned_ticket_cannot_start` fail (in `test_workflow` and `test_main`).
- Removing the "resolved cannot be assigned" check makes `test_resolved_ticket_cannot_be_assigned` fail.
- Removing `.strip()` on the staff name makes `test_blank_name_is_rejected_and_nothing_changes` and 3 more fail.
- Making `reopen_ticket` clear the assignee makes `test_reopens_a_resolved_ticket_and_keeps_the_assignee` fail.

**Decision:** Accepted. I made no changes to the code.
**Related file/commit:** `campusflow/workflow.py`, `tests/test_workflow.py`, PR #10, commit `5592bf4`
**What I can now explain without AI:** `ALLOWED_MOVES` lists, for each status, the statuses it may move to, so one `in` check replaces a chain of `if` statements. The status is changed only after every check has passed, so a rejected move cannot leave a ticket half-changed. `reopen_ticket` is the only way back from resolved, and it keeps the assignee because the same person usually still owns the ticket.

---

### Interaction #3: The work queue and the summary report
**Problem:** The queue must list only open tickets, most urgent first, with ties going to the lower ID. The report must show the total and the counts by status and priority, including groups with zero tickets.
**Prompt to AI:** Engineer A asked on my behalf, using the same kit request as for the workflow, and later: "i have merged her feat 4 word, now, give me the description on her pull request for feat 5". I received the code, tests and instructions from him, committed them myself on `feat/5-queue-and-reports`, and opened PR #11.
**Useful AI guidance:** `queue_order` returns a tuple `(position of priority in PRIORITIES, numeric part of the ID)` and `sorted(..., key=queue_order)` sorts by it. The numeric part is used instead of the ID text so that T1000 comes after T999. `build_report` starts every count at 0 so a missing group still shows 0, and raises `ValueError` for an unknown status or priority. `get_work_queue` returns a new sorted list and does not change the original. **This code was supplied by the AI, and I committed it myself.**
**My independent experiment/test:** AI run on the merged code:
- Comparing the ID text instead of the number makes `test_numeric_order_not_text_order` fail.
- Dropping the ID from the sort key makes `test_ties_go_to_the_earlier_id` fail (plus the numeric-order test).
- Including `in_progress` tickets in the queue makes `test_only_open_tickets_are_included` and `test_urgent_ticket_that_is_in_progress_is_not_in_the_queue` fail.
- Starting the report's priority counts as an empty dictionary instead of zeros makes `test_empty_list_gives_all_zeros` and 3 more fail.

**Verification source or result:** Normal run: 104 tests, OK (28 workflow tests and 5 report tests).
**Decision:** Accepted. I made no changes to the code.
**Related file/commit:** `campusflow/workflow.py` (`queue_order`, `get_work_queue`), `campusflow/reports.py`, `tests/test_reports.py`, PR #11, commit `b6eff45`
**What I can now explain without AI:** The sorting key is a tuple, so Python compares the priority position first and the ID only when the priorities are equal. The ID is converted to a number because as text "T1000" sorts before "T999". The report starts every count at 0 so the screen always shows all statuses and priorities, including empty ones.

---

### Interaction #4: Menu options for assign, status, reopen, queue and report
**Problem:** Connect my logic functions to the menu without putting `input()` and `print()` inside the logic, and without breaking Engineer A's menu loop.
**My initial understanding:** i had no initial understanding.
**Prompt to AI:** Engineer A asked on my behalf: "some of these files have the same titles, or names, how am i supposed to know which is which. i thought you were going to give me each code for each branch..." The AI then repackaged my code into one zip per branch with a walkthrough. I received the menu-options kit, committed it myself on `feat/4-menu-options`, and opened PR #14.
**Useful AI guidance:** Each menu option is a small function that takes the tickets, plus the `ask` and `say` functions as parameters (so tests can pass fake ones). The options are registered in a dictionary `ACTIONS` keyed by the menu number. A `ValueError` raised by the logic is caught in the menu loop and shown as `Error: ...`. **This code was supplied by the AI, and I committed it myself.**
**My independent experiment/test:** AI run: removing the "resolved cannot be assigned" check also fails `test_assign_resolved_ticket_is_rejected` in `test_main`, so the menu is tested as well as the logic.
**Verification source or result:** Normal run: 104 tests, OK, including 31 menu tests.
**Decision:** Accepted. I made no changes to the code.
**Related file/commit:** `campusflow/main.py` (assign, status, reopen, queue and report actions), PR #14, commit `c23ad1f`
**What I can now explain without AI:** `ACTIONS` is a dictionary from the menu number to a function, so adding an option means adding one entry. `ask` and `say` are parameters so the tests can pass fake ones instead of typing. A `ValueError` from my functions is caught in the menu loop, so a mistake shows an error message and the program keeps running.

---

### Interaction #5: A suggestion I checked and corrected (REQUIRED ENTRY)
> The marking asks for at least one entry where I checked an AI suggestion and corrected or rejected it. I cannot copy this one from anyone. If it happened, I write it. If not, I do a real check now: read the AI's code line by line, find one thing that is wrong, unclear or weaker than it could be, change it, and re-run the tests.
>
> Known candidates from the reviews (not written by me, so I only use one if I really checked it myself): the status prompt lists "open" although the menu option cannot set it; non-string input to the logic functions raises `AttributeError` instead of `ValueError`; there is a duplicate `campusflow.tickets` import in `main.py`.

---

### Interaction #6: Reviewing my partner's pull request
**Problem:** Review Engineer A's pull requests properly, with specific comments and without approving blindly.
**Prompt to AI:** Engineer A asked the AI for a review message for me to post on his pull request ("she is going to review the pull request right?, i want you to give me a review message for her"). The AI declined to write the review itself and gave me a checklist instead, because a review only counts if I read the code. I use the checklist; the comments I post are my own.
**Verification source or result:** [PR #9: ticket creation](https://github.com/tayande/campusflow-pd/pull/9)
**Related file/commit:** [PR #9: ticket creation](https://github.com/tayande/campusflow-pd/pull/9)

---

## Part 2: Clarification questions (running list)

**Question 1:** What is CampusFlow, and what problem does it solve?

**AI's answer (as I recorded it):** CampusFlow is a Python command-line helpdesk application designed to help campus staff manage technical support requests. For example, a student might report that the campus Wi-Fi is not working, a staff member might report a faulty laptop, or someone might need help installing software. Without a proper system, these requests could be forgotten or handled in the wrong order. CampusFlow solves this problem by allowing users to:
Create support tickets.
Calculate ticket priorities.
Assign tickets to staff members.
Track the progress of tickets.
View unresolved tickets in priority order.
Generate reports.
Save tickets so they remain available after restarting the application. In simple terms: CampusFlow helps a support team record problems, decide which problems need attention first, and track them until they are resolved.

**Did I verify it? How?** *(one sentence in my own words)*

**Question 2:** What is a command-line application?

**AI's answer (as I recorded it):** A command-line application is a program that users interact with by entering commands or selecting options in a terminal. CampusFlow does not need a website or graphical interface. Users can manage tickets through a text-based menu.
For example:
===== CAMPUSFLOW =====
1. Create Ticket
2. View All Tickets
3. Assign Ticket
4. Update Ticket Status
5. View Work Queue
6. View Reports
7. Exit

Choose an option:
When a user selects an option, the program performs the corresponding action. Important: The guide specifically requires a command-line application, so building a website is not necessary for this sprint.

**Did I verify it? How?** *(one sentence in my own words)*

**Question 3:** What is a GitHub Issue, and why do we need it for CampusFlow?

**AI's answer (as I recorded it):** A GitHub Issue is a task, problem, or improvement recorded in a GitHub repository. Instead of immediately writing code, the team uses Issues to organize the work that needs to be completed. For example, we could create an Issue titled:
Issue #1: Implement Ticket Creation
The description might say: Implement a function that creates a ticket using the required fields. Validate the title, category, urgency, and number of affected users. Generate a unique ticket ID and calculate the ticket priority.
We could also include acceptance criteria:
A valid ticket can be created.
The ticket receives a unique ID.
A blank title is rejected.
Zero affected users are rejected.
The ticket's priority is calculated correctly. Once the task is complete, the developer can link the Issue to the pull request that implements it. Why do we need Issues?
They help us divide the project into manageable tasks, assign responsibility, and track progress.

---

## Part 3: Use of AI statement

Claude supplied most of the code for `workflow.py`, `reports.py`, the menu options and their tests, together with the step-by-step instructions. I did not use a separate chatbot for this project. I committed the code myself on my own branches and each PR says the code was supplied by the AI.
