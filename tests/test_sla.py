import unittest
from datetime import datetime, timedelta, timezone

from campusflow.sla import SLA_MINUTES, calculate_due_at, is_overdue
from campusflow.tickets import create_ticket
from campusflow.timeutil import parse_iso, to_iso, utc_now
from campusflow.workflow import assign_ticket, change_status, reopen_ticket

# A fixed clock: tests never read the real time.
START = datetime(2026, 10, 14, 10, 0, tzinfo=timezone.utc)


def minutes_later(minutes):
    return START + timedelta(minutes=minutes)


def new_ticket(urgency="high", users=15, now=START):
    """Create one ticket at the fixed start time and return (list, ticket)."""
    tickets = []
    ticket = create_ticket(tickets, "Wi-Fi down", "Network", urgency, users, now=now)
    return tickets, ticket


class TestTimeHelpers(unittest.TestCase):
    def test_to_iso_writes_utc_with_offset(self):
        self.assertEqual(to_iso(START), "2026-10-14T10:00:00+00:00")

    def test_to_iso_converts_other_zones_to_utc(self):
        lagos = datetime(2026, 10, 14, 11, 0, tzinfo=timezone(timedelta(hours=1)))
        self.assertEqual(to_iso(lagos), "2026-10-14T10:00:00+00:00")

    def test_round_trip(self):
        self.assertEqual(parse_iso(to_iso(START)), START)

    def test_naive_time_is_rejected(self):
        with self.assertRaises(ValueError):
            to_iso(datetime(2026, 10, 14, 10, 0))

    def test_text_without_a_timezone_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_iso("2026-10-14T10:00:00")

    def test_bad_text_and_non_text_are_rejected(self):
        for bad in ["yesterday", "", None, 12345]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    parse_iso(bad)

    def test_utc_now_is_aware(self):
        self.assertEqual(utc_now().utcoffset(), timedelta(0))


class TestCalculateDueAt(unittest.TestCase):
    def test_minutes_for_every_priority(self):
        for priority, minutes in [("critical", 60), ("high", 240),
                                  ("medium", 1440), ("low", 2880)]:
            with self.subTest(priority=priority):
                self.assertEqual(calculate_due_at(priority, START), minutes_later(minutes))

    def test_table_matches_the_brief(self):
        self.assertEqual(SLA_MINUTES, {"critical": 60, "high": 240, "medium": 1440, "low": 2880})

    def test_unknown_priority_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_due_at("urgent", START)

    def test_naive_start_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_due_at("low", datetime(2026, 10, 14, 10, 0))


class TestIsOverdue(unittest.TestCase):
    def test_critical_at_exactly_60_minutes_is_not_overdue(self):
        _, ticket = new_ticket()
        self.assertEqual(ticket["priority"], "critical")
        self.assertFalse(is_overdue(ticket, minutes_later(60)))

    def test_critical_at_61_minutes_is_overdue(self):
        _, ticket = new_ticket()
        self.assertTrue(is_overdue(ticket, minutes_later(61)))

    def test_one_second_after_the_deadline_is_overdue(self):
        _, ticket = new_ticket()
        self.assertTrue(is_overdue(ticket, minutes_later(60) + timedelta(seconds=1)))

    def test_before_the_deadline_is_not_overdue(self):
        _, ticket = new_ticket()
        self.assertFalse(is_overdue(ticket, minutes_later(10)))

    def test_boundary_for_every_priority(self):
        cases = [("high", 10, 60), ("high", 1, 240), ("medium", 1, 1440), ("low", 1, 2880)]
        for urgency, users, minutes in cases:
            with self.subTest(minutes=minutes):
                _, ticket = new_ticket(urgency, users)
                due = parse_iso(ticket["due_at"])
                self.assertEqual(due, minutes_later(minutes))
                self.assertFalse(is_overdue(ticket, due))
                self.assertTrue(is_overdue(ticket, due + timedelta(minutes=1)))

    def test_resolved_ticket_is_never_overdue(self):
        _, ticket = new_ticket()
        ticket["status"] = "resolved"
        self.assertFalse(is_overdue(ticket, minutes_later(10_000)))

    def test_in_progress_ticket_can_be_overdue(self):
        _, ticket = new_ticket()
        ticket["status"] = "in_progress"
        self.assertTrue(is_overdue(ticket, minutes_later(61)))

    def test_naive_now_is_rejected(self):
        _, ticket = new_ticket()
        with self.assertRaises(ValueError):
            is_overdue(ticket, datetime(2026, 10, 14, 12, 0))


class TestNewTicketFields(unittest.TestCase):
    def test_new_ticket_has_the_time_fields(self):
        _, ticket = new_ticket()
        self.assertEqual(ticket["created_at"], "2026-10-14T10:00:00+00:00")
        self.assertEqual(ticket["updated_at"], ticket["created_at"])
        self.assertEqual(ticket["due_at"], "2026-10-14T11:00:00+00:00")
        self.assertEqual(ticket["escalation_cycle"], 0)
        self.assertIsNone(ticket["escalated_cycle"])

    def test_original_fields_are_unchanged(self):
        _, ticket = new_ticket()
        self.assertEqual(ticket["id"], "T001")
        self.assertEqual(ticket["status"], "open")
        self.assertIsNone(ticket["assigned_to"])

    def test_naive_now_creates_nothing(self):
        tickets = []
        with self.assertRaises(ValueError):
            create_ticket(tickets, "Wi-Fi down", "Network", "high", 15,
                          now=datetime(2026, 10, 14, 10, 0))
        self.assertEqual(tickets, [])

    def test_a_bad_input_still_creates_nothing(self):
        tickets = []
        with self.assertRaises(ValueError):
            create_ticket(tickets, "  ", "Network", "high", 15, now=START)
        self.assertEqual(tickets, [])


class TestUpdatedAt(unittest.TestCase):
    def test_assign_and_status_change_set_updated_at(self):
        tickets, ticket = new_ticket()
        assign_ticket(tickets, "T001", "Sam", now=minutes_later(5))
        self.assertEqual(ticket["updated_at"], to_iso(minutes_later(5)))
        change_status(tickets, "T001", "in_progress", now=minutes_later(10))
        self.assertEqual(ticket["updated_at"], to_iso(minutes_later(10)))
        self.assertEqual(ticket["created_at"], "2026-10-14T10:00:00+00:00")

    def test_a_rejected_change_leaves_updated_at_alone(self):
        tickets, ticket = new_ticket()
        before = dict(ticket)
        with self.assertRaises(ValueError):
            change_status(tickets, "T001", "resolved", now=minutes_later(5))
        self.assertEqual(ticket, before)


class TestReopenStartsANewCycle(unittest.TestCase):
    def resolved_ticket(self):
        tickets, ticket = new_ticket()
        assign_ticket(tickets, "T001", "Sam", now=minutes_later(5))
        change_status(tickets, "T001", "in_progress", now=minutes_later(10))
        change_status(tickets, "T001", "resolved", now=minutes_later(20))
        return tickets, ticket

    def test_reopen_gives_a_later_deadline(self):
        tickets, ticket = self.resolved_ticket()
        old_due = ticket["due_at"]
        reopen_ticket(tickets, "T001", now=minutes_later(300))
        self.assertNotEqual(ticket["due_at"], old_due)
        self.assertEqual(parse_iso(ticket["due_at"]), minutes_later(360))

    def test_reopen_keeps_created_at_and_the_assignee(self):
        tickets, ticket = self.resolved_ticket()
        reopen_ticket(tickets, "T001", now=minutes_later(300))
        self.assertEqual(ticket["created_at"], "2026-10-14T10:00:00+00:00")
        self.assertEqual(ticket["assigned_to"], "Sam")
        self.assertEqual(ticket["status"], "open")
        self.assertEqual(ticket["updated_at"], to_iso(minutes_later(300)))

    def test_reopen_moves_to_the_next_cycle(self):
        tickets, ticket = self.resolved_ticket()
        reopen_ticket(tickets, "T001", now=minutes_later(300))
        self.assertEqual(ticket["escalation_cycle"], 1)

    def test_reopened_ticket_is_overdue_by_the_new_deadline(self):
        tickets, ticket = self.resolved_ticket()
        reopen_ticket(tickets, "T001", now=minutes_later(300))
        self.assertFalse(is_overdue(ticket, minutes_later(360)))
        self.assertTrue(is_overdue(ticket, minutes_later(361)))

    def test_reopening_an_unresolved_ticket_changes_nothing(self):
        tickets, ticket = new_ticket()
        before = dict(ticket)
        with self.assertRaises(ValueError):
            reopen_ticket(tickets, "T001", now=minutes_later(300))
        self.assertEqual(ticket, before)

    def test_naive_time_changes_nothing(self):
        tickets, ticket = self.resolved_ticket()
        before = dict(ticket)
        with self.assertRaises(ValueError):
            reopen_ticket(tickets, "T001", now=datetime(2026, 10, 14, 15, 0))
        self.assertEqual(ticket, before)


if __name__ == "__main__":
    unittest.main()
