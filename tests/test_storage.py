import json
import os
import tempfile
import unittest

from datetime import datetime, timezone

from campusflow.history import record_event
from campusflow.storage import (DEFAULT_PATH, load_data, load_tickets, save_data,
                                save_tickets)
from campusflow.tickets import create_ticket


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


# ---------------------------------------------------------------------------
# Version 2 file: tickets and events
# ---------------------------------------------------------------------------

START = datetime(2026, 10, 14, 10, 0, tzinfo=timezone.utc)


def make_data():
    """Return a fresh (tickets, events) pair made the normal way, at a fixed time."""
    tickets = []
    create_ticket(tickets, "Wi-Fi down", "Network", "high", 15, now=START)
    create_ticket(tickets, "Mouse broken", "Hardware", "low", 1, now=START)
    events = []
    record_event(events, "T001", "CREATE", "Sam", START, None, "open", {"priority": "critical"})
    record_event(events, "T002", "CREATE", "Sam", START, None, "open", {"priority": "low"})
    return tickets, events


class TestSaveAndLoadData(StorageTestCase):
    def test_round_trip_gives_back_the_same_data(self):
        tickets, events = make_data()
        save_data(self.path, tickets, events)
        self.assertEqual(load_data(self.path), (tickets, events))

    def test_file_holds_the_version_number(self):
        save_data(self.path, *make_data())
        with open(self.path, encoding="utf-8") as file:
            data = json.load(file)
        self.assertEqual(data["schema_version"], 2)
        self.assertEqual(sorted(data), ["events", "schema_version", "tickets"])

    def test_missing_file_means_a_fresh_start(self):
        self.assertEqual(load_data(self.path), ([], []))

    def test_save_creates_a_missing_folder(self):
        nested = os.path.join(self.folder.name, "data", "tickets.json")
        save_data(nested, *make_data())
        self.assertTrue(os.path.exists(nested))

    def test_save_leaves_no_temp_file_behind(self):
        save_data(self.path, *make_data())
        self.assertFalse(os.path.exists(self.path + ".tmp"))

    def test_none_values_survive(self):
        tickets, events = make_data()
        save_data(self.path, tickets, events)
        loaded_tickets, loaded_events = load_data(self.path)
        self.assertIsNone(loaded_tickets[0]["assigned_to"])
        self.assertIsNone(loaded_tickets[0]["escalated_cycle"])
        self.assertIsNone(loaded_events[0]["before_status"])

    def test_a_new_ticket_after_reload_gets_the_next_id(self):
        tickets, events = make_data()
        save_data(self.path, tickets, events)
        loaded, _ = load_data(self.path)
        new = create_ticket(loaded, "Projector", "Other", "low", 1, now=START)
        self.assertEqual(new["id"], "T003")
        self.assertEqual(len({t["id"] for t in loaded}), 3)


class TestLoadDataRejectsBadFiles(StorageTestCase):
    def good_data(self):
        tickets, events = make_data()
        return {"schema_version": 2, "tickets": tickets, "events": events}

    def write_json(self, data):
        self.write_text(json.dumps(data))

    def assert_rejected(self, data):
        self.write_json(data)
        with self.assertRaises(ValueError):
            load_data(self.path)

    def test_corrupted_json(self):
        self.write_text("{ not json")
        with self.assertRaises(ValueError):
            load_data(self.path)

    def test_empty_file(self):
        self.write_text("")
        with self.assertRaises(ValueError):
            load_data(self.path)

    def test_old_list_format_is_refused_and_left_alone(self):
        save_tickets(make_tickets(), self.path)
        with open(self.path, encoding="utf-8") as file:
            before = file.read()
        with self.assertRaises(ValueError):
            load_data(self.path)
        with open(self.path, encoding="utf-8") as file:
            self.assertEqual(file.read(), before)

    def test_wrong_or_missing_version(self):
        for version in [1, 3, "2", True, None]:
            with self.subTest(version=version):
                data = self.good_data()
                data["schema_version"] = version
                self.assert_rejected(data)
        data = self.good_data()
        del data["schema_version"]
        self.assert_rejected(data)

    def test_missing_tickets_or_events_part(self):
        for part in ["tickets", "events"]:
            with self.subTest(part=part):
                data = self.good_data()
                del data[part]
                self.assert_rejected(data)

    def test_parts_must_be_lists(self):
        for part in ["tickets", "events"]:
            with self.subTest(part=part):
                data = self.good_data()
                data[part] = {}
                self.assert_rejected(data)

    def test_ticket_time_problems(self):
        for field, bad in [("created_at", "2026-10-14T10:00:00"),   # no timezone
                           ("due_at", "tomorrow"),
                           ("updated_at", 12345),
                           ("due_at", None)]:
            with self.subTest(field=field, bad=bad):
                data = self.good_data()
                data["tickets"][0][field] = bad
                self.assert_rejected(data)

    def test_ticket_cycle_problems(self):
        for field, bad in [("escalation_cycle", -1), ("escalation_cycle", True),
                           ("escalation_cycle", "0"), ("escalated_cycle", 1.5),
                           ("escalated_cycle", False)]:
            with self.subTest(field=field, bad=bad):
                data = self.good_data()
                data["tickets"][0][field] = bad
                self.assert_rejected(data)

    def test_missing_new_ticket_field(self):
        for field in ["created_at", "updated_at", "due_at",
                      "escalation_cycle", "escalated_cycle"]:
            with self.subTest(field=field):
                data = self.good_data()
                del data["tickets"][0][field]
                self.assert_rejected(data)

    def test_old_ticket_rules_still_apply(self):
        data = self.good_data()
        data["tickets"][0]["priority"] = "urgent"
        self.assert_rejected(data)

    def test_duplicate_ticket_ids(self):
        data = self.good_data()
        data["tickets"][1]["id"] = "T001"
        self.assert_rejected(data)

    def test_duplicate_event_ids(self):
        data = self.good_data()
        data["events"][1]["event_id"] = "E001"
        self.assert_rejected(data)

    def test_event_for_a_missing_ticket(self):
        data = self.good_data()
        data["events"][0]["ticket_id"] = "T099"
        self.assert_rejected(data)

    def test_event_field_problems(self):
        for field, bad in [("event_type", "DELETE"), ("actor", "  "), ("actor", None),
                           ("timestamp", "2026-10-14T10:00:00"), ("after_status", "done"),
                           ("before_status", "done"), ("details", "text"),
                           ("event_id", "X001")]:
            with self.subTest(field=field, bad=bad):
                data = self.good_data()
                data["events"][0][field] = bad
                self.assert_rejected(data)

    def test_event_that_is_not_an_object(self):
        data = self.good_data()
        data["events"][0] = "event"
        self.assert_rejected(data)


class TestSaveDataIsSafe(StorageTestCase):
    def test_invalid_data_is_not_written_and_the_good_file_survives(self):
        tickets, events = make_data()
        save_data(self.path, tickets, events)
        with open(self.path, encoding="utf-8") as file:
            good_text = file.read()
        bad_tickets = [dict(tickets[0], due_at="tomorrow")]
        with self.assertRaises(ValueError):
            save_data(self.path, bad_tickets, [])
        with open(self.path, encoding="utf-8") as file:
            self.assertEqual(file.read(), good_text)
        self.assertEqual(load_data(self.path), (tickets, events))
        self.assertFalse(os.path.exists(self.path + ".tmp"))

    def test_empty_defaults_never_replace_a_damaged_file(self):
        self.write_text("{ not json")
        with self.assertRaises(ValueError):
            load_data(self.path)
        with open(self.path, encoding="utf-8") as file:
            self.assertEqual(file.read(), "{ not json")


if __name__ == "__main__":
    unittest.main()
