import unittest

from campusflow.duplicates import detect_duplicates, normalize_title


def make_ticket(ticket_id, title, category="Network", status="open"):
    """Build a bare ticket by hand, so these tests do not depend on other code."""
    return {"id": ticket_id, "title": title, "category": category,
            "urgency": "low", "affected_users": 1, "priority": "low",
            "status": status, "assigned_to": None}


class TestNormalizeTitle(unittest.TestCase):
    def test_trims_lowercases_and_collapses_spaces(self):
        self.assertEqual(normalize_title("  Wi-Fi   Down "), "wi-fi down")

    def test_tabs_and_newlines_count_as_spaces(self):
        self.assertEqual(normalize_title("Wi-Fi\t\tDown\n"), "wi-fi down")

    def test_casefold_handles_special_letters(self):
        self.assertEqual(normalize_title("STRASSE"), normalize_title("straße"))

    def test_blank_title_gives_empty_text(self):
        self.assertEqual(normalize_title("   "), "")


class TestDetectDuplicates(unittest.TestCase):
    def test_spaced_and_capitalised_title_matches_plain_one(self):
        tickets = [make_ticket("T001", "  Wi-Fi   Down ")]
        self.assertEqual(detect_duplicates(tickets, "Network", "wi-fi down"), ["T001"])

    def test_different_category_does_not_match(self):
        tickets = [make_ticket("T001", "Wi-Fi down", category="Hardware")]
        self.assertEqual(detect_duplicates(tickets, "Network", "Wi-Fi down"), [])

    def test_category_is_compared_ignoring_case(self):
        tickets = [make_ticket("T001", "Wi-Fi down")]
        self.assertEqual(detect_duplicates(tickets, " network ", "Wi-Fi down"), ["T001"])

    def test_resolved_ticket_does_not_match(self):
        tickets = [make_ticket("T001", "Wi-Fi down", status="resolved")]
        self.assertEqual(detect_duplicates(tickets, "Network", "Wi-Fi down"), [])

    def test_open_and_in_progress_tickets_both_match_in_list_order(self):
        tickets = [
            make_ticket("T003", "Wi-Fi down", status="in_progress"),
            make_ticket("T001", "Wi-Fi down"),
            make_ticket("T002", "Printer jam"),
        ]
        self.assertEqual(detect_duplicates(tickets, "Network", "WI-FI DOWN"), ["T003", "T001"])

    def test_different_title_does_not_match(self):
        tickets = [make_ticket("T001", "Wi-Fi down")]
        self.assertEqual(detect_duplicates(tickets, "Network", "Wi-Fi slow"), [])

    def test_no_tickets_gives_no_matches(self):
        self.assertEqual(detect_duplicates([], "Network", "Wi-Fi down"), [])

    def test_detecting_does_not_change_the_tickets(self):
        tickets = [make_ticket("T001", "  Wi-Fi   Down ")]
        before = [dict(ticket) for ticket in tickets]
        detect_duplicates(tickets, "Network", "wi-fi down")
        self.assertEqual(tickets, before)


if __name__ == "__main__":
    unittest.main()
