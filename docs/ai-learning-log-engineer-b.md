# AI Learning Log: Engineer B

**Fellow:** Peace Onma Oigoga (GitHub: onma77)

**AI assistant used:** ChatGPT, as a tutor and reviewer.

> **How to use this file:** This is an honest working draft based on the
> CampusFlow handoff and our conversation. I have filled in details that
> are supported by the conversation and kept unverified work clearly
> marked. Do not claim you ran tests, changed code, reviewed/approved a
> PR, or corrected an AI suggestion unless you personally did it.
> Replace every **ACTION NEEDED** note with your real observation after
> completing that step.

------------------------------------------------------------------------

## Part 1: Learning log entries

### Interaction #1: Reading the handoff and the shared decisions (D1 to D12)

**Problem:** I joined a project where Engineer A and I write separate
modules. I needed to understand the shared decisions (tickets as a list
of dictionaries passed first, `ValueError` for errors, no `input()` or
`print()` in the logic, the workflow table, and the queue rule) before
writing code.

**My initial understanding:** Before reading the handoff carefully, I
needed a clearer picture of the whole project, how the features fit
together, and which parts I was responsible for as Engineer B.

**Prompt to AI:** "Explain every step of this project and how to start."

**Useful AI guidance:** The handoff divides the work between the two
engineers. My assigned work is ticket assignment and status workflow
(issue #4), the work queue and reports (issue #5), related tests, and
adding menu options. The shared decisions say logic functions receive
the ticket list first, raise `ValueError` for invalid actions, and do
not use `input()` or `print()`. The menu handles user interaction and
catches errors.

**My independent experiment/test:** **ACTION NEEDED:** I should explain
D3 and D4 in my own words, then inspect `campusflow/tickets.py` and
identify how `get_ticket()` finds a ticket. Record what I actually
checked here.

**Verification source or result:** The project handoff, especially the
shared decisions and Engineer B responsibilities. I have not recorded a
personal test result for this interaction yet.

**Decision:** I understand the proposed design and will follow it unless
Engineer A and I agree to change a decision and update
`docs/design-decisions.md`.

**Related file/commit:** `docs/design-decisions.md`; project handoff.

**What I can now explain without AI:** Logic functions raise errors
instead of printing messages because they should perform the task
without controlling the user interface. `main.py` can catch the error
and display it. Keeping `input()` and `print()` out of logic functions
also makes those functions easier to test.

------------------------------------------------------------------------

### Interaction #2: The status workflow (`assign_ticket`, `change_status`, `reopen_ticket`)

**Problem:** Tickets must move from `open` to `in_progress` to
`resolved`, with rules: a ticket must be assigned before work starts, an
open ticket cannot jump directly to resolved, and a resolved ticket must
be reopened through the specific reopen function.

**My initial understanding:** I needed to learn how to check whether a
requested status change is allowed and how to make sure an invalid
operation does not change the ticket.

**Prompt to AI:** No feature-specific prompt about implementing these
functions is recorded in the conversation available for this draft.
**ACTION NEEDED:** If I asked a separate prompt while coding, paste the
exact prompt here. Do not present a suggested prompt as one I already
used.

**Useful AI guidance:** The handoff specifies the allowed status
transitions and requires invalid operations to raise `ValueError`. The
repository scaffold describes using an `ALLOWED_MOVES` dictionary to
represent permitted transitions. All checks should happen before
changing `ticket["status"]`, so a rejected operation leaves the ticket
unchanged. Reopening a resolved ticket keeps the assignee.

**My independent experiment/test:** **ACTION NEEDED:** Run
`python3 -m unittest discover -s tests -v` yourself and record the
actual result. If you deliberately break a check, record exactly what
you changed and the exact test that failed. Do not claim this experiment
happened until you have done it.

**Verification source or result:** The expected rules are in the handoff
and the workflow tests are in the repository. **ACTION NEEDED:** Add the
actual number of tests and the real test output from your own run.

**Decision:** I will follow the specified workflow rules. I will only
say I accepted or changed a particular code suggestion after checking
the code and recording what I actually did.

**Related file/commit:** `campusflow/workflow.py`,
`tests/test_workflow.py`, PR #10, commit `5592bf4` (as listed in the
supplied scaffold; confirm these references still match the repository).

**What I can now explain without AI:** `ALLOWED_MOVES` represents which
destination statuses are permitted from a current status. The function
checks the ticket's existence, the requested transition, and any
assignment requirement before changing the status. Changing the status
last prevents a rejected action from partially updating the ticket.

------------------------------------------------------------------------

### Interaction #3: The work queue and the summary report

**Problem:** The queue must list only open tickets, most urgent first,
with ties going to the lower numeric ticket ID. The report must show the
total and counts by status and priority, including categories with zero
tickets.

**My initial understanding:** I needed to understand how to put tickets
in priority order and how to count tickets by category. I also needed to
account for ticket IDs such as `T010`, whose numeric part should be
treated as 10.

**Prompt to AI:** No feature-specific prompt about implementing the
queue or report is recorded in the conversation available for this
draft. **ACTION NEEDED:** Add the exact prompt if I used one while
coding.

**Useful AI guidance:** The handoff requires the queue to include open
tickets only and to sort by priority, then numeric ID. The scaffold
describes a sorting key that returns a tuple containing the priority's
rank and the numeric part of the ID. Python sorts by the first tuple
item and then uses the second item to break ties. The report should
initialise every required status and priority count to zero, then count
the tickets. Unknown statuses or priorities should be handled according
to the implementation's validation rules.

**My independent experiment/test:** **ACTION NEEDED:** Build or inspect
a small list of tickets with mixed priorities and IDs, write down the
expected order before running the function, and compare it with the
actual output. Run the report on both an empty list and a mixed list.
Record only what I really tested.

**Verification source or result:** The queue and report requirements in
the handoff, plus `tests/test_workflow.py` and `tests/test_reports.py`
in the repository. **ACTION NEEDED:** Record the actual output and any
mismatch from your own run.

**Decision:** I will use the priority order and numeric-ID tie-breaker
specified by the project. I will keep all status and priority keys in
the report, even when their counts are zero.

**Related file/commit:** `campusflow/workflow.py` (`queue_order`,
`get_work_queue`), `campusflow/reports.py`, `tests/test_reports.py`, PR
#11 (as listed in the supplied scaffold; confirm these references still
match the repository).

**What I can now explain without AI:** A tuple sorting key lets Python
compare priority rank first and numeric ticket ID second. Starting each
report count at zero ensures the output includes every required
category, even if no ticket belongs to that category. Filtering the
queue into a new list also avoids changing the original tickets list
just to display the queue.

------------------------------------------------------------------------

### Interaction #4: Menu options for assign, status, reopen, queue and report

**Problem:** My logic functions need to be connected to the menu without
putting `input()` and `print()` inside the logic functions or breaking
Engineer A's menu loop.

**My initial understanding:** I needed to understand how the menu can
collect user input, call my functions, and show results while keeping
the business logic separate from user interaction.

**Prompt to AI:** The prompt recorded in this conversation was:
"https://github.com/tayande/campusflow-pd.git --- check this out for us
to work and build together." I also asked for an explanation of every
project step and how to start. A specific prompt about implementing the
menu is not recorded here. **ACTION NEEDED:** Add the exact prompt if I
used one during menu integration.

**Useful AI guidance:** The scaffold describes keeping each menu action
separate and passing the ticket list plus `ask` and `say` functions into
the action. The `ACTIONS` dictionary maps menu choices to their actions.
The menu loop catches `ValueError` and displays an understandable error
message. This keeps input/output in the menu layer rather than in the
logic functions.

**My independent experiment/test:** **ACTION NEEDED:** Run
`python3 -m campusflow.main` yourself and try the assign, status,
reopen, queue, and report options, including an unknown ticket ID.
Record the actual behaviour you observe.

**Verification source or result:** `campusflow/main.py`, the relevant
pull request, and the output from my own manual run. **ACTION NEEDED:**
Record what appeared on screen and whether the program saved successful
changes.

**Decision:** I will follow the project's separation between logic and
menu interaction. I will not claim the menu was manually tested until I
have run it myself.

**Related file/commit:** `campusflow/main.py` (assign, status, reopen,
queue and report actions), PR #14 (as listed in the supplied scaffold;
confirm these references still match the repository).

**What I can now explain without AI:** The `ACTIONS` dictionary connects
menu choices to the functions that handle them. Passing `ask` and `say`
as parameters makes menu actions easier to test with substitute
functions. Catching `ValueError` in the menu lets the program display an
error without placing printing inside the logic functions.

------------------------------------------------------------------------

### Interaction #5: A suggestion I checked and corrected (REQUIRED ENTRY)

> This entry must describe a real check. The conversation available for
> this draft does not establish that I have already found and corrected
> a specific AI suggestion. I must complete the experiment before
> submitting this as a completed entry.

**Problem:** **ACTION NEEDED:** Choose a real AI suggestion or piece of
suggested code that I was unsure about. State exactly what it was.

**My initial understanding:** **ACTION NEEDED:** Explain what I thought
was correct or potentially wrong and why I wanted to check it.

**Prompt to AI:** **ACTION NEEDED:** Paste the actual prompt and, if
possible, the relevant AI suggestion. Do not invent a past prompt.

**Useful AI guidance:** **ACTION NEEDED:** Summarise the actual
suggestion that I checked.

**My independent experiment/test:** Read the relevant code line by line.
Identify a concrete issue, weakness, or unclear part; make a correction
myself; then run the relevant test command. A possible way to
investigate is to check whether a rejected status transition leaves the
ticket unchanged, but I must only use this example if I actually perform
that test.

**Verification source or result:** **ACTION NEEDED:** Record the
specific problem found and the real test output that demonstrated it.

**Decision:** **ACTION NEEDED:** State what I corrected or rejected and
why, based on the experiment.

**Related file/commit:** **ACTION NEEDED:** Add the actual file and
commit SHA for my correction.

**What I can now explain without AI:** **ACTION NEEDED:** Explain the
lesson I learned from independently checking the suggestion rather than
trusting it automatically.

------------------------------------------------------------------------

### Interaction #6: Reviewing my partner's pull request

**Problem:** I need to review Engineer A's pull request carefully, leave
specific comments, and avoid approving it without checking the code.

**My initial understanding:** I needed guidance on how to review the
shared foundation and how to tell whether the code and tests meet the
agreed requirements.

**Prompt to AI:** "Check this out for us to work and build together,"
followed by the repository URL. I also asked for an explanation of the
project and its starting steps.

**Useful AI guidance:** The review should check the changed files,
compare the implementation with the requirements, and run the tests
locally. A useful review identifies specific issues or asks questions
about particular lines; a vague comment such as "Looks good" is not
sufficient. The team process requires at least two substantive review
comments before approval.

**My independent experiment/test:** **ACTION NEEDED:** Open PR #8, read
its changed files, and run the tests locally. Record the actual command
and output. If I have not submitted review comments, I must say that the
review is not yet complete.

**Verification source or result:** [PR #8 --- Shared
Foundation](https://github.com/tayande/campusflow-pd/pull/8) and my own
review of its changed files. **ACTION NEEDED:** Record at least two real
comments I posted, or state that I have not posted them yet.

**Decision:** No approval decision is recorded in this conversation.
**ACTION NEEDED:** After reviewing and testing the PR, record whether I
approved it or requested changes and explain why.

**Related file/commit:** [PR #8 --- Shared
Foundation](https://github.com/tayande/campusflow-pd/pull/8).

**What I can now explain without AI:** A pull request review checks
whether a change meets the requirements, behaves correctly, is
understandable, and has adequate tests. I should refer to specific code
or test behaviour in my comments and verify claims by inspecting the
code or running tests.

------------------------------------------------------------------------

## Part 2: Clarification questions (running list)

The first two prompts below are based on questions I actually asked in
this conversation. The remaining rows are suggested questions to ask
while doing the work; after asking them, replace the wording if
necessary and record the real answer and verification.

  -------------------------------------------------------------------------------------------------------
  \#                Question I asked                                AI's answer in      Did I verify it?
                                                                    short               How?
  ----------------- ----------------------------------------------- ------------------- -----------------
  1                 "Explain every step of this project and how to  CampusFlow is a     I received an
                    start."                                         command-line ticket explanation based
                                                                    manager. The        on the handoff. I
                                                                    handoff divides     still need to
                                                                    responsibilities    verify the
                                                                    between Engineer A  current
                                                                    and Engineer B and  repository files
                                                                    defines the         and run the
                                                                    features, rules,    relevant commands
                                                                    tests, and Git      myself.
                                                                    workflow.           

  2                 "https://github.com/tayande/campusflow-pd.git   The repository is   **ACTION
                    --- check this out for us to work and build     the project to use. NEEDED:** Confirm
                    together."                                      The proposed next   the current PR
                                                                    step is to inspect  status, inspect
                                                                    the                 the changed
                                                                    shared-foundation   files, and run
                                                                    PR, set up the      the tests
                                                                    local copy, and     locally.
                                                                    verify the tests    
                                                                    before coding.      

  3                 Suggested: "Can you explain `raise ValueError`  This should help me Ask this
                    and `try/except` with a small example unrelated understand how      question,
                    to CampusFlow?"                                 functions reject    complete a small
                                                                    invalid operations  exercise, and
                                                                    and how the menu    record my actual
                                                                    handles those       result.
                                                                    errors.             

  4                 Suggested: "How can I test that a rejected      This should help me Ask this
                    status change leaves the ticket unchanged?"     design a test that  question, write
                                                                    checks both the     or run the test,
                                                                    exception and the   and record the
                                                                    ticket's original   actual output.
                                                                    state.              

  5                 Suggested: "Can you explain how `sorted()` uses This should clarify Ask this
                    a tuple key to sort by priority and numeric     the queue's two     question, predict
                    ticket ID?"                                     sorting criteria.   the order of a
                                                                                        hand-built ticket
                                                                                        list, and compare
                                                                                        it with the
                                                                                        program's output.
  -------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## Part 3: Use of AI statement

I used ChatGPT as a tutor to help me understand the CampusFlow handoff,
the division of responsibilities, the project structure, and the
expected workflow for reviewing the repository and building my features.
The conversation so far mainly covers explanation and planning; it does
not establish that ChatGPT wrote my implementation or that I
independently ran the project's tests. I will describe any code
suggestions I use, changes I make myself, and test results accurately,
and I will not claim that I verified or corrected something until I have
actually done so.