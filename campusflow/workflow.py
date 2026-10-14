"""Assignment and status workflow for CampusFlow."""

from campusflow.sla import calculate_due_at, to_iso, utc_now
from campusflow.tickets import PRIORITIES, STATUSES, get_ticket

# Which status a ticket may move to, from each status (decision D10).
# "resolved" has no way forward here: only reopen_ticket can bring it back.
ALLOWED_MOVES = {
    "open": ["in_progress"],
    "in_progress": ["resolved"],
    "resolved": [],
}


def assign_ticket(tickets, ticket_id, staff_name, now=None):
    """Assign a ticket to a staff member and return it."""
    if now is None:
        now = utc_now()
    ticket = get_ticket(tickets, ticket_id)
    staff_name = staff_name.strip()
    if staff_name == "":
        raise ValueError("Staff name cannot be blank")
    if ticket["status"] == "resolved":
        raise ValueError(f"Ticket {ticket['id']} is resolved. Reopen it first")
    stamp = to_iso(now)
    ticket["assigned_to"] = staff_name
    ticket["updated_at"] = stamp
    return ticket


def change_status(tickets, ticket_id, new_status, now=None):
    """Move a ticket to its next status and return it. Raise ValueError if not allowed."""
    if now is None:
        now = utc_now()
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

    stamp = to_iso(now)

    # Every check passed, so it is now safe to change the ticket.
    ticket["status"] = new_status
    ticket["updated_at"] = stamp
    return ticket


def reopen_ticket(tickets, ticket_id, now=None):
    """Reopen a resolved ticket and start a new SLA cycle. The assignee is kept.

    The ticket keeps its created_at. Its deadline restarts from `now`, and its
    escalation_cycle goes up by one, so it can be escalated again in the new cycle.
    """
    if now is None:
        now = utc_now()
    ticket = get_ticket(tickets, ticket_id)
    if ticket["status"] != "resolved":
        raise ValueError(f"Ticket {ticket['id']} is not resolved, so it cannot be reopened")
    stamp = to_iso(now)
    due = to_iso(calculate_due_at(ticket["priority"], now))

    # Everything is worked out, so it is now safe to change the ticket.
    ticket["status"] = "open"
    ticket["due_at"] = due
    ticket["updated_at"] = stamp
    ticket["escalation_cycle"] = ticket.get("escalation_cycle", 0) + 1
    return ticket


def queue_order(ticket):
    """Sorting key: priority first (critical to low), then the earlier ID."""
    return (PRIORITIES.index(ticket["priority"]), int(ticket["id"][1:]))


def get_work_queue(tickets):
    """Return the open tickets, most urgent first (decision D9, section 5)."""
    open_tickets = [ticket for ticket in tickets if ticket["status"] == "open"]
    return sorted(open_tickets, key=queue_order)