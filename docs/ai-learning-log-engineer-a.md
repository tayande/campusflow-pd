# AI Learning Log: Engineer A
YOUR WORDS
**Fellow:** Terngu David Ayande (GitHub: tayande)
**AI assistant used:** Claude (chat), as a tutor and reviewer.

> **How to read this file.** Facts (what I asked, what the AI said, what the code and tests do) come from our conversation and the repository. Test results marked "AI run" were produced by the AI in its own environment on the merged code and can be reproduced with `python3 -m unittest discover -s tests -v`.

> A learning log is graded as evidence of my own work, so nothing stays in it that I cannot say is true.

---

## Part 1: Learning log entries


### Interaction #1: Understanding the CampusFlow brief and the priority rules
**Problem:** I needed to understand what the project asks for, how the marks are split, and how the four priority rules combine.
**My initial understanding:** I knew CampusFlow was a helpdesk ticket program for a two-person sprint, but not which features were required, how the 100 marks were split, or how the priority was worked out.
**Prompt to AI:** "make me understand the project first, what its all about and the requirements from me to be able to do the project well."
**Useful AI guidance:** The project is a command-line ticket manager with seven features (create, list/view, assign, workflow, queue, reports, persistence). Only 40 of the 100 marks are for the program itself; the rest are tests, Git workflow, AI learning and the defense. The priority rules are checked in order and the first match wins, so "high urgency and 10+ users" is critical, not just high.
**My independent experiment/test:** I worked out on paper what a low-urgency ticket gets with 9, 10, 3 and 2 users, using the rules only: 9 users gives medium (3 or more), 10 users gives high (10 or more), 3 users gives medium, 2 users gives low.
**Verification source or result:** The rules in `docs/design-decisions.md` section 5, and the unit tests in `TestCalculatePriority`. AI run: changing the critical rule from `>= 10` to `> 10` makes `test_high_urgency_with_ten_users_is_critical` fail, which proves the boundary is tested.
**Decision:** Accepted.
**Related file/commit:** `docs/design-decisions.md` (priority rules, section 5), PR #7
**What I can now explain without AI:** The rules are checked top to bottom and the first match wins. If "high urgency" were checked before "high urgency AND 10+ users", a critical ticket would be labelled only high. The order is what makes the most serious case win.

---

### Interaction #2: Shared function contracts and error handling
**Problem:** Two engineers write separate modules. I needed to understand how to agree on function names, parameters, return values and error handling so the code fits together and can be tested without typing input.
**My initial understanding:** I thought we could each write our own functions and join them at the end. I had not thought about agreeing the names, inputs and errors first.
**Prompt to AI:** "so go ahead and divide the work as the project suggests, then give me or hand me the relevant part of the project for my other member, so that she would understand everything we are doing here, how to do it and then when she hands it over to her chatbot, it will understand what to do exactly as well as the decisions we will be making in this project too."
**Useful AI guidance:** A handoff file for Engineer B and a set of proposed decisions (D1 to D12): tickets as a list of dictionaries passed as the first parameter, errors raised as `ValueError` and caught in the menu, no `input()` or `print()` in logic functions, next ID = highest existing number + 1, and a work queue of `open` tickets only.
**My independent experiment/test:** None for this step. The decisions are tested later by the unit tests, which pass tickets in and check what comes out without any typing.
**Verification source or result:** Engineer B read the hand-off file and agreed to all decisions without changes. Her merged code (PR #10, #11, #14) and mine (PR #9, #12, #13) fit together without any renaming, which is the real check.
**Decision:** Accepted as written. One assumption (D9, queue shows open tickets only) is recorded as open to revision.
**Related file/commit:** `docs/design-decisions.md`, PR #7
**What I can now explain without AI:** Logic functions raise errors instead of printing them so the menu decides how to show them and tests can check them with `assertRaises`. IDs use the highest number plus one, not the count, so an ID is never reused if a ticket is ever removed.

---

### Interaction #3: Setting up `.gitignore`, and a snippet that did not work
**Problem:** I needed to create a `.gitignore` so runtime data and local files are not committed.
**My initial understanding:** After creating the repo without a `.gitignore`, I asked: "i have created the repo without doing the .gitignore then, so i believe i will have to clone it now and do it right?"
**Prompt to AI:** "about the .gitignore, should i just craete it in the browser on my github or i must clone it to my vs code first"
**Useful AI guidance:** Either way works, as long as it exists before any ignored file is committed, because `.gitignore` only affects files Git is not already tracking. I was given five lines to put in the file and a check to run with `git check-ignore -v`.
**My independent experiment/test:** I created `data/tickets.json` and ran `git check-ignore -v data/tickets.json` and `git status`. The first printed nothing and `git status` listed `data/` as untracked, so the rule was not working. I then ran `ls -a`, `cat .gitignore` and `git ls-files`.
**Verification source or result:** `cat .gitignore` showed every line starting with three spaces. Git treats leading spaces as part of the pattern, so no pattern matched anything. The most likely cause is that the code block I copied was indented in the chat message.
**Decision:** Corrected. I rewrote the file with no leading spaces and re-ran the check. I confirmed it was fixed ("its all done now").
**Related file/commit:** `.gitignore`
**What I can now explain without AI:** A leading space is part of the pattern, so `   data/` looks for a folder whose name starts with spaces and matches nothing. `git check-ignore -v <path>` prints which rule ignores a path, and printing nothing proves no rule matches.

> This is the entry for "corrected an AI suggestion after checking it".

---

### Interaction #4: `git push` failing with "Authentication failed"
**Problem:** `git push` failed with `askpass.sh: Permission denied`, `remote: No anonymous write access` and `fatal: Authentication failed`.
**My initial understanding:** I thought my GitHub password or account was wrong.
**Prompt to AI:** I pasted the full error output.
**Useful AI guidance:** GitHub no longer accepts account passwords for HTTPS pushes. VS Code's credential helper script was not executable, so Git sent no credentials and was treated as anonymous. The fix was a fine-grained personal access token with Contents read/write, entered when Git prompts, with `unset GIT_ASKPASS` and a credential cache so it is not asked again every time.
**My independent experiment/test:** I created the token, followed the steps and re-ran `git push`.
**Verification source or result:** The push succeeded, and I could see the commit on GitHub ("pushed").
**Decision:** Accepted. The token is never committed to the repo or shared.
**Related file/commit:** The first push of my work to the repo.
**What I can now explain without AI:** A password proves who I am on the website only. For command-line pushes, GitHub wants a token with limited permissions that can be revoked. The three error lines meant: the helper script could not run, so no credentials were sent, so GitHub saw an anonymous user and refused to let it write.

---

### Interaction #5: GitHub Issues: what they are, how they work, why we need them
**Problem:** I did not know how to use GitHub Issues or why the guide requires them.
**My initial understanding:** I thought issues were only for reporting bugs.
**Prompt to AI:** "i want to understand how to use them, how they work and why i need them."
**Useful AI guidance:** An issue is a numbered, trackable task with an assignee, label and acceptance criteria written as checkboxes. Branch names carry the issue number, and a PR can reference it (`Closes #n` closes it on merge; `Refs #n` only links it). Issues must be created in order so the numbers match the branch names. I was given drafts for all six issues and a table of assignees and labels.
**My independent experiment/test:** I created the six issues and assigned them (#1 to #3 to me, #4 and #5 to Engineer B, #6 to both).
**Verification source or result:** The Issues tab shows six numbered issues with the right assignees.
**Decision:** Accepted the drafts. I did not change the wording.
**Related file/commit:** GitHub Issues #1 to #6
**What I can now explain without AI:** Each acceptance criterion should be testable, so anyone can say "done" or "not done" without opinion. `Closes #4` closes the issue automatically when the PR merges; `Refs #6` only links it and leaves it open. I used `Refs #6` on the README PR because issue #6 also needs both logs.

---

### Interaction #6: Branch and pull request for the design decisions document
**Problem:** I needed to learn the whole branch, commit, push, PR, review and merge flow.
**My initial understanding:** I thought I would just commit and push my files to `main`.
**Prompt to AI:** "on step 4, the description on the pull request, can you give me the actual content?"
**Useful AI guidance:** Branch `docs/6-design-decisions` from an updated `main`, add the file, check with `git status` and `git diff --staged`, push, open the PR with the template, request Engineer B as reviewer, and merge only after approval.
**My independent experiment/test:** I ran `git status` and `git diff --staged` before committing, pushed the branch, and opened the PR from the GitHub banner.
**Verification source or result:** PR #7 was reviewed by Engineer B and merged. Her review comments are on the PR's Conversation tab (https://github.com/tayande/campusflow-pd/pull/7).
**Decision:** Accepted as given.
**Related file/commit:** PR #7, `docs/design-decisions.md`
**What I can now explain without AI:** A branch lets me work without touching `main`; the PR is where my partner checks the change before it merges, and the merge only happens after her approval. `git diff --staged` shows exactly what is about to be committed.

---

### Interaction #7: Foundation code (`get_ticket` and its tests), supplied by the AI
**Problem:** Issue #1 needs the shared constants and `get_ticket`
**My initial understanding:** I understood that `get_ticket` finds a ticket by its ID, but not why it needs to clean the ID or why it raises an error.
**Prompt to AI:** "Explain how i am going to write this `get_ticket` function, the reason behind it before giving me the actual code for it."
**Useful AI guidance:** The AI supplied `campusflow/tickets.py` (four constants and `get_ticket`) and `tests/test_tickets.py` (a `make_tickets()` helper and four tests), and updated `concepts-to-review.md` to explain how each concept appears in the code line by line. **This code was written by the AI at my request, not by me from scratch.**
**My independent experiment/test:** AI run on the merged code: replacing `ticket_id.strip().upper()` with `ticket_id` made `test_ignores_spaces_and_letter_case` fail (plus 3 more in other files that use `get_ticket`); replacing `raise ValueError` with `return None` made `test_unknown_id_raises_value_error` and `test_empty_list_raises_value_error` fail, plus 5 in the workflow and menu tests.
**Verification source or result:** Normal run: 104 tests, OK. With the `return None` change: `FAILED (failures=2, errors=5)`.
**Decision:** Accepted. I made no changes to the code, and said so in the PR.
**Related file/commit:** PR #8
**What I can now explain without AI:** `return` is inside the loop so it stops at the first match, and `raise` is after the loop because it only runs if nothing matched. The tests use `make_tickets()` so each test starts with fresh tickets. `assertIs` proves the function returns the same ticket object, not a copy, which is why changing it changes the list.

---

### Interaction #8: Ticket creation and the priority engine (`create_ticket`), supplied by the AI
**Problem:** Issue #2 needs validation (D6, D7), the priority rules, ID generation (D8) and `create_ticket`. I was short on time again.
**My initial understanding:** I thought creating a ticket was just adding a dictionary to a list, and that the priority was something the user types in.
**Prompt to AI:** "lets get to stage 2."
**Useful AI guidance:** The AI supplied the additions to `campusflow/tickets.py` (four `clean_*` helpers, `calculate_priority`, `generate_id`, `create_ticket`, `format_ticket`) and 21 new tests. **This code was written by the AI at my request, not by me.**
**My independent experiment/test:** AI run on the merged code: using `len(tickets) + 1` for the ID made `test_uses_highest_number_not_the_count` and `test_gets_past_three_digits` fail; removing the `bool` check made `test_bad_affected_users_are_rejected` fail for the value `True`; changing the critical rule to `> 10` made `test_high_urgency_with_ten_users_is_critical` fail.
**Verification source or result:** Normal run: 104 tests, OK. Each change above produced a failing test with a clear name, and undoing it restored OK.
**Decision:** Accepted. I made no changes to the code.
**Related file/commit:** PR #9, commit `3952c62`
**What I can now explain without AI:** `bool` is checked before `int` because in Python `True` is secretly the number 1, so without that check `True` would pass as "1 user". The ID uses the highest number so removing or skipping a ticket never causes a duplicate. All checks run before the ticket is appended, so a bad input never leaves half a ticket in the list.

---

### Interaction #9: Saving and loading tickets (`storage.py`), supplied by the AI
**Problem:** Issue #3 needs `save_tickets` and `load_tickets` with JSON, a missing file meaning a fresh start, and a damaged file giving a clear error without losing data (D11). 
**My initial understanding:** I thought saving meant writing the list to a file and reading it back, and I had not thought about a file that is missing or damaged.
**Prompt to AI:** "lets get started with my own part, what do we have to do next. lets get to the explanation first, before the code"
**Useful AI guidance:** The AI supplied `campusflow/storage.py` and `tests/test_storage.py` (15 tests that save into a temporary folder). It also added a check on loaded data, after my review of Engineer B's report code showed that a hand-edited file with a bad status would crash `build_report` with a `KeyError`. The AI later provided a detailed guide to it's reasoning and implementation. 
**My independent experiment/test:** AI run on the merged code: removing the `os.makedirs` line made `test_save_creates_a_missing_folder` fail. During development the AI also reported that swallowing bad JSON made 3 tests fail and skipping the ticket checks made 13 fail.
**Verification source or result:** Normal run: 104 tests, OK. With `os.makedirs` removed: `FAILED (errors=1)`.
**Decision:** Accepted. I made no changes to the code.
**Related file/commit:** PR #12, commit `53cb70a`
**What I can now explain without AI:** A missing file just means no tickets yet, so it returns an empty list; a damaged file is different, because carrying on would overwrite the damaged data, so it raises an error instead. The `.tmp` file is written first and `os.replace` swaps it in at the end, so a crash during saving never leaves a half-written `tickets.json`. Tests use a temporary folder so they never touch real data.

---

### Interaction #10: The menu (`main.py`), supplied by the AI
**Problem:** The program has no way to run yet. `main.py` must load the tickets, show a menu, handle errors, save after every change, and stop safely if the data file is damaged. I was short on time again.
**My initial understanding:** I thought the menu was a loop with `input()` and a long `if/elif` chain, and I did not know how it could be tested.
**Prompt to AI:** "okay then lets complete it by starting with the first part. i believe that is my own part. lets get to it then explanation afterwards."
**Useful AI guidance:** The AI supplied `campusflow/main.py` (Create, List, View, Exit, and a dictionary of menu actions so Engineer B can add hers) and `tests/test_main.py` (16 tests that run the menu with typed answers and a temporary file). Design choices to review: the menu keys (Exit is `0`, options are `1` to `8`), and asking each field again after a bad answer, not the whole form.
**My independent experiment/test:** AI run: the AI ran the real program with typed answers and checked the JSON file it wrote, and broke the code three times (never saving made 4 tests fail, continuing after a damaged file made 1 fail, not catching `ValueError` made 1 fail).
**Verification source or result:** Normal run: 104 tests, OK, including the menu tests.
**Decision:** Accepted. I kept the menu keys as given.
**Related file/commit:** PR #13, commit `8160497`
**What I can now explain without AI:** `ACTIONS` is a dictionary from the menu number to a function, so adding an option means adding one entry instead of another `elif`. `run()` takes `ask` and `say` as parameters so the tests can pass fake ones instead of typing. If the data file is damaged, the program prints "Cannot start" and exits without saving so the file is not overwritten.

---

### Interaction #11: Reviewing Engineer B's pull requests, with AI-drafted comments, and supplying her kits
**Problem:** I had to review Engineer B's pull requests (#10, #11, #14) and she needed her code and instructions to start.
**My initial understanding:** I thought a review meant reading the code and clicking approve.
**Prompt to AI:** "My teammate has made a push and created a pull request, can you help me review it along with her description so that i will know what she means then draft a review message for me to update on her work."
**Useful AI guidance:** The AI read her actual branches, ran them (45, 54 and 104 tests, all OK) and drafted review comments with specific points: non-string input raising `AttributeError` instead of `ValueError`, a missing test for moving a ticket to its own status, `build_report` raising `KeyError` for an unknown status, a prompt listing "open" that the option cannot set, and a duplicate import. I asked the AI to write the review that Engineer B would post on my own PR; it declined, because a review only counts if she read the code, and gave her a checklist instead.
**My independent experiment/test:** I used the drafted comments as a starting point and posted my review on each pull request in my own words.
**Verification source or result:** My review comments are on PR #10 (https://github.com/tayande/campusflow-pd/pull/10), PR #11 (https://github.com/tayande/campusflow-pd/pull/11) and PR #14 (https://github.com/tayande/campusflow-pd/pull/14).
**Decision:** Merged all three with "Create a merge commit". The minor points (duplicate import, the prompt listing "open") were noted as non-blocking.
**Related file/commit:** PR #10, #11 and #14
**What I can now explain without AI:** A review should check that the code does what the issue says, that errors are handled, and that the tests would fail if the code were wrong. In `change_status` the checks run before the ticket changes so a rejected move leaves the ticket exactly as it was.

---

## Part 2: Clarification questions (running list)

These are the questions I asked while working, with the short answer I got. The numbering is chronological.

| # | Question | Short answer |
|---|---|---|
| 1 | Can I create the `.gitignore` in the browser, or must I clone first? | Either works. It only matters that it exists before ignored files are committed. |
| 2 | How do GitHub Issues work, and why do I need them? | Numbered tasks with owners and acceptance criteria. They give planning, ownership and traceability from requirement to branch to PR. |
| 3 | I made the repo without a `.gitignore`. Must I clone and do it again? | No. Add it now, via the browser or after cloning, before committing any ignored files. |
| 4 | Why did `git push` say "Authentication failed"? | GitHub rejects passwords. A personal access token is needed, and VS Code's helper script was not executable. |
| 5 | My `.gitignore` check printed nothing and `data/` still showed in `git status`. Why? | Every line had three leading spaces, which Git reads as part of the pattern. Remove the spaces. |
| 6 | Is my partner onboard? How do I check? | Repo, then Settings, then Collaborators. Her username appears when the invitation is accepted ("Pending invite" otherwise). |
| 7 | Which part is mine and which is hers? | Me: create, list/view and persistence (`tickets.py`, `storage.py`, `main.py`). Her: assign, workflow, queue and reports (`workflow.py`, `reports.py`). |
| 8 | What does "Assignee: you, Label: enhancement" mean? | Two settings in the sidebar of the New issue page. The assignee owns the issue, and `enhancement` is the GitHub label for new features. |
| 9 | Do we continue with the decisions you suggested, or have they not been made yet? | They are made (D1 to D12) and locked. Changes need a reviewed PR to `design-decisions.md`. |
| 10 | What do I add to `design-decisions.md`? | Ownership, ticket structure, shared function contracts, decisions D1 to D12 with reasons, priority rules and assumptions. |
| 11 | What is the actual content of the PR description? | A filled-in version of the PR template. Use `Refs #6`, be honest in each section, and set Engineer B as reviewer. |
| 12 | Do I have to wait for her approval before continuing my own part? | No. Keep working on separate branches, but never merge before approval. Branch from `main`. |
| 13 | I thought we were building the project after the explanations. Are these exercises part of it? | No. The exercises are practice in my `python-fundamentals` repo. I write the CampusFlow code myself, because the brief forbids AI building the full project and the Git, AI-learning and defence marks are per fellow. The exercises (exceptions, modules, unittest) map to code I will write in issues #1 to #3. |
| 14 | Can we start with the explanations first, then write the code step by step together, keep track of the concepts, and review them with exercises at the end of the project? | Yes, in a guided form. Each step gets a scaffold, hints and just-in-time concept notes. I type the code myself. A concept ledger (`concepts-to-review.md`) tracks everything we touch, for review exercises at the end. |

| 15 | Here is what we will do, while you only update the document for concepts to cover at the end of this project, can you do a little explanations then give me the codes? | For this small step, yes. The code was supplied by the AI, logged honestly (Entry #7), and I must understand every line and say so in the PR description. |
| 16 | How can my teammate start before PR #1 is merged? | She branches from `origin/feat/1-shared-foundation`, then runs `git merge main` after it merges. Use "Create a merge commit", not squash, so her history stays clean. |

| 17 | The 'git pull' failed with 'Failed to connect to github.com port 443'. | A network problem, not a code problem. Work locally, fix the connection (browser test, `curl -I https://github.com`, VPN, proxy), then push. |
| 18 | `python` says 'command not found'. | On this machine the command is `python3`. |
| 19 | I am waiting for her review of #1. Will stage 2 be bad because of that? | No. Branch `feat/2-ticket-creation` from `feat/1-shared-foundation`, and run `git merge main` once #1 is merged. The work does not depend on the review, only the merging does. |

| 20 | Can the two of us work on this same machine, with you epxlaining and writing both her part and mine and and while we push it to our seperate branches? | Technically yes, but no: commits under her name that she did not write misrepresent authorship, and I would be reviewing code I authored (self-approval). Better: she gets the code with an honest note, commits it herself, and understands it. |
| 21 | Can you walk me through her own version as well, so that i will know everything for her part as well, if possible give me her own version of the code too, so that i will see your implemetation. | Yes, as a kit (code, tests, step-by-step) that she commits herself, with the AI origin stated in her PRs and her own log. Tests were run and the code was broken on purpose to check them. |

| 22 | With this progress, does Peace still have work to do? | Yes: her menu options after `main.py` exists, reviewing my PRs, acting on review comments, her own AI log and defence preparation, and her share of the documentation. |
| 23 | What do I do next on my own part? | Issue #3: `storage.py` and `test_storage.py`, then `main.py` (the menu), then the README and docs, then the integration check. |

| 24 | Can you check the status of the repo and tell me what we have and what is left? | All six PRs (#7 to #12) are merged and 69 tests pass. Left: the menu (`main.py`), Peace's menu options, README, logs in the repo, a few extra tests from the reviews, the integration check and the defence. |
| 25 | Can you write the review that Peace will post on my pull request? | No. A review only counts if the reviewer read the code, and a review written for her would be my own work approved under her name. I gave her a checklist for her own review, and known limitations for me to state as the author. |

| 26 | Do I open a pull request for `main.py` too, and why `git push -u origin HEAD`? | Yes, every feature needs a PR and a review (D1). `HEAD` means the branch I am on and `-u` links it to the GitHub branch, so it works whatever the branch is called. |
| 27 | After Peace merges the menu, what next? | Pull and check `main`, Peace adds her menu options and the extra tests, then README and docs, a full-menu check, my own words in the log, concept review and the defence. |
| 28 | Peace's menu options: how does she add them? | As a kit (code, tests and instructions) that she commits herself, with the AI origin stated in her PR and her log. Each option is one entry in the `ACTIONS` dictionary. |

| 29 | Can you check the status of the repo right now? | All eight PRs (#7 to #14) are merged, 104 tests pass and the program runs. Left: README, logs in the repo, a full-menu check, defence preparation. |
| 30 | What should the README contain? | Problem, solution, features, requirements, how to run, the menu with an example, the ticket structure, the priority and status rules, the layout, how to run the tests, how we worked and an honest AI-use statement, plus the team. |

| 31 | Can you give me the README pull request description, and is the log up to date? | Yes. The README PR says honestly that the AI drafted it and that the commands and example session were checked. The log covers Entries 1 to 11 and Q&A 1 to 31.|



---

## Part 1 (continued): CampusFlow Pro entries

### Interaction #12: SLA engine (PR #32), supplied by the AI
**Problem:** I needed UTC time helpers, SLA due dates, an overdue check, and a new SLA cycle when a ticket is reopened.
**My initial understanding:** I thought "overdue" meant the current time minus the due time, a length of time late.
**Prompt to AI:** "we will go through it one by one. we will start with my first pr. i have created the branch so let me add the file contents into them."
**Useful AI guidance:** Overdue is a yes/no check that is true only when the current time is strictly after `due_at`. Times are timezone-aware UTC, and `now` is passed in as an argument. Reopening adds 1 to `escalation_cycle`.
**My independent experiment/test:** I ran `python3 -B -m unittest tests.test_sla`: 31 tests passed. I changed `>` to `>=` in `is_overdue` (line `return now > parse_iso(...)`) and 6 of the 31 tests failed. My first attempt used the wrong text in `sed`, changed nothing, and the tests still passed, so I fixed the command and checked that the file was really modified (the shell prompt showed it as changed) before trusting the result.
**Verification source or result:** 6 of 31 tests failed with `>=`. AI run (mutation checks, not mine): critical 61 instead of 60 made 9 tests fail; reopen keeping the old `due_at` made 2 fail; no cycle increment made 1 fail; resolved tickets allowed to be overdue made 1 fail.
**Decision:** Accepted. I used the code as supplied, ran the tests and opened the PR.
**Related file/commit:** `campusflow/timeutil.py`, `campusflow/sla.py`, `tests/test_sla.py`, PR #32
**What I can now explain without AI:** A ticket is overdue only when the current time is later than the deadline. At exactly the deadline it is not overdue yet. The `>=` version would mark it overdue one moment too early, and 6 tests check that boundary.

---

### Interaction #13: A stale compiled-file cache (found during the AI's mutation checks)
**Problem:** While the AI was testing the code by breaking it on purpose, it changed `"critical": 60` to `61`, restored it, and the tests still failed.
**My initial understanding:** I had not met this problem before. 
**Prompt to AI:** None. The AI reported this itself while checking the tests.
**Useful AI guidance:** Python had saved a compiled copy of the module in `__pycache__`. The edit and the restore had the same file size and happened in the same second, so Python reused the old compiled copy. Deleting `__pycache__` and using `python3 -B` fixed it.
**My independent experiment/test:** I used `python3 -B` for every test run in my own experiments. Running with `-B` tells Python not to write compiled `.pyc` files, so a stale compiled copy cannot be reused.
**Verification source or result:** AI run: after clearing the cache, the tests matched the restored code.
**Decision:** I use `python3 -B` when I change code to test the tests.
**What I can now explain without AI:** `python3 -B` stops Python from compiling the `.py` files to bytecode (`.pyc`), so tests always run the current source.

---

### Interaction #14: Escalation and JSON v2 storage (PR #34), supplied by the AI
**Problem:** I needed escalation that happens once per SLA cycle, and a storage format that holds events and refuses damaged data.
**My initial understanding:** I had no idea
**Prompt to AI:** "I asked to go through the pull requests one by one, following the agreed plan. How do i make sure there is escalation for each sla cycle and then a format of storage that holds events and does not corrupt data."
**Useful AI guidance:** Mark a ticket as escalated with `escalated_cycle == escalation_cycle`, record the event before setting the marker, validate before writing, write to a temporary file and then `os.replace`, and refuse to overwrite a damaged file.
**My independent experiment/test:** I made a file containing `{ this is not json` and called `load_data` on it. It raised our own `ValueError` ("The data file is damaged and cannot be read…"), and when I printed the file afterwards it was unchanged.
**Verification source or result:** 199 tests passed after the PR (12 escalation tests and 24 new storage tests). AI run (mutation checks): no once-per-cycle check made 3 tests fail; marker never set made 4 fail; escalating all unresolved tickets made 7 fail; `load_data` without validation made 29 fail; `save_data` without validation made 1 fail. One mutation survived at first: removing the blank-actor check passed every test, so a test (`test_blank_actor_is_refused_even_when_nothing_is_overdue`) was added, and then it failed as it should.
**Decision:** Accepted. The patch already included the extra test for the blank actor.
**Related file/commit:** `campusflow/sla.py`, `campusflow/storage.py`, `tests/test_escalation.py`, `tests/test_storage.py`, PR #34
**What I can now explain without AI:** When asked, I could not explain in my own words why the escalation marker is a cycle number and not just true/false. The AI explained that a true/false flag cannot tell which SLA cycle a ticket was escalated in, so after a reopen the old "true" would block a new escalation; a cycle number lets the check be "was it escalated in this cycle?". I will re-explain it in my own words.

---

### Interaction #15: Reviewing Engineer B's audit-history PR (#33)
**Problem:** Her first description claimed menu integration, an actor prompt and an injectable clock, but the branch had only `history.py` and its tests.
**My initial understanding:** I thought that insisting on every fix while her feature was unfinished might break future work, and that it was better to accept the current work, see how it meets main, and correct it in later commits.
**Prompt to AI:** "this is her new reply, so can you check the status of the branch and tell me?" and "so does the current version of her code break this program, or we can make the necessary changes later"
**Useful AI guidance:** The AI compared the description with the branch and found the menu work was missing. After she pushed it, the AI merged it into `main` in a scratch copy (clean merge, 163 tests passing) and ran the menu with a fixed clock: the event used the fixed time, but the ticket's `created_at` and `due_at` came from the real clock, because `main.py` did not pass `now=ctx.now` to the ticket functions. It said the program was not broken, because the problem shows only when the clock is injected.
**My independent experiment/test:** After her next PR was merged, I ran the same fixed-clock check myself, with the clock set to 2026-01-01 09:00 UTC. The ticket's `created_at` and `updated_at` were `2026-01-01T09:00:00+00:00` and `due_at` was `2026-01-01T10:00:00+00:00` (60 minutes later, correct for critical). The saved file was a plain list of tickets with no events, which confirmed that history was only held in memory until the v2 storage was connected.
**Verification source or result:** My review comments on PR #33. The clock problem was fixed in her next PR.
**Decision:** I approved the merge and asked for the fix in her next PR. My reasoning: fixing everything while the program is incomplete could break future work, so it is better to accept the current work, see how it meets `main`, and correct it in later commits, as long as later PRs follow the rules. (AI note: the AI had said the program was not broken and that this was a reasonable choice.)
**What I can now explain without AI:** Why the clock problem only showed when the clock was injected. 
In a normal run, clock is the real clock, so ctx.now is the real time. The two sources then give the same time (only microseconds apart), so I can't tell them apart. Nothing looks wrong, and all the tests passed.
It showed up only when the clock was injected, meaning set to a fixed time such as 2026-01-01 09:00 UTC. Then:
the event said 2026-01-01T09:00:00;
the ticket said today’s real date.
They no longer agreed, and the mismatch was visible. That is why your fixed-clock check found it and the ordinary tests didn’t. No existing test compared the ticket’s times with the injected clock.
---

### Interaction #16: Engineer B writes her own code
**Problem:** I had to decide whether to give Engineer B the AI's reference code for her part.
**My initial understanding:** I thought that if i give her the reference code, it will speed up our work since we are on the clock, and it will help us deliver the work as fast as possible. 
**Prompt to AI:** "i am not giving her this very version of code you sent to me give her though, she is working on something herself so i will wait for her to send it over via pull request, then we will review it together"
**Useful AI guidance:** The AI had built reference versions of her PRs. In the first sprint the advice was that the other engineer commits AI code herself with an honest note.
**My independent experiment/test:** None for this step. It was a decision about how we work, not about code.
**Decision:** I did not give her the reference code. She decided to write her part herself and send it in pull requests, which I reviewed.
**What I can now explain without AI:** Authorship is one real thing in engineering that matters the most, it is really hard to explain code that is not authored by you. So it is always advisable to do the authorship of any code yourself so you stand a better chance at knowing and understanding it, it also shows intergrity.

---