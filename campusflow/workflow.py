"""Assignment and status workflow for CampusFlow."""

from campusflow.tickets import PRIORITIES, STATUSES, get_ticket

# Which status a ticket may move to, from each status (decision D10).
# "resolved" has no way forward here: only reopen_ticket can bring it back.
ALLOWED_MOVES = {
    "open": ["in_progress"],
    "in_progress": ["resolved"],
    "resolved": [],
}


def assign_ticket(tickets, ticket_id, staff_name):
    """Assign a ticket to a staff member and return it."""
    ticket = get_ticket(tickets, ticket_id)
    staff_name = staff_name.strip()
    if staff_name == "":
        raise ValueError("Staff name cannot be blank")
    if ticket["status"] == "resolved":
        raise ValueError(f"Ticket {ticket['id']} is resolved. Reopen it first")
    ticket["assigned_to"] = staff_name
    return ticket


def change_status(tickets, ticket_id, new_status):
    """Move a ticket to its next status and return it. Raise ValueError if not allowed."""
    ticket = get_ticket(tickets, ticket_id)
    new_status = new_status.strip().lower()
    if new_status not in STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(STATUSES)}")

    current = ticket["status"]
    if new_status not in ALLOWED_MOVES[current]:
        if current == "resolved":
            raise ValueError("A resolved ticket can only be reopened, not changed")
        raise ValueError(f"Cannot move a ticket from {current} to {new_status}")
    if new_status == "in_progress" and ticket["assigned_to"] is None:
        raise ValueError("Assign the ticket to someone before starting work on it")

    # Every check passed, so it is now safe to change the ticket.
    ticket["status"] = new_status
    return ticket


def reopen_ticket(tickets, ticket_id):
    """Reopen a resolved ticket. The assignee is kept."""
    ticket = get_ticket(tickets, ticket_id)
    if ticket["status"] != "resolved":
        raise ValueError(f"Ticket {ticket['id']} is not resolved, so it cannot be reopened")
    ticket["status"] = "open"
    return ticket


def queue_order(ticket):
    """Sorting key: priority first (critical to low), then the earlier ID."""
    return (PRIORITIES.index(ticket["priority"]), int(ticket["id"][1:]))


def get_work_queue(tickets):
    """Return the open tickets, most urgent first (decision D9, section 5)."""
    open_tickets = [ticket for ticket in tickets if ticket["status"] == "open"]
    return sorted(open_tickets, key=queue_order)