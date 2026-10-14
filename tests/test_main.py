import json
import os
import tempfile
import unittest
from datetime import datetime, timezone

from campusflow.main import run
from campusflow.storage import load_tickets, save_tickets


FIXED_TIME = datetime(2026, 10, 14, 10, 0, tzinfo=timezone.utc)


def fixed_clock():
    """A clock that always says the same time, so tests never depend on the real one."""
    return FIXED_TIME


def make_tickets():
    """Return a fresh list of two tickets, so tests never share data."""
    return [
        {"id": "T001", "title": "Campus Wi-Fi is down", "category": "Network",
         "urgency": "high", "affected_users": 15, "priority": "critical",
         "status": "open", "assigned_to": None},
        {"id": "T002", "title": "Laptop will not start", "category": "Hardware",
         "urgency": "low", "affected_users": 1, "priority": "low",
         "status": "in_progress", "assigned_to": "Sam"},
    ]


class MenuTestCase(unittest.TestCase):
    """Runs the menu with typed answers and a temporary data file."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = os.path.join(self.folder.name, "tickets.json")
        self.output = []

    def use_menu(self, answers, actor="Tester", clock=fixed_clock):
        """Run the menu with these answers; return its exit code.

        The menu first asks for the operator's name, so it is typed here
        automatically. Pass actor=None to type it yourself in `answers`.
        """
        remaining = list(answers) if actor is None else [actor] + list(answers)

        def fake_ask(prompt):
            if not remaining:
                raise EOFError  # the user ran out of input
            return remaining.pop(0)

        return run(self.path, ask=fake_ask, say=self.output.append, clock=clock)

    def text(self):
        return "\n".join(self.output)


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
        saved = load_tickets(self.path)
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
        saved = load_tickets(self.path)
        self.assertEqual(saved[0]["affected_users"], 3)
        self.assertEqual(saved[0]["priority"], "medium")

    def test_new_ticket_continues_after_existing_ones(self):
        save_tickets(make_tickets(), self.path)
        self.use_menu(["1", "Projector", "Other", "low", "1", "0"])
        ids = [t["id"] for t in load_tickets(self.path)]
        self.assertEqual(ids, ["T001", "T002", "T003"])

    def test_two_tickets_in_one_session_get_different_ids(self):
        self.use_menu(["1", "A", "Other", "low", "1",
                       "1", "B", "Other", "low", "1", "0"])
        ids = [t["id"] for t in load_tickets(self.path)]
        self.assertEqual(ids, ["T001", "T002"])

    def test_leaving_in_the_middle_of_create_saves_nothing(self):
        self.use_menu(["1", "Half a ticket", "Other"])
        self.assertFalse(os.path.exists(self.path))


class TestListAndView(MenuTestCase):
    def test_list_with_no_tickets(self):
        self.use_menu(["2", "0"])
        self.assertIn("No tickets yet.", self.output)

    def test_list_shows_every_saved_ticket(self):
        save_tickets(make_tickets(), self.path)
        self.use_menu(["2", "0"])
        self.assertIn("T001 | Campus Wi-Fi is down | Network | critical | open | unassigned",
                      self.output)
        self.assertIn("T002 | Laptop will not start | Hardware | low | in_progress | Sam",
                      self.output)

    def test_view_shows_all_details(self):
        save_tickets(make_tickets(), self.path)
        self.use_menu(["3", " t002 ", "0"])
        self.assertIn("Title:          Laptop will not start", self.output)
        self.assertIn("Assigned to:    Sam", self.output)
        self.assertIn("Status:         in_progress", self.output)

    def test_view_unknown_ticket_shows_error_and_keeps_going(self):
        save_tickets(make_tickets(), self.path)
        self.use_menu(["3", "T999", "0"])
        self.assertIn("Error: Ticket T999 not found", self.output)
        self.assertIn("Goodbye.", self.output)

    def test_list_does_not_change_the_file(self):
        save_tickets(make_tickets(), self.path)
        with open(self.path, encoding="utf-8") as file:
            before = file.read()
        self.use_menu(["2", "3", "T001", "0"])
        with open(self.path, encoding="utf-8") as file:
            self.assertEqual(file.read(), before)


def make_workflow_tickets():
    """Tickets in every state, for the workflow menu options."""
    def ticket(number, priority, status, assigned_to=None):
        return {"id": f"T{number:03d}", "title": f"Problem {number}",
                "category": "Other", "urgency": "low", "affected_users": 1,
                "priority": priority, "status": status, "assigned_to": assigned_to}
    return [
        ticket(1, "low", "open"),
        ticket(2, "critical", "open", "Sam"),
        ticket(3, "high", "in_progress", "Ada"),
        ticket(4, "medium", "resolved", "Kim"),
    ]


class WorkflowMenuTestCase(MenuTestCase):
    def setUp(self):
        super().setUp()
        save_tickets(make_workflow_tickets(), self.path)

    def file_text(self):
        with open(self.path, encoding="utf-8") as file:
            return file.read()

    def saved(self, ticket_id):
        for ticket in load_tickets(self.path):
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
        save_tickets([], self.path)
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
        save_tickets(make_tickets(), self.path)  # T001 is open and unassigned
        with open(self.path, "rb") as file:
            before = file.read()
        self.use_menu(["5", "T001", "in_progress", "12", "T001", "0"])
        self.assertIn("Error: Assign the ticket to someone", self.text())
        self.assertIn("No history recorded for T001.", self.output)
        with open(self.path, "rb") as file:
            self.assertEqual(file.read(), before)

    def test_other_rejected_actions_add_no_event(self):
        save_tickets(make_tickets(), self.path)
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
        save_tickets(make_tickets(), self.path)
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


if __name__ == "__main__":
    unittest.main()