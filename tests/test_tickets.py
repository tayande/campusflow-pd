import unittest

from campusflow.tickets import get_ticket


def make_tickets():
    """Return a fresh list of two tickets, so tests never share data."""
    return [
        {
            "id": "T001",
            "title": "Campus Wi-Fi is down",
            "category": "Network",
            "urgency": "high",
            "affected_users": 15,
            "priority": "critical",
            "status": "open",
            "assigned_to": None,
        },
        {
            "id": "T002",
            "title": "Laptop will not start",
            "category": "Hardware",
            "urgency": "low",
            "affected_users": 1,
            "priority": "low",
            "status": "open",
            "assigned_to": None,
        },
    ]


class TestGetTicket(unittest.TestCase):
    def test_finds_existing_ticket(self):
        tickets = make_tickets()
        ticket = get_ticket(tickets, "T001")
        self.assertEqual(ticket["id"], "T001")
        self.assertEqual(ticket["title"], "Campus Wi-Fi is down")
        self.assertIs(ticket, tickets[0])  # the same dictionary, not a copy

    def test_ignores_spaces_and_letter_case(self):
        tickets = make_tickets()
        ticket = get_ticket(tickets, " t002 ")
        self.assertEqual(ticket["id"], "T002")

    def test_unknown_id_raises_value_error(self):
        tickets = make_tickets()
        with self.assertRaises(ValueError):
            get_ticket(tickets, "T999")

    def test_empty_list_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_ticket([], "T001")


if __name__ == "__main__":
    unittest.main()