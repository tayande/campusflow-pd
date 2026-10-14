import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from campusflow.main import run
from campusflow.storage import load_data, save_data


FIXED_TIME = datetime(2026, 10, 14, 10, 0, tzinfo=timezone.utc)


def fixed_clock():
    """A clock that always says the same time, so tests never depend on the real one."""
    return FIXED_TIME


def make_ticket(ticket_id, title, category, urgency, affected_users,
                priority, status, assigned_to=None,
                escalation_cycle=0, escalated_cycle=None,
                due_in_minutes=120):
    """Build a valid version 2 ticket by hand.

    due_in_minutes is measured from FIXED_TIME, so a negative value is already overdue.
    """
    stamp = FIXED_TIME.isoformat()
    return {
        "id": ticket_id, "title": title, "category": category,
        "urgency": urgency, "affected_users": affected_users,
        "priority": priority, "status": status, "assigned_to": assigned_to,
        "created_at": stamp, "updated_at": stamp,
        "due_at": (FIXED_TIME + timedelta(minutes=due_in_minutes)).isoformat(),
        "escalation_cycle": escalation_cycle, "escalated_cycle": escalated_cycle,
    }


def make_tickets():
    """Return a fresh list of two tickets, so tests never share data."""
    return [
        make_ticket("T001", "Campus Wi-Fi is down", "Network", "high", 15,
                    "critical", "open"),
        make_ticket("T002", "Laptop will not start", "Hardware", "low", 1,
                    "low", "in_progress", "Sam"),
    ]


class MenuTestCase(unittest.TestCase):
    """Runs the menu with typed answers and a temporary data file."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = os.path.join(self.folder.name, "tickets.json")
        self.output = []
        self.prompts = []

    def use_menu(self, answers, actor="Tester", clock=fixed_clock):
        """Run the menu with these answers; return its exit code.

        The menu first asks for the operator's name, so it is typed here
        automatically. Pass actor=None to type it yourself in `answers`.
        The prompts are recorded in `self.prompts`, since only a real
        input() would show them in the output.
        """
        remaining = list(answers) if actor is None else [actor] + list(answers)

        def fake_ask(prompt):
            self.prompts.append(prompt)
            if not remaining:
                raise EOFError  # the user ran out of input
            return remaining.pop(0)

        return run(self.path, ask=fake_ask, say=self.output.append, clock=clock)

    def text(self):
        return "\n".join(self.output)

    def saved_tickets(self):
        """The tickets as they are in the file now."""
        return load_data(self.path)[0]

    def saved_events(self):
        """The event history as it is in the file now."""
        return load_data(self.path)[1]


class TestStartAndExit(MenuTestCase):
    def test_exit_ends_cleanly(self):
        self.assertEqual(self.use_menu(["0"]), 0)
        self.assertIn("Goodbye.", self.output)

    def test_menu_lists_the_options(self):
        self.use_menu(["0"])
        for label in ["Create a ticket", "List all tickets", "View one ticket", "Exit"]:
            self.assertIn(label, self.text())

    def test_nothing_is_saved_if_nothing_changed(self):
        self.use_menu(["2", "0"])
        self.assertFalse(os.path.exists(self.path))

    def test_unknown_choice_shows_a_message_and_continues(self):
        self.use_menu(["banana", "", "0"])
        self.assertEqual(self.text().count("Please choose a number"), 2)

    def test_running_out_of_input_exits_cleanly(self):
        self.assertEqual(self.use_menu([]), 0)
        self.assertIn("Goodbye.", self.output)


class TestDamagedFile(MenuTestCase):
    def test_damaged_file_stops_the_program_and_is_not_overwritten(self):
        with open(self.path, "w", encoding="utf-8") as file:
            file.write("{ not json")
        code = self.use_menu(["1", "Title", "Network", "low", "1", "0"])
        self.assertEqual(code, 1)
        self.assertIn("Cannot start", self.text())
        self.assertNotIn("=== CampusFlow ===", self.text())
        with open(self.path, encoding="utf-8") as file:
            self.assertEqual(file.read(), "{ not json")


class TestCreate(MenuTestCase):
    def test_create_saves_the_ticket_to_the_file(self):
        self.use_menu(["1", "Printer jam", "hardware", "MEDIUM", "4", "0"])
        saved = load_data(self.path)[0]
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["id"], "T001")
        self.assertEqual(saved[0]["category"], "Hardware")
        self.assertEqual(saved[0]["urgency"], "medium")
        self.assertEqual(saved[0]["priority"], "medium")
        self.assertIn("Created T001 with priority medium.", self.output)

    def test_bad_answers_are_asked_again(self):
        answers = [
            "1",
            "   ", "Printer jam",      # blank title, then good
            "plumbing", "Hardware",     # bad category, then good
            "urgent", "low",            # bad urgency, then good
            "0", "abc", "-2", "2.5", "3",  # bad users x4, then good
            "0",
        ]
        self.use_menu(answers)
        self.assertEqual(self.text().count("Error:"), 7)
        saved = load_data(self.path)[0]
        self.assertEqual(saved[0]["affected_users"], 3)
        self.assertEqual(saved[0]["priority"], "medium")

    def test_new_ticket_continues_after_existing_ones(self):
        save_data(self.path, make_tickets(), [])
        self.use_menu(["1", "Projector", "Other", "low", "1", "0"])
        ids = [t["id"] for t in load_data(self.path)[0]]
        self.assertEqual(ids, ["T001", "T002", "T003"])

    def test_two_tickets_in_one_session_get_different_ids(self):
        self.use_menu(["1", "A", "Other", "low", "1",
                       "1", "B", "Other", "low", "1", "0"])
        ids = [t["id"] for t in load_data(self.path)[0]]
        self.assertEqual(ids, ["T001", "T002"])

    def test_leaving_in_the_middle_of_create_saves_nothing(self):
        self.use_menu(["1", "Half a ticket", "Other"])
        self.assertFalse(os.path.exists(self.path))


class TestListAndView(MenuTestCase):
    def test_list_with_no_tickets(self):
        self.use_menu(["2", "0"])
        self.assertIn("No tickets yet.", self.output)

    def test_list_shows_every_saved_ticket(self):
        save_data(self.path, make_tickets(), [])
        self.use_menu(["2", "0"])
        self.assertIn("T001 | Campus Wi-Fi is down | Network | critical | open | unassigned",
                      self.output)
        self.assertIn("T002 | Laptop will not start | Hardware | low | in_progress | Sam",
                      self.output)

    def test_view_shows_all_details(self):
        save_data(self.path, make_tickets(), [])
        self.use_menu(["3", " t002 ", "0"])
        self.assertIn("Title:          Laptop will not start", self.output)
        self.assertIn("Assigned to:    Sam", self.output)
        self.assertIn("Status:         in_progress", self.output)

    def test_view_unknown_ticket_shows_error_and_keeps_going(self):
        save_data(self.path, make_tickets(), [])
        self.use_menu(["3", "T999", "0"])
        self.assertIn("Error: Ticket T999 not found", self.output)
        self.assertIn("Goodbye.", self.output)

    def test_list_does_not_change_the_file(self):
        save_data(self.path, make_tickets(), [])
        with open(self.path, encoding="utf-8") as file:
            before = file.read()
        self.use_menu(["2", "3", "T001", "0"])
        with open(self.path, encoding="utf-8") as file:
            self.assertEqual(file.read(), before)


def make_workflow_tickets():
    """Tickets in every state, for the workflow menu options."""
    return [
        make_ticket("T001", "Problem 1", "Other", "low", 1, "low", "open"),
        make_ticket("T002", "Problem 2", "Other", "low", 1, "critical", "open", "Sam"),
        make_ticket("T003", "Problem 3", "Other", "low", 1, "high", "in_progress", "Ada"),
        make_ticket("T004", "Problem 4", "Other", "low", 1, "medium", "resolved", "Kim"),
    ]


class WorkflowMenuTestCase(MenuTestCase):
    def setUp(self):
        super().setUp()
        save_data(self.path, make_workflow_tickets(), [])

    def file_text(self):
        with open(self.path, encoding="utf-8") as file:
            return file.read()

    def saved(self, ticket_id):
        for ticket in load_data(self.path)[0]:
            if ticket["id"] == ticket_id:
                return ticket


class TestMenuListsAllOptions(WorkflowMenuTestCase):
    def test_menu_shows_the_workflow_options(self):
        self.use_menu(["0"])
        for label in ["Assign a ticket", "Change a ticket's status",
                      "Reopen a resolved ticket", "Show the work queue",
                      "Show the report"]:
            self.assertIn(label, self.text())


class TestAssignOption(WorkflowMenuTestCase):
    def test_assign_saves_the_name(self):
        self.use_menu(["4", "t001", "  Lee ", "0"])
        self.assertEqual(self.saved("T001")["assigned_to"], "Lee")
        self.assertIn("T001 is now assigned to Lee.", self.output)

    def test_assign_unknown_ticket_shows_error_and_changes_nothing(self):
        before = self.file_text()
        self.use_menu(["4", "T999", "Lee", "0"])
        self.assertIn("Error: Ticket T999 not found", self.output)
        self.assertEqual(self.file_text(), before)

    def test_assign_blank_name_is_rejected(self):
        before = self.file_text()
        self.use_menu(["4", "T001", "   ", "0"])
        self.assertIn("Error: Staff name cannot be blank", self.output)
        self.assertEqual(self.file_text(), before)

    def test_assign_resolved_ticket_is_rejected(self):
        before = self.file_text()
        self.use_menu(["4", "T004", "Lee", "0"])
        self.assertIn("Error:", self.text())
        self.assertEqual(self.file_text(), before)


class TestStatusOption(WorkflowMenuTestCase):
    def test_status_change_is_saved(self):
        self.use_menu(["5", "T003", "resolved", "0"])
        self.assertEqual(self.saved("T003")["status"], "resolved")
        self.assertIn("T003 is now resolved.", self.output)

    def test_assigned_ticket_can_start(self):
        self.use_menu(["5", "T002", "in_progress", "0"])
        self.assertEqual(self.saved("T002")["status"], "in_progress")

    def test_unassigned_ticket_cannot_start(self):
        before = self.file_text()
        self.use_menu(["5", "T001", "in_progress", "0"])
        self.assertIn("Error: Assign the ticket", self.text())
        self.assertEqual(self.file_text(), before)

    def test_nonsense_status_is_rejected(self):
        before = self.file_text()
        self.use_menu(["5", "T002", "banana", "0"])
        self.assertIn("Error: Status must be one of", self.text())
        self.assertEqual(self.file_text(), before)


class TestReopenOption(WorkflowMenuTestCase):
    def test_reopen_keeps_the_assignee(self):
        self.use_menu(["6", "T004", "0"])
        ticket = self.saved("T004")
        self.assertEqual(ticket["status"], "open")
        self.assertEqual(ticket["assigned_to"], "Kim")
        self.assertIn("T004 is open again.", self.output)

    def test_reopen_a_ticket_that_is_not_resolved_is_rejected(self):
        before = self.file_text()
        self.use_menu(["6", "T001", "0"])
        self.assertIn("Error:", self.text())
        self.assertEqual(self.file_text(), before)


class TestQueueAndReportOptions(WorkflowMenuTestCase):
    def test_queue_shows_open_tickets_most_urgent_first(self):
        self.use_menu(["7", "0"])
        self.assertIn("Work queue (most urgent first):", self.output)
        lines = [line for line in self.output if line[:4] in ("1. T", "2. T", "3. T")]
        self.assertEqual(len(lines), 2)  # T003 is in progress, T004 is resolved
        self.assertTrue(lines[0].startswith("1. T002"))
        self.assertTrue(lines[1].startswith("2. T001"))

    def test_empty_queue_message(self):
        save_data(self.path, [], [])
        self.use_menu(["7", "0"])
        self.assertIn("The work queue is empty.", self.output)

    def test_report_shows_the_counts(self):
        self.use_menu(["8", "0"])
        self.assertIn("Total tickets: 4", self.output)
        self.assertIn("  open: 2", self.output)
        self.assertIn("  in_progress: 1", self.output)
        self.assertIn("  resolved: 1", self.output)
        self.assertIn("  critical: 1", self.output)
        self.assertIn("  low: 1", self.output)

    def test_queue_and_report_do_not_change_the_file(self):
        before = self.file_text()
        self.use_menu(["7", "8", "0"])
        self.assertEqual(self.file_text(), before)


def event_lines(output):
    """Pick the history lines (they start with an event ID like E001) out of the output."""
    return [line.split(" | ") for line in output if line[:1] == "E" and " | " in line]


class TestHistoryEvents(MenuTestCase):
    def test_full_lifecycle_records_the_exact_event_sequence(self):
        self.use_menu([
            "1", "Wi-Fi down", "Network", "high", "15",   # create T001
            "4", "T001", "Ada",                            # assign
            "5", "T001", "in_progress",                    # start
            "5", "T001", "resolved",                       # resolve
            "6", "T001",                                   # reopen
            "12", "T001", "0",                             # show history
        ])
        lines = event_lines(self.output)
        self.assertEqual([line[2] for line in lines],
                         ["CREATE", "ASSIGN", "START", "RESOLVE", "REOPEN"])
        self.assertEqual([line[4] for line in lines],
                         ["- -> open", "open -> open", "open -> in_progress",
                          "in_progress -> resolved", "resolved -> open"])
        self.assertEqual([line[0] for line in lines],
                         ["E001", "E002", "E003", "E004", "E005"])

    def test_every_event_carries_the_actor_and_the_clock_time(self):
        self.use_menu(["1", "Wi-Fi down", "Network", "low", "1", "12", "T001", "0"],
                      actor="  Zed ")
        (line,) = event_lines(self.output)
        self.assertEqual(line[1], "2026-10-14T10:00:00+00:00")
        self.assertEqual(line[3], "Zed")

    def test_rejected_transition_adds_no_event_and_changes_nothing(self):
        save_data(self.path, make_tickets(), [])  # T001 is open and unassigned
        with open(self.path, "rb") as file:
            before = file.read()
        self.use_menu(["5", "T001", "in_progress", "12", "T001", "0"])
        self.assertIn("Error: Assign the ticket to someone", self.text())
        self.assertIn("No history recorded for T001.", self.output)
        with open(self.path, "rb") as file:
            self.assertEqual(file.read(), before)

    def test_other_rejected_actions_add_no_event(self):
        save_data(self.path, make_tickets(), [])
        self.use_menu([
            "4", "T001", "   ",          # blank staff name
            "4", "T999", "Ada",          # unknown ticket
            "6", "T001",                 # reopen a ticket that is not resolved
            "5", "T001", "banana",       # nonsense status
            "12", "T001", "0",
        ])
        self.assertEqual(self.text().count("Error:"), 4)
        self.assertIn("No history recorded for T001.", self.output)

    def test_actor_prompt_rejects_blank_and_asks_again(self):
        self.use_menu(["", "   ", "Zed", "0"], actor=None)
        self.assertEqual(self.text().count("Error: Actor cannot be blank"), 2)
        self.assertIn("Goodbye.", self.output)

    def test_history_of_unknown_ticket_shows_an_error(self):
        self.use_menu(["12", "T404", "0"])
        self.assertIn("Error: Ticket T404 not found", self.text())

    def test_showing_history_does_not_change_the_file(self):
        save_data(self.path, make_tickets(), [])
        with open(self.path, "rb") as file:
            before = file.read()
        self.use_menu(["12", "T001", "0"])
        with open(self.path, "rb") as file:
            self.assertEqual(file.read(), before)

    def test_two_tickets_keep_separate_histories(self):
        self.use_menu([
            "1", "First", "Network", "low", "1",
            "1", "Second", "Hardware", "low", "1",
            "4", "T002", "Ada",
            "12", "T001", "12", "T002", "0",
        ])
        lines = event_lines(self.output)
        self.assertEqual([line[2] for line in lines], ["CREATE", "CREATE", "ASSIGN"])


class TestDuplicateWarning(MenuTestCase):
    FIRST = ["1", " Wi-Fi   Down ", "Network", "high", "15"]

    def test_matching_title_warns_and_confirming_creates_the_ticket(self):
        self.use_menu(self.FIRST + ["1", "wi-fi down", "Network", "low", "1", "yes", "0"])
        self.assertIn("Warning: similar unresolved ticket(s) already exist: T001.", self.output)
        self.assertEqual([t["id"] for t in load_data(self.path)[0]], ["T001", "T002"])

    def test_declining_creates_neither_a_ticket_nor_an_event(self):
        self.use_menu(self.FIRST + ["1", "wi-fi down", "Network", "low", "1", "no",
                                    "12", "T001", "0"])
        self.assertIn("Cancelled. No ticket was created.", self.output)
        self.assertEqual([t["id"] for t in load_data(self.path)[0]], ["T001"])
        self.assertEqual([line[2] for line in event_lines(self.output)], ["CREATE"])

    def test_confirming_records_exactly_one_more_create_event(self):
        self.use_menu(self.FIRST + ["1", "wi-fi down", "Network", "low", "1", "y",
                                    "12", "T001", "12", "T002", "0"])
        self.assertEqual([line[2] for line in event_lines(self.output)], ["CREATE", "CREATE"])

    def test_unclear_answer_is_asked_again(self):
        self.use_menu(self.FIRST + ["1", "wi-fi down", "Network", "low", "1",
                                    "maybe", "", "no", "0"])
        self.assertEqual(self.text().count("Please answer yes or no."), 2)
        self.assertEqual(len(load_data(self.path)[0]), 1)

    def test_different_category_gives_no_warning(self):
        self.use_menu(self.FIRST + ["1", "wi-fi down", "Hardware", "low", "1", "0"])
        self.assertNotIn("Warning", self.text())
        self.assertEqual(len(load_data(self.path)[0]), 2)

    def test_resolved_ticket_gives_no_warning(self):
        tickets = make_tickets()
        tickets[0]["status"] = "resolved"
        save_data(self.path, tickets, [])
        self.use_menu(["1", "Campus Wi-Fi is down", "Network", "low", "1", "0"])
        self.assertNotIn("Warning", self.text())
        self.assertEqual(len(load_data(self.path)[0]), 3)

    def test_running_out_of_input_at_the_warning_creates_nothing(self):
        self.use_menu(self.FIRST + ["1", "wi-fi down", "Network", "low", "1"])
        self.assertEqual(len(load_data(self.path)[0]), 1)

class TestMenuKeysForTheNewFeatures(MenuTestCase):
    """The new actions must sit on the keys the plan fixes them to."""

    def test_menu_labels_the_new_options(self):
        self.use_menu(["0"])
        for line in ["9. Escalate overdue tickets",
                     "10. Show the SLA attention queue",
                     "11. Show ticket and SLA metrics",
                     "12. Show a ticket's history",
                     "13. Engineering Knowledge Lab"]:
            self.assertIn(line, self.output)

    def test_the_knowledge_lab_is_the_quiz_at_key_13(self):
        # Key 13 runs the quiz, which asks for a participant before anything else.
        self.use_menu(["13"])
        self.assertIn("Participant (A or B): ", self.prompts)
        self.assertNotIn("Escalated in current cycle:", self.text())


class SlaMenuTestCase(MenuTestCase):
    """A saved world with one overdue ticket (T001) and one that is not due (T002)."""

    def setUp(self):
        super().setUp()
        save_data(self.path, [
            make_ticket("T001", "Overdue Wi-Fi", "Network", "high", 15,
                        "critical", "open", due_in_minutes=-30),
            make_ticket("T002", "Laptop later", "Hardware", "low", 1,
                        "low", "open", due_in_minutes=+600),
        ], [])


class TestEscalateMenuOption(SlaMenuTestCase):
    def test_escalating_saves_one_event(self):
        self.use_menu(["9", "0"])
        self.assertIn("Newly escalated: 1", self.output)
        events = self.saved_events()
        self.assertEqual([event["event_type"] for event in events], ["ESCALATE"])
        self.assertEqual(events[0]["ticket_id"], "T001")
        self.assertEqual(events[0]["actor"], "Tester")

    def test_the_escalation_marker_is_saved_on_the_ticket(self):
        self.use_menu(["9", "0"])
        ticket = self.saved_tickets()[0]
        self.assertEqual(ticket["escalation_cycle"], 0)
        self.assertEqual(ticket["escalated_cycle"], 0)

    def test_only_the_overdue_ticket_is_escalated(self):
        self.use_menu(["9", "0"])
        self.assertEqual([event["ticket_id"] for event in self.saved_events()], ["T001"])

    def test_escalating_twice_creates_only_one_event(self):
        self.use_menu(["9", "9", "0"])
        self.assertIn("Newly escalated: 1", self.output)
        self.assertIn("Already escalated in this cycle: 1", self.output)
        self.assertEqual(len(self.saved_events()), 1)

    def test_key_9_is_the_escalation_action_and_not_the_queue(self):
        self.use_menu(["9", "0"])
        self.assertIn("Newly escalated: 1", self.output)
        self.assertNotIn("(overdue tickets first)", self.text())


class TestSlaQueueMenuOption(SlaMenuTestCase):
    def test_key_10_shows_the_queue_with_overdue_tickets_first(self):
        self.use_menu(["10", "0"])
        self.assertIn("SLA attention queue (overdue tickets first):", self.output)
        self.assertIn("1. [OVERDUE] T001", self.text())
        self.assertIn("2. [on time] T002", self.text())

    def test_key_10_does_not_escalate_anything(self):
        self.use_menu(["10", "0"])
        self.assertEqual(self.saved_events(), [])
        self.assertNotIn("Newly escalated:", self.text())

    def test_showing_the_queue_does_not_change_the_file(self):
        with open(self.path, "rb") as file:
            before = file.read()
        self.use_menu(["10", "0"])
        with open(self.path, "rb") as file:
            self.assertEqual(file.read(), before)


class TestMetricsMenuOption(SlaMenuTestCase):
    def test_key_11_shows_the_metrics(self):
        self.use_menu(["11", "0"])
        self.assertIn("Total tickets: 2", self.output)
        self.assertIn("Overdue unresolved: 1", self.output)
        self.assertIn("Escalated in current cycle: 0", self.output)

    def test_key_11_is_not_the_queue_and_escalates_nothing(self):
        self.use_menu(["11", "0"])
        self.assertNotIn("(overdue tickets first)", self.text())
        self.assertNotIn("Newly escalated:", self.text())
        self.assertEqual(self.saved_events(), [])

    def test_metrics_after_escalating_count_the_escalated_ticket(self):
        self.use_menu(["9", "11", "0"])
        self.assertIn("Escalated in current cycle: 1", self.output)


class TestHistorySurvivesARestart(MenuTestCase):
    def test_history_is_still_there_after_exiting_and_starting_again(self):
        self.use_menu(["1", "Wi-Fi down", "Network", "high", "15", "0"])
        self.assertEqual([event["event_type"] for event in self.saved_events()],
                         ["CREATE"])

        self.output.clear()
        self.use_menu(["12", "T001", "0"])
        self.assertNotIn("No history recorded for T001.", self.output)
        self.assertEqual([line[2] for line in event_lines(self.output)], ["CREATE"])

    def test_every_event_survives_a_second_restart(self):
        self.use_menu(["1", "Wi-Fi down", "Network", "high", "15",
                       "4", "T001", "Ada", "0"])
        self.output.clear()
        self.use_menu(["12", "T001", "0"])
        self.assertEqual([line[2] for line in event_lines(self.output)],
                         ["CREATE", "ASSIGN"])

    def test_escalation_and_its_event_survive_a_restart(self):
        # Created at 09:00, so the critical ticket (SLA 60 minutes) is due at 10:00.
        morning = datetime(2026, 10, 14, 9, 0, tzinfo=timezone.utc)
        self.use_menu(["1", "Wi-Fi down", "Network", "high", "15", "0"],
                      clock=lambda: morning)

        # Restart at 11:00: the ticket is overdue, so escalate it, then twice over.
        later = datetime(2026, 10, 14, 11, 0, tzinfo=timezone.utc)
        self.output.clear()
        self.use_menu(["9", "9", "0"], clock=lambda: later)
        self.assertIn("Newly escalated: 1", self.output)
        self.assertIn("Already escalated in this cycle: 1", self.output)

        # Restart once more: history and metrics must now agree with each other.
        self.output.clear()
        self.use_menu(["12", "T001", "11", "0"], clock=lambda: later)
        self.assertEqual([line[2] for line in event_lines(self.output)],
                         ["CREATE", "ESCALATE"])
        self.assertIn("Escalated in current cycle: 1", self.output)


if __name__ == "__main__":
    unittest.main()