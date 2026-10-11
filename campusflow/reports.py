"""Summary report for CampusFlow."""

from campusflow.tickets import PRIORITIES, STATUSES


def build_report(tickets):
    """Return a dictionary with the total and the counts by status and priority."""
    # Start every count at 0, so a missing group still shows up as 0.
    by_status = {status: 0 for status in STATUSES}
    by_priority = {priority: 0 for priority in PRIORITIES}

    for ticket in tickets:
        by_status[ticket["status"]] += 1
        by_priority[ticket["priority"]] += 1

    return {
        "total": len(tickets),
        "by_status": by_status,
        "by_priority": by_priority,
    }