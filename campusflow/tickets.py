"""Ticket rules and lookup for CampusFlow."""

from campusflow.sla import calculate_due_at, to_iso, utc_now

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


def clean_title(title):
    """Return the title without outer spaces. Raise ValueError if it is blank."""
    title = title.strip()
    if title == "":
        raise ValueError("Title cannot be blank")
    return title


def clean_category(category):
    """Return the category in its proper form, e.g. 'network' -> 'Network'."""
    wanted = category.strip().lower()
    for name in CATEGORIES:
        if name.lower() == wanted:
            return name
    raise ValueError(f"Category must be one of: {', '.join(CATEGORIES)}")


def clean_urgency(urgency):
    """Return the urgency in lowercase. Raise ValueError if it is not allowed."""
    wanted = urgency.strip().lower()
    if wanted not in URGENCIES:
        raise ValueError(f"Urgency must be one of: {', '.join(URGENCIES)}")
    return wanted


def clean_affected_users(value):
    """Return affected users as a positive whole number (decision D7)."""
    if isinstance(value, bool):  # True is secretly 1 in Python, so reject it first
        raise ValueError("Affected users must be a whole number")
    if isinstance(value, str):
        text = value.strip()
        if not (text.isascii() and text.isdigit()):
            raise ValueError("Affected users must be a whole number")
        value = int(text)
    if not isinstance(value, int):
        raise ValueError("Affected users must be a whole number")
    if value < 1:
        raise ValueError("Affected users must be at least 1")
    return value


def calculate_priority(urgency, affected_users):
    """Return the priority. The first matching rule wins (section 5)."""
    if urgency == "high" and affected_users >= 10:
        return "critical"
    if urgency == "high" or affected_users >= 10:
        return "high"
    if urgency == "medium" or affected_users >= 3:
        return "medium"
    return "low"


def generate_id(tickets):
    """Return the next ID: the highest existing number plus one (decision D8)."""
    highest = 0
    for ticket in tickets:
        number = int(ticket["id"][1:])
        if number > highest:
            highest = number
    return f"T{highest + 1:03d}"


def create_ticket(tickets, title, category, urgency, affected_users, now=None):
    """Validate the inputs, add a new ticket to the list and return it.

    `now` is the creation time (an aware datetime). The menu passes it in;
    if it is left out, the real clock is read once here.
    """
    if now is None:
        now = utc_now()
    # Every check happens first, so a bad input never changes the list.
    title = clean_title(title)
    category = clean_category(category)
    urgency = clean_urgency(urgency)
    affected_users = clean_affected_users(affected_users)
    priority = calculate_priority(urgency, affected_users)
    created = to_iso(now)  # also rejects a time with no timezone

    ticket = {
        "id": generate_id(tickets),
        "title": title,
        "category": category,
        "urgency": urgency,
        "affected_users": affected_users,
        "priority": priority,
        "status": "open",
        "assigned_to": None,
        "created_at": created,
        "updated_at": created,
        "due_at": to_iso(calculate_due_at(priority, now)),
        "escalation_cycle": 0,
        "escalated_cycle": None,
    }
    tickets.append(ticket)
    return ticket


def format_ticket(ticket):
    """Return one ticket as a single line of text for the menu to print."""
    assigned = ticket["assigned_to"] or "unassigned"
    return (
        f"{ticket['id']} | {ticket['title']} | {ticket['category']} | "
        f"{ticket['priority']} | {ticket['status']} | {assigned}"
    )