import unittest

from campusflow.tickets import (
    calculate_priority,
    create_ticket,
    format_ticket,
    generate_id,
    get_ticket,
)


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


class TestCalculatePriority(unittest.TestCase):
    def test_high_urgency_with_ten_users_is_critical(self):
        self.assertEqual(calculate_priority("high", 10), "critical")

    def test_high_urgency_with_few_users_is_high(self):
        self.assertEqual(calculate_priority("high", 9), "high")

    def test_ten_users_with_low_urgency_is_high(self):
        self.assertEqual(calculate_priority("low", 10), "high")

    def test_medium_urgency_is_medium(self):
        self.assertEqual(calculate_priority("medium", 1), "medium")

    def test_three_users_with_low_urgency_is_medium(self):
        self.assertEqual(calculate_priority("low", 3), "medium")

    def test_low_urgency_with_two_users_is_low(self):
        self.assertEqual(calculate_priority("low", 2), "low")

    def test_medium_urgency_with_ten_users_is_high_not_medium(self):
        self.assertEqual(calculate_priority("medium", 10), "high")


class TestGenerateId(unittest.TestCase):
    def test_first_id_on_empty_list(self):
        self.assertEqual(generate_id([]), "T001")

    def test_next_id_after_existing_tickets(self):
        self.assertEqual(generate_id(make_tickets()), "T003")

    def test_uses_highest_number_not_the_count(self):
        tickets = [{"id": "T005"}, {"id": "T002"}]
        self.assertEqual(generate_id(tickets), "T006")

    def test_gets_past_three_digits(self):
        self.assertEqual(generate_id([{"id": "T999"}]), "T1000")


class TestCreateTicket(unittest.TestCase):
    def test_creates_a_full_ticket(self):
        tickets = []
        ticket = create_ticket(tickets, "Printer jam", "Hardware", "medium", 4)
        self.assertEqual(ticket["id"], "T001")
        self.assertEqual(ticket["title"], "Printer jam")
        self.assertEqual(ticket["category"], "Hardware")
        self.assertEqual(ticket["urgency"], "medium")
        self.assertEqual(ticket["affected_users"], 4)
        self.assertEqual(ticket["priority"], "medium")
        self.assertEqual(ticket["status"], "open")
        self.assertIsNone(ticket["assigned_to"])

    def test_adds_the_same_ticket_to_the_list(self):
        tickets = make_tickets()
        ticket = create_ticket(tickets, "Printer jam", "Hardware", "low", 1)
        self.assertEqual(len(tickets), 3)
        self.assertIs(tickets[-1], ticket)
        self.assertEqual(ticket["id"], "T003")

    def test_cleans_spaces_and_letter_case(self):
        ticket = create_ticket([], "  Wi-Fi down  ", " network ", " HIGH ", " 12 ")
        self.assertEqual(ticket["title"], "Wi-Fi down")
        self.assertEqual(ticket["category"], "Network")
        self.assertEqual(ticket["urgency"], "high")
        self.assertEqual(ticket["affected_users"], 12)
        self.assertEqual(ticket["priority"], "critical")

    def test_blank_title_is_rejected(self):
        with self.assertRaises(ValueError):
            create_ticket([], "   ", "Network", "low", 1)

    def test_unknown_category_is_rejected(self):
        with self.assertRaises(ValueError):
            create_ticket([], "Problem", "Plumbing", "low", 1)

    def test_unknown_urgency_is_rejected(self):
        with self.assertRaises(ValueError):
            create_ticket([], "Problem", "Network", "urgent", 1)

    def test_bad_affected_users_are_rejected(self):
        bad_values = [0, -3, 2.5, "abc", "", "  ", "4.5", "-2", True, None]
        for bad in bad_values:
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    create_ticket([], "Problem", "Network", "low", bad)

    def test_rejected_ticket_does_not_change_the_list(self):
        tickets = make_tickets()
        with self.assertRaises(ValueError):
            create_ticket(tickets, "Problem", "Network", "low", 0)
        self.assertEqual(len(tickets), 2)


class TestFormatTicket(unittest.TestCase):
    def test_unassigned_ticket(self):
        line = format_ticket(make_tickets()[0])
        self.assertEqual(
            line, "T001 | Campus Wi-Fi is down | Network | critical | open | unassigned"
        )

    def test_assigned_ticket(self):
        ticket = make_tickets()[1]
        ticket["assigned_to"] = "Sam"
        self.assertTrue(format_ticket(ticket).endswith("| Sam"))


if __name__ == "__main__":
    unittest.main()