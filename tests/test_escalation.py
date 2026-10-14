import unittest
from datetime import datetime, timedelta, timezone

from campusflow.history import record_event
from campusflow.sla import escalate_overdue
from campusflow.tickets import create_ticket
from campusflow.timeutil import to_iso
from campusflow.workflow import assign_ticket, change_status, reopen_ticket

START = datetime(2026, 10, 14, 10, 0, tzinfo=timezone.utc)


def at(minutes):
    return START + timedelta(minutes=minutes)


def make_world():
    """A critical ticket (due +60) and a low ticket (due +2880), both created at START."""
    tickets = []
    create_ticket(tickets, "Wi-Fi down", "Network", "high", 15, now=START)     # T001 critical
    create_ticket(tickets, "Mouse broken", "Hardware", "low", 1, now=START)    # T002 low
    return tickets, []


def escalations(events):
    return [e for e in events if e["event_type"] == "ESCALATE"]


class TestEscalateOverdue(unittest.TestCase):
    def test_overdue_ticket_gets_one_event(self):
        tickets, events = make_world()
        result = escalate_overdue(tickets, events, at(61), "Peace")
        self.assertEqual(result, {"newly_escalated": 1, "already_escalated": 0})
        self.assertEqual(len(escalations(events)), 1)
        event = events[0]
        self.assertEqual(event["ticket_id"], "T001")
        self.assertEqual(event["actor"], "Peace")
        self.assertEqual(event["timestamp"], to_iso(at(61)))
        self.assertEqual(event["details"], {"cycle": 0, "due_at": tickets[0]["due_at"]})

    def test_running_it_twice_adds_no_second_event(self):
        tickets, events = make_world()
        escalate_overdue(tickets, events, at(61), "Peace")
        again = escalate_overdue(tickets, events, at(70), "Peace")
        self.assertEqual(again, {"newly_escalated": 0, "already_escalated": 1})
        self.assertEqual(len(events), 1)

    def test_exactly_on_the_deadline_is_not_escalated(self):
        tickets, events = make_world()
        result = escalate_overdue(tickets, events, at(60), "Peace")
        self.assertEqual(result, {"newly_escalated": 0, "already_escalated": 0})
        self.assertEqual(events, [])

    def test_resolved_tickets_are_skipped(self):
        tickets, events = make_world()
        tickets[0]["status"] = "resolved"
        escalate_overdue(tickets, events, at(500), "Peace")
        self.assertEqual(events, [])

    def test_only_overdue_tickets_are_escalated(self):
        tickets, events = make_world()
        escalate_overdue(tickets, events, at(61), "Peace")
        self.assertEqual([e["ticket_id"] for e in events], ["T001"])
        escalate_overdue(tickets, events, at(2881), "Peace")
        self.assertEqual([e["ticket_id"] for e in events], ["T001", "T002"])

    def test_escalation_changes_only_the_marker_and_updated_at(self):
        tickets, events = make_world()
        before = dict(tickets[0])
        escalate_overdue(tickets, events, at(61), "Peace")
        after = tickets[0]
        for key in ["status", "priority", "assigned_to", "due_at", "created_at",
                    "escalation_cycle"]:
            self.assertEqual(after[key], before[key], key)
        self.assertEqual(after["escalated_cycle"], 0)
        self.assertEqual(after["updated_at"], to_iso(at(61)))

    def test_a_reopened_ticket_can_be_escalated_again(self):
        tickets, events = make_world()
        escalate_overdue(tickets, events, at(61), "Peace")
        assign_ticket(tickets, "T001", "Sam", now=at(62))
        change_status(tickets, "T001", "in_progress", now=at(63))
        change_status(tickets, "T001", "resolved", now=at(64))
        reopen_ticket(tickets, "T001", now=at(100))       # new cycle, due at +160
        self.assertEqual(
            escalate_overdue(tickets, events, at(160), "Peace"),
            {"newly_escalated": 0, "already_escalated": 0},   # not overdue yet
        )
        result = escalate_overdue(tickets, events, at(161), "Peace")
        self.assertEqual(result, {"newly_escalated": 1, "already_escalated": 0})
        cycles = [e["details"]["cycle"] for e in escalations(events)]
        self.assertEqual(cycles, [0, 1])
        again = escalate_overdue(tickets, events, at(170), "Peace")
        self.assertEqual(again["newly_escalated"], 0)

    def test_blank_actor_changes_nothing(self):
        tickets, events = make_world()
        before = [dict(t) for t in tickets]
        for actor in ["", "   ", None, 5]:
            with self.subTest(actor=actor):
                with self.assertRaises(ValueError):
                    escalate_overdue(tickets, events, at(61), actor)
        self.assertEqual(tickets, before)
        self.assertEqual(events, [])

    def test_blank_actor_is_refused_even_when_nothing_is_overdue(self):
        tickets, events = make_world()
        with self.assertRaises(ValueError):
            escalate_overdue(tickets, events, at(1), "")

    def test_naive_now_changes_nothing(self):
        tickets, events = make_world()
        before = [dict(t) for t in tickets]
        with self.assertRaises(ValueError):
            escalate_overdue(tickets, events, datetime(2026, 10, 14, 12, 0), "Peace")
        self.assertEqual(tickets, before)
        self.assertEqual(events, [])

    def test_existing_events_are_not_touched(self):
        tickets, events = make_world()
        record_event(events, "T001", "CREATE", "Sam", START, None, "open")
        first = dict(events[0])
        escalate_overdue(tickets, events, at(61), "Peace")
        self.assertEqual(events[0], first)
        self.assertEqual([e["event_id"] for e in events], ["E001", "E002"])

    def test_no_tickets_gives_zero_counts(self):
        self.assertEqual(escalate_overdue([], [], at(1), "Peace"),
                         {"newly_escalated": 0, "already_escalated": 0})


if __name__ == "__main__":
    unittest.main()
