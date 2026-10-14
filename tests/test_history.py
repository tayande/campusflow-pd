import unittest
from datetime import datetime, timezone

from campusflow.history import (
    EVENT_TYPES,
    clean_actor,
    format_event,
    get_history,
    record_event,
)

NOW = datetime(2026, 10, 14, 10, 0, tzinfo=timezone.utc)


class TestRecordEvent(unittest.TestCase):
    def test_event_has_all_eight_fields(self):
        events = []
        event = record_event(events, "T001", "CREATE", "Peace", NOW, None, "open", {"priority": "high"})
        self.assertEqual(
            sorted(event),
            sorted(["event_id", "ticket_id", "event_type", "actor",
                    "timestamp", "before_status", "after_status", "details"]),
        )
        self.assertEqual(event["timestamp"], "2026-10-14T10:00:00+00:00")
        self.assertEqual(event["details"], {"priority": "high"})
        self.assertEqual(events, [event])

    def test_ids_count_up_from_e001(self):
        events = []
        ids = [record_event(events, "T001", "ASSIGN", "Peace", NOW, "open", "open")["event_id"]
               for _ in range(3)]
        self.assertEqual(ids, ["E001", "E002", "E003"])

    def test_next_id_uses_highest_number_not_the_count(self):
        events = [{"event_id": "E009"}, {"event_id": "E002"}]  # highest is not last
        event = record_event(events, "T001", "START", "Peace", NOW, "open", "in_progress")
        self.assertEqual(event["event_id"], "E010")

    def test_bad_event_type_is_rejected_and_events_unchanged(self):
        events = []
        with self.assertRaises(ValueError):
            record_event(events, "T001", "DELETE", "Peace", NOW, "open", "open")
        self.assertEqual(events, [])

    def test_blank_or_non_text_actor_is_rejected_and_events_unchanged(self):
        events = []
        for bad in ["", "   ", None, 5]:
            with self.assertRaises(ValueError):
                record_event(events, "T001", "CREATE", bad, NOW, None, "open")
        self.assertEqual(events, [])

    def test_naive_time_is_rejected_and_events_unchanged(self):
        events = []
        with self.assertRaises(ValueError):
            record_event(events, "T001", "CREATE", "Peace", datetime(2026, 10, 14, 10, 0), None, "open")
        self.assertEqual(events, [])

    def test_details_default_is_a_fresh_dict_each_time(self):
        events = []
        first = record_event(events, "T001", "START", "Peace", NOW, "open", "in_progress")
        first["details"]["x"] = 1
        second = record_event(events, "T001", "RESOLVE", "Peace", NOW, "in_progress", "resolved")
        self.assertEqual(second["details"], {})

    def test_all_six_event_types_exist(self):
        self.assertEqual(set(EVENT_TYPES),
                         {"CREATE", "ASSIGN", "START", "RESOLVE", "REOPEN", "ESCALATE"})

    def test_actor_is_stored_without_outer_spaces(self):
        events = []
        event = record_event(events, "T001", "CREATE", "  Peace ", NOW, None, "open")
        self.assertEqual(event["actor"], "Peace")


class TestCleanActor(unittest.TestCase):
    def test_strips_spaces(self):
        self.assertEqual(clean_actor("  Ada "), "Ada")

    def test_blank_and_non_text_are_rejected(self):
        for bad in ["", "   ", None, 7]:
            with self.assertRaises(ValueError):
                clean_actor(bad)


def make_event(event_id, ticket_id, timestamp, event_type="ASSIGN"):
    """Build a bare event by hand, so these tests do not depend on record_event."""
    return {"event_id": event_id, "ticket_id": ticket_id, "event_type": event_type,
            "actor": "Peace", "timestamp": timestamp,
            "before_status": "open", "after_status": "open", "details": {}}


class TestGetHistory(unittest.TestCase):
    def test_events_come_back_in_time_order_not_insertion_order(self):
        later = make_event("E001", "T001", "2026-10-14T11:00:00+00:00")
        earlier = make_event("E002", "T001", "2026-10-14T10:00:00+00:00")
        self.assertEqual(get_history([later, earlier], "T001"), [earlier, later])

    def test_same_timestamp_is_broken_by_numeric_event_id(self):
        same = "2026-10-14T10:00:00+00:00"
        e1000 = make_event("E1000", "T001", same)
        e999 = make_event("E999", "T001", same)
        # As text "E1000" sorts before "E999"; as numbers 999 comes first.
        self.assertEqual(get_history([e1000, e999], "T001"), [e999, e1000])

    def test_time_order_uses_real_instants_not_text(self):
        # 10:00+01:00 is 09:00 UTC, so it is EARLIER than 09:30+00:00,
        # even though its text sorts later.
        earlier = make_event("E002", "T001", "2026-10-14T10:00:00+01:00")
        later = make_event("E001", "T001", "2026-10-14T09:30:00+00:00")
        self.assertEqual(get_history([later, earlier], "T001"), [earlier, later])

    def test_other_tickets_are_left_out(self):
        mine = make_event("E001", "T001", "2026-10-14T10:00:00+00:00")
        other = make_event("E002", "T002", "2026-10-14T10:00:00+00:00")
        self.assertEqual(get_history([mine, other], "T001"), [mine])

    def test_no_events_gives_an_empty_list(self):
        self.assertEqual(get_history([], "T001"), [])
        self.assertEqual(get_history([make_event("E001", "T002", "2026-10-14T10:00:00+00:00")], "T001"), [])

    def test_get_history_does_not_change_or_reuse_the_events_list(self):
        later = make_event("E001", "T001", "2026-10-14T11:00:00+00:00")
        earlier = make_event("E002", "T001", "2026-10-14T10:00:00+00:00")
        events = [later, earlier]
        result = get_history(events, "T001")
        self.assertEqual(events, [later, earlier])  # order untouched
        self.assertIsNot(result, events)

    def test_ticket_id_typed_in_lowercase_still_matches(self):
        mine = make_event("E001", "T001", "2026-10-14T10:00:00+00:00")
        self.assertEqual(get_history([mine], " t001 "), [mine])


class TestFormatEvent(unittest.TestCase):
    def test_line_shows_time_type_actor_statuses_and_details(self):
        event = make_event("E003", "T001", "2026-10-14T10:00:00+00:00", "ASSIGN")
        event["details"] = {"assigned_to": "Ada"}
        line = format_event(event)
        for part in ["E003", "2026-10-14T10:00:00+00:00", "ASSIGN", "Peace",
                     "open -> open", "assigned_to=Ada"]:
            self.assertIn(part, line)

    def test_create_event_shows_a_dash_for_the_missing_before_status(self):
        event = make_event("E001", "T001", "2026-10-14T10:00:00+00:00", "CREATE")
        event["before_status"] = None
        event["after_status"] = "open"
        self.assertIn("- -> open", format_event(event))


if __name__ == "__main__":
    unittest.main()
