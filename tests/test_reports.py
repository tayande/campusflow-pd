import unittest

from campusflow.reports import build_report


def report_ticket(number, priority, status):
    """Build a small ticket for report tests."""
    return {"id": f"T{number:03d}", "title": "x", "category": "Other",
            "urgency": "low", "affected_users": 1, "priority": priority,
            "status": status, "assigned_to": None}


class TestBuildReport(unittest.TestCase):
    def test_empty_list_gives_all_zeros(self):
        report = build_report([])
        self.assertEqual(report["total"], 0)
        self.assertEqual(report["by_status"],
                         {"open": 0, "in_progress": 0, "resolved": 0})
        self.assertEqual(report["by_priority"],
                         {"critical": 0, "high": 0, "medium": 0, "low": 0})

    def test_counts_by_status_and_priority(self):
        tickets = [
            report_ticket(1, "critical", "open"),
            report_ticket(2, "critical", "resolved"),
            report_ticket(3, "low", "open"),
            report_ticket(4, "medium", "in_progress"),
        ]
        report = build_report(tickets)
        self.assertEqual(report["total"], 4)
        self.assertEqual(report["by_status"],
                         {"open": 2, "in_progress": 1, "resolved": 1})
        self.assertEqual(report["by_priority"],
                         {"critical": 2, "high": 0, "medium": 1, "low": 1})

    def test_totals_add_up(self):
        tickets = [report_ticket(n, "high", "open") for n in range(1, 6)]
        report = build_report(tickets)
        self.assertEqual(sum(report["by_status"].values()), report["total"])
        self.assertEqual(sum(report["by_priority"].values()), report["total"])

    def test_unknown_status_is_rejected(self):
        with self.assertRaises(ValueError):
            build_report([report_ticket(1, "low", "done")])

    def test_unknown_priority_is_rejected(self):
        with self.assertRaises(ValueError):
            build_report([report_ticket(1, "extreme", "open")])


if __name__ == "__main__":
    unittest.main()