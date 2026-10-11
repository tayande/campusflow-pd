import json
import os
import tempfile
import unittest

from campusflow.storage import DEFAULT_PATH, load_tickets, save_tickets


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


class StorageTestCase(unittest.TestCase):
    """Gives every test its own empty temporary folder, deleted afterwards."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = os.path.join(self.folder.name, "tickets.json")

    def write_text(self, text):
        with open(self.path, "w", encoding="utf-8") as file:
            file.write(text)


class TestSaveAndLoad(StorageTestCase):
    def test_round_trip_gives_back_the_same_tickets(self):
        tickets = make_tickets()
        save_tickets(tickets, self.path)
        self.assertEqual(load_tickets(self.path), tickets)

    def test_none_assignee_survives_the_round_trip(self):
        save_tickets(make_tickets(), self.path)
        self.assertIsNone(load_tickets(self.path)[0]["assigned_to"])

    def test_empty_list_round_trip(self):
        save_tickets([], self.path)
        self.assertEqual(load_tickets(self.path), [])

    def test_save_creates_a_missing_folder(self):
        nested = os.path.join(self.folder.name, "data", "tickets.json")
        save_tickets(make_tickets(), nested)
        self.assertTrue(os.path.exists(nested))

    def test_save_replaces_the_old_contents(self):
        save_tickets(make_tickets(), self.path)
        save_tickets([], self.path)
        self.assertEqual(load_tickets(self.path), [])

    def test_save_leaves_no_side_file_behind(self):
        save_tickets(make_tickets(), self.path)
        self.assertEqual(os.listdir(self.folder.name), ["tickets.json"])

    def test_default_path_points_to_data_tickets_json(self):
        self.assertTrue(DEFAULT_PATH.endswith(os.path.join("data", "tickets.json")))


class TestLoadProblems(StorageTestCase):
    def test_missing_file_gives_an_empty_list(self):
        self.assertEqual(load_tickets(self.path), [])

    def test_empty_file_is_rejected(self):
        self.write_text("")
        with self.assertRaises(ValueError):
            load_tickets(self.path)

    def test_malformed_json_is_rejected(self):
        self.write_text('[{"id": "T001", ')
        with self.assertRaises(ValueError):
            load_tickets(self.path)

    def test_rejected_file_is_left_untouched(self):
        self.write_text("not json at all")
        with self.assertRaises(ValueError):
            load_tickets(self.path)
        with open(self.path, encoding="utf-8") as file:
            self.assertEqual(file.read(), "not json at all")

    def test_json_that_is_not_a_list_is_rejected(self):
        self.write_text('{"id": "T001"}')
        with self.assertRaises(ValueError):
            load_tickets(self.path)

    def test_item_that_is_not_a_ticket_is_rejected(self):
        self.write_text('["T001"]')
        with self.assertRaises(ValueError):
            load_tickets(self.path)

    def test_missing_key_is_rejected(self):
        ticket = make_tickets()[0]
        del ticket["status"]
        self.write_text(json.dumps([ticket]))
        with self.assertRaises(ValueError):
            load_tickets(self.path)

    def test_bad_values_are_rejected(self):
        bad_changes = [
            ("id", "X001"), ("id", "T"), ("id", 5),
            ("category", "Plumbing"), ("urgency", "urgent"),
            ("priority", "extreme"), ("status", "done"),
            ("affected_users", 0), ("affected_users", "5"),
            ("affected_users", True), ("affected_users", 2.5),
        ]
        for key, value in bad_changes:
            with self.subTest(key=key, value=value):
                ticket = make_tickets()[0]
                ticket[key] = value
                self.write_text(json.dumps([ticket]))
                with self.assertRaises(ValueError):
                    load_tickets(self.path)


if __name__ == "__main__":
    unittest.main()