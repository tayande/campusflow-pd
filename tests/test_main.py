import json
import os
import tempfile
import unittest

from campusflow.main import run
from campusflow.storage import load_tickets, save_tickets


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

    def use_menu(self, answers):
        """Run the menu with these answers; return its exit code."""
        remaining = list(answers)

        def fake_ask(prompt):
            if not remaining:
                raise EOFError  # the user ran out of input
            return remaining.pop(0)

        return run(self.path, ask=fake_ask, say=self.output.append)

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


if __name__ == "__main__":
    unittest.main()