"""Ticket rules and lookup for CampusFlow."""

CATEGORIES = ["Network", "Hardware", "Software", "Other"]
URGENCIES = ["low", "medium", "high"]
STATUSES = ["open", "in_progress", "resolved"]
PRIORITIES = ["critical", "high", "medium", "low"]


def get_ticket(tickets, ticket_id):
    """Return the ticket with this ID. Raise ValueError if there is none."""
    wanted = ticket_id.strip().upper()
    for ticket in tickets:
        if ticket["id"] == wanted:
            return ticket
    raise ValueError(f"Ticket {ticket_id} not found")