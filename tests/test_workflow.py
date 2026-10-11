import unittest

from campusflow.workflow import (
    assign_ticket,
    change_status,
    get_work_queue,
    reopen_ticket,
)


def make_tickets():
    """Return a fresh list of tickets in different states, so tests never share data."""
    return [
        {"id": "T001", "title": "Campus Wi-Fi is down", "category": "Network",
         "urgency": "high", "affected_users": 15, "priority": "critical",
         "status": "open", "assigned_to": None},
        {"id": "T002", "title": "Laptop will not start", "category": "Hardware",
         "urgency": "low", "affected_users": 1, "priority": "low",
         "status": "open", "assigned_to": "Sam"},
        {"id": "T003", "title": "Projector flickers", "category": "Hardware",
         "urgency": "medium", "affected_users": 4, "priority": "medium",
         "status": "in_progress", "assigned_to": "Ada"},
        {"id": "T004", "title": "Email login fails", "category": "Software",
         "urgency": "medium", "affected_users": 2, "priority": "medium",
         "status": "resolved", "assigned_to": "Kim"},
    ]


class TestAssignTicket(unittest.TestCase):
    def test_assigns_an_open_ticket(self):
        tickets = make_tickets()
        ticket = assign_ticket(tickets, "T001", "Sam")
        self.assertEqual(ticket["assigned_to"], "Sam")
        self.assertIs(ticket, tickets[0])

    def test_staff_name_is_stripped_and_id_is_forgiving(self):
        tickets = make_tickets()
        assign_ticket(tickets, " t001 ", "  Sam  ")
        self.assertEqual(tickets[0]["assigned_to"], "Sam")

    def test_can_reassign_an_in_progress_ticket(self):
        tickets = make_tickets()
        assign_ticket(tickets, "T003", "Lee")
        self.assertEqual(tickets[2]["assigned_to"], "Lee")

    def test_blank_name_is_rejected_and_nothing_changes(self):
        tickets = make_tickets()
        with self.assertRaises(ValueError):
            assign_ticket(tickets, "T001", "   ")
        self.assertIsNone(tickets[0]["assigned_to"])

    def test_unknown_ticket_is_rejected(self):
        with self.assertRaises(ValueError):
            assign_ticket(make_tickets(), "T999", "Sam")

    def test_resolved_ticket_cannot_be_assigned(self):
        tickets = make_tickets()
        with self.assertRaises(ValueError):
            assign_ticket(tickets, "T004", "Lee")
        self.assertEqual(tickets[3]["assigned_to"], "Kim")


class TestChangeStatus(unittest.TestCase):
    def test_unassigned_ticket_cannot_start(self):
        tickets = make_tickets()
        with self.assertRaises(ValueError):
            change_status(tickets, "T001", "in_progress")
        self.assertEqual(tickets[0]["status"], "open")

    def test_assigned_open_ticket_moves_to_in_progress(self):
        tickets = make_tickets()
        ticket = change_status(tickets, "T002", "in_progress")
        self.assertEqual(ticket["status"], "in_progress")
        self.assertIs(ticket, tickets[1])

    def test_in_progress_ticket_moves_to_resolved(self):
        tickets = make_tickets()
        change_status(tickets, "T003", "resolved")
        self.assertEqual(tickets[2]["status"], "resolved")

    def test_open_cannot_jump_to_resolved(self):
        tickets = make_tickets()
        with self.assertRaises(ValueError):
            change_status(tickets, "T002", "resolved")
        self.assertEqual(tickets[1]["status"], "open")

    def test_in_progress_cannot_go_back_to_open(self):
        tickets = make_tickets()
        with self.assertRaises(ValueError):
            change_status(tickets, "T003", "open")
        self.assertEqual(tickets[2]["status"], "in_progress")

    def test_resolved_cannot_be_changed_here(self):
        tickets = make_tickets()
        for target in ["open", "in_progress", "resolved"]:
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    change_status(tickets, "T004", target)
        self.assertEqual(tickets[3]["status"], "resolved")

    def test_status_is_cleaned_before_checking(self):
        tickets = make_tickets()
        change_status(tickets, "T003", "  RESOLVED ")
        self.assertEqual(tickets[2]["status"], "resolved")

    def test_unknown_status_is_rejected(self):
        with self.assertRaises(ValueError):
            change_status(make_tickets(), "T002", "banana")

    def test_moving_to_the_same_status_is_rejected(self):
        tickets = make_tickets()
        with self.assertRaises(ValueError):
            change_status(tickets, "T003", "in_progress")
        self.assertEqual(tickets[2]["status"], "in_progress")

    def test_unknown_ticket_is_rejected(self):
        with self.assertRaises(ValueError):
            change_status(make_tickets(), "T999", "in_progress")


class TestReopenTicket(unittest.TestCase):
    def test_reopens_a_resolved_ticket_and_keeps_the_assignee(self):
        tickets = make_tickets()
        ticket = reopen_ticket(tickets, "T004")
        self.assertEqual(ticket["status"], "open")
        self.assertEqual(ticket["assigned_to"], "Kim")

    def test_open_ticket_cannot_be_reopened(self):
        with self.assertRaises(ValueError):
            reopen_ticket(make_tickets(), "T001")

    def test_in_progress_ticket_cannot_be_reopened(self):
        with self.assertRaises(ValueError):
            reopen_ticket(make_tickets(), "T003")

    def test_unknown_ticket_is_rejected(self):
        with self.assertRaises(ValueError):
            reopen_ticket(make_tickets(), "T999")

    def test_reopened_ticket_can_be_changed_again(self):
        tickets = make_tickets()
        reopen_ticket(tickets, "T004")
        change_status(tickets, "T004", "in_progress")
        self.assertEqual(tickets[3]["status"], "in_progress")


def queue_ticket(number, priority, status="open"):
    """Build a small ticket for queue tests."""
    return {"id": f"T{number:03d}", "title": "x", "category": "Other",
            "urgency": "low", "affected_users": 1, "priority": priority,
            "status": status, "assigned_to": None}


class TestGetWorkQueue(unittest.TestCase):
    def test_orders_by_priority_critical_first(self):
        tickets = [queue_ticket(1, "low"), queue_ticket(2, "critical"),
                   queue_ticket(3, "medium"), queue_ticket(4, "high")]
        ids = [t["id"] for t in get_work_queue(tickets)]
        self.assertEqual(ids, ["T002", "T004", "T003", "T001"])

    def test_ties_go_to_the_earlier_id(self):
        tickets = [queue_ticket(3, "high"), queue_ticket(1, "high"), queue_ticket(2, "high")]
        ids = [t["id"] for t in get_work_queue(tickets)]
        self.assertEqual(ids, ["T001", "T002", "T003"])

    def test_numeric_order_not_text_order(self):
        tickets = [queue_ticket(1000, "low"), queue_ticket(999, "low")]
        ids = [t["id"] for t in get_work_queue(tickets)]
        self.assertEqual(ids, ["T999", "T1000"])

    def test_only_open_tickets_are_included(self):
        tickets = [queue_ticket(1, "high", "in_progress"),
                   queue_ticket(2, "high", "resolved"),
                   queue_ticket(3, "low", "open")]
        ids = [t["id"] for t in get_work_queue(tickets)]
        self.assertEqual(ids, ["T003"])

    def test_urgent_ticket_that_is_in_progress_is_not_in_the_queue(self):
        tickets = [queue_ticket(1, "critical", "in_progress"), queue_ticket(2, "low")]
        ids = [t["id"] for t in get_work_queue(tickets)]
        self.assertEqual(ids, ["T002"])

    def test_empty_list_gives_empty_queue(self):
        self.assertEqual(get_work_queue([]), [])

    def test_original_list_is_not_reordered(self):
        tickets = [queue_ticket(1, "low"), queue_ticket(2, "critical")]
        get_work_queue(tickets)
        self.assertEqual([t["id"] for t in tickets], ["T001", "T002"])


if __name__ == "__main__":
    unittest.main()