import copy
import unittest
from datetime import datetime, timedelta, timezone

from campusflow.reports import (
    build_metrics,
    build_report,
    format_sla_ticket,
    get_sla_attention_queue,
)
from campusflow.workflow import get_work_queue

NOW = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)


def iso(minutes_from_now):
    """A timestamp this many minutes after (or before, if negative) NOW."""
    return (NOW + timedelta(minutes=minutes_from_now)).isoformat()


def make_ticket(ticket_id, due_in_minutes, status="open", priority="high",
                escalation_cycle=0, escalated_cycle=None):
    """Build a bare ticket by hand. due_in_minutes < 0 means it is already past due."""
    return {"id": ticket_id, "title": f"Ticket {ticket_id}", "category": "Network",
            "urgency": "low", "affected_users": 1, "priority": priority,
            "status": status, "assigned_to": None,
            "created_at": iso(-600), "updated_at": iso(-600), "due_at": iso(due_in_minutes),
            "escalation_cycle": escalation_cycle, "escalated_cycle": escalated_cycle}


def ids(tickets):
    return [ticket["id"] for ticket in tickets]


class TestSlaAttentionQueue(unittest.TestCase):
    def test_overdue_tickets_come_before_ones_that_are_not(self):
        tickets = [make_ticket("T001", +30), make_ticket("T002", -30)]
        self.assertEqual(ids(get_sla_attention_queue(tickets, NOW)), ["T002", "T001"])

    def test_overdue_come_first_even_if_a_not_overdue_ticket_is_due_sooner_by_id(self):
        tickets = [make_ticket("T001", +1), make_ticket("T002", +5), make_ticket("T003", -500)]
        self.assertEqual(ids(get_sla_attention_queue(tickets, NOW)), ["T003", "T001", "T002"])

    def test_within_each_group_the_earliest_due_at_comes_first(self):
        tickets = [
            make_ticket("T001", -10), make_ticket("T002", -90),
            make_ticket("T003", +20), make_ticket("T004", +5),
        ]
        self.assertEqual(ids(get_sla_attention_queue(tickets, NOW)),
                         ["T002", "T001", "T004", "T003"])

    def test_equal_due_at_is_broken_by_numeric_id_not_text(self):
        tickets = [make_ticket("T1000", -10), make_ticket("T999", -10), make_ticket("T002", -10)]
        self.assertEqual(ids(get_sla_attention_queue(tickets, NOW)), ["T002", "T999", "T1000"])

    def test_exactly_at_due_at_counts_as_not_overdue(self):
        tickets = [make_ticket("T001", 0), make_ticket("T002", -1)]
        self.assertEqual(ids(get_sla_attention_queue(tickets, NOW)), ["T002", "T001"])
        self.assertIn("[on time]", format_sla_ticket(tickets[0], NOW))
        self.assertIn("[OVERDUE]", format_sla_ticket(tickets[1], NOW))

    def test_open_and_in_progress_are_included_and_resolved_is_left_out(self):
        tickets = [make_ticket("T001", +10, status="open"),
                   make_ticket("T002", +10, status="in_progress"),
                   make_ticket("T003", -10, status="resolved")]
        self.assertEqual(ids(get_sla_attention_queue(tickets, NOW)), ["T001", "T002"])

    def test_no_tickets_gives_an_empty_queue(self):
        self.assertEqual(get_sla_attention_queue([], NOW), [])

    def test_queue_does_not_change_or_reorder_the_tickets(self):
        tickets = [make_ticket("T002", +10), make_ticket("T001", -10)]
        before = copy.deepcopy(tickets)
        queue = get_sla_attention_queue(tickets, NOW)
        self.assertEqual(tickets, before)
        self.assertIsNot(queue, tickets)

    def test_label_line_shows_the_deadline(self):
        line = format_sla_ticket(make_ticket("T001", -30), NOW)
        self.assertTrue(line.startswith("[OVERDUE] T001 | "))
        self.assertIn(f"due {iso(-30)}", line)


class TestOriginalQueueIsUntouched(unittest.TestCase):
    def test_open_work_queue_still_orders_by_priority_then_id(self):
        tickets = [
            make_ticket("T003", -500, priority="low"),
            make_ticket("T002", +500, priority="critical"),
            make_ticket("T001", +500, priority="critical"),
            make_ticket("T004", -500, priority="high", status="in_progress"),
        ]
        # Priority decides, not how overdue a ticket is; in_progress is not "open".
        self.assertEqual(ids(get_work_queue(tickets)), ["T001", "T002", "T003"])

    def test_original_report_still_works_on_new_style_tickets(self):
        tickets = [make_ticket("T001", +10), make_ticket("T002", -10, status="resolved")]
        report = build_report(tickets)
        self.assertEqual(report["total"], 2)
        self.assertEqual(report["by_status"]["resolved"], 1)


class TestBuildMetrics(unittest.TestCase):
    def sample(self):
        return [
            make_ticket("T001", -30, status="open", priority="critical"),                  # overdue
            make_ticket("T002", -30, status="in_progress", priority="high",
                        escalation_cycle=0, escalated_cycle=0),                            # overdue, escalated
            make_ticket("T003", +30, status="open", priority="medium"),                    # fine
            make_ticket("T004", -99, status="resolved", priority="low",
                        escalation_cycle=0, escalated_cycle=0),                            # resolved
            make_ticket("T005", -30, status="open", priority="critical",
                        escalation_cycle=1, escalated_cycle=0),                            # reopened: new cycle
        ]

    def test_status_counts(self):
        metrics = build_metrics(self.sample(), NOW)
        self.assertEqual((metrics["open"], metrics["in_progress"], metrics["resolved"]), (3, 1, 1))

    def test_overdue_counts_unresolved_tickets_only(self):
        self.assertEqual(build_metrics(self.sample(), NOW)["overdue_unresolved"], 3)

    def test_escalated_counts_current_cycle_of_unresolved_tickets_only(self):
        # T002 yes; T004 is resolved; T005 was escalated in cycle 0 but is now in cycle 1.
        self.assertEqual(build_metrics(self.sample(), NOW)["escalated_current_cycle"], 1)

    def test_never_escalated_ticket_is_not_counted_even_when_cycle_is_zero(self):
        metrics = build_metrics([make_ticket("T001", -30)], NOW)
        self.assertEqual(metrics["escalated_current_cycle"], 0)

    def test_priority_counts_include_every_priority_and_add_up(self):
        metrics = build_metrics(self.sample(), NOW)
        self.assertEqual(metrics["by_priority"],
                         {"critical": 2, "high": 1, "medium": 1, "low": 1})
        self.assertEqual(sum(metrics["by_priority"].values()), metrics["total"])
        self.assertEqual(metrics["open"] + metrics["in_progress"] + metrics["resolved"],
                         metrics["total"])

    def test_no_tickets_gives_all_zeros(self):
        metrics = build_metrics([], NOW)
        self.assertEqual(metrics["total"], 0)
        self.assertEqual(metrics["by_priority"],
                         {"critical": 0, "high": 0, "medium": 0, "low": 0})
        self.assertEqual(metrics["overdue_unresolved"], 0)

    def test_metrics_do_not_change_the_tickets(self):
        tickets = self.sample()
        before = copy.deepcopy(tickets)
        build_metrics(tickets, NOW)
        self.assertEqual(tickets, before)

    def test_unknown_status_or_priority_is_rejected(self):
        for field, value in [("status", "banana"), ("priority", "urgent")]:
            ticket = make_ticket("T001", +10)
            ticket[field] = value
            with self.assertRaises(ValueError):
                build_metrics([ticket], NOW)


if __name__ == "__main__":
    unittest.main()
