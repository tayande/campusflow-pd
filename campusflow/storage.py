"""Saving and loading tickets as JSON for CampusFlow."""

import json
import os

from campusflow.history import EVENT_TYPES
from campusflow.tickets import CATEGORIES, PRIORITIES, STATUSES, URGENCIES
from campusflow.timeutil import parse_iso

# data/tickets.json at the top of the project, wherever the program is started from.
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(PROJECT_FOLDER, "data", "tickets.json")

SCHEMA_VERSION = 2

REQUIRED_KEYS = [
    "id", "title", "category", "urgency",
    "affected_users", "priority", "status", "assigned_to",
]


def save_tickets(tickets, path=DEFAULT_PATH):
    """Write the tickets to a JSON file, creating the folder if needed."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    # Write to a side file first, then swap it in. If the program stops half-way,
    # the old tickets.json is still complete (decision D11: no silent data loss).
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(tickets, file, indent=2)
    os.replace(temp_path, path)


def check_ticket(ticket, position):
    """Raise ValueError if a loaded ticket is not a valid ticket."""
    where = f"Ticket number {position} in the data file"
    if not isinstance(ticket, dict):
        raise ValueError(f"{where} is not a ticket")
    for key in REQUIRED_KEYS:
        if key not in ticket:
            raise ValueError(f"{where} is missing '{key}'")

    ticket_id = ticket["id"]
    if not (isinstance(ticket_id, str) and ticket_id[:1] == "T" and ticket_id[1:].isdigit()):
        raise ValueError(f"{where} has a bad id: {ticket_id!r}")
    if ticket["category"] not in CATEGORIES:
        raise ValueError(f"{where} has a bad category: {ticket['category']!r}")
    if ticket["urgency"] not in URGENCIES:
        raise ValueError(f"{where} has a bad urgency: {ticket['urgency']!r}")
    if ticket["priority"] not in PRIORITIES:
        raise ValueError(f"{where} has a bad priority: {ticket['priority']!r}")
    if ticket["status"] not in STATUSES:
        raise ValueError(f"{where} has a bad status: {ticket['status']!r}")
    users = ticket["affected_users"]
    if isinstance(users, bool) or not isinstance(users, int) or users < 1:
        raise ValueError(f"{where} has bad affected_users: {users!r}")


def load_tickets(path=DEFAULT_PATH):
    """Return the saved tickets. A missing file means a fresh start (empty list).

    Raise ValueError if the file is not valid JSON or does not hold valid tickets.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise ValueError(f"The data file is damaged and cannot be read: {error}")

    if not isinstance(data, list):
        raise ValueError("The data file must hold a list of tickets")
    for position, ticket in enumerate(data, start=1):
        check_ticket(ticket, position)
    return data


# ---------------------------------------------------------------------------
# Version 2 file: {"schema_version": 2, "tickets": [...], "events": [...]}
# The older functions above (a plain list of tickets) are kept for the old format.
# ---------------------------------------------------------------------------

V2_TICKET_KEYS = ["created_at", "updated_at", "due_at", "escalation_cycle", "escalated_cycle"]
EVENT_KEYS = [
    "event_id", "ticket_id", "event_type", "actor",
    "timestamp", "before_status", "after_status", "details",
]


def check_whole_number(value, where, name):
    """Raise ValueError unless value is an int of at least 0 (and not a bool)."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{where} has a bad {name}: {value!r}")


def check_time(value, where, name):
    """Raise ValueError unless value is ISO-8601 text with a timezone."""
    try:
        parse_iso(value)
    except ValueError as error:
        raise ValueError(f"{where} has a bad {name}: {error}")


def check_ticket_v2(ticket, position):
    """Raise ValueError if a ticket is not a valid version 2 ticket."""
    check_ticket(ticket, position)
    where = f"Ticket number {position} in the data file"
    for key in V2_TICKET_KEYS:
        if key not in ticket:
            raise ValueError(f"{where} is missing '{key}'")
    for key in ["created_at", "updated_at", "due_at"]:
        check_time(ticket[key], where, key)
    check_whole_number(ticket["escalation_cycle"], where, "escalation_cycle")
    if ticket["escalated_cycle"] is not None:
        check_whole_number(ticket["escalated_cycle"], where, "escalated_cycle")


def check_event(event, position):
    """Raise ValueError if an event is not a valid event."""
    where = f"Event number {position} in the data file"
    if not isinstance(event, dict):
        raise ValueError(f"{where} is not an event")
    for key in EVENT_KEYS:
        if key not in event:
            raise ValueError(f"{where} is missing '{key}'")

    event_id = event["event_id"]
    if not (isinstance(event_id, str) and event_id[:1] == "E" and event_id[1:].isdigit()):
        raise ValueError(f"{where} has a bad event_id: {event_id!r}")
    if not isinstance(event["ticket_id"], str):
        raise ValueError(f"{where} has a bad ticket_id: {event['ticket_id']!r}")
    if event["event_type"] not in EVENT_TYPES:
        raise ValueError(f"{where} has a bad event_type: {event['event_type']!r}")
    actor = event["actor"]
    if not isinstance(actor, str) or actor.strip() == "":
        raise ValueError(f"{where} has a bad actor: {actor!r}")
    check_time(event["timestamp"], where, "timestamp")
    if event["before_status"] is not None and event["before_status"] not in STATUSES:
        raise ValueError(f"{where} has a bad before_status: {event['before_status']!r}")
    if event["after_status"] not in STATUSES:
        raise ValueError(f"{where} has a bad after_status: {event['after_status']!r}")
    if not isinstance(event["details"], dict):
        raise ValueError(f"{where} has bad details: {event['details']!r}")


def check_data(tickets, events):
    """Raise ValueError unless the tickets and events are valid and agree with each other."""
    if not isinstance(tickets, list):
        raise ValueError("The 'tickets' part of the data file must be a list")
    if not isinstance(events, list):
        raise ValueError("The 'events' part of the data file must be a list")

    ticket_ids = set()
    for position, ticket in enumerate(tickets, start=1):
        check_ticket_v2(ticket, position)
        if ticket["id"] in ticket_ids:
            raise ValueError(f"Duplicate ticket ID in the data file: {ticket['id']}")
        ticket_ids.add(ticket["id"])

    event_ids = set()
    for position, event in enumerate(events, start=1):
        check_event(event, position)
        if event["event_id"] in event_ids:
            raise ValueError(f"Duplicate event ID in the data file: {event['event_id']}")
        event_ids.add(event["event_id"])
        if event["ticket_id"] not in ticket_ids:
            raise ValueError(
                f"Event {event['event_id']} refers to a missing ticket: {event['ticket_id']}"
            )


def save_data(path, tickets, events):
    """Check the data, then write it as a version 2 file (temp file, then swap in)."""
    # Never write invalid data: a bad save must not damage a good file.
    check_data(tickets, events)

    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    data = {"schema_version": SCHEMA_VERSION, "tickets": tickets, "events": events}
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
    os.replace(temp_path, path)


def load_data(path):
    """Return (tickets, events) from a version 2 file.

    A missing file means a fresh start: ([], []). Anything else that is wrong
    raises ValueError BEFORE anything is returned, so bad data never replaces
    good data in memory.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return [], []
    except json.JSONDecodeError as error:
        raise ValueError(f"The data file is damaged and cannot be read: {error}")

    if isinstance(data, list):
        raise ValueError(
            "The data file is in the old format (a plain list of tickets). "
            "It was not changed."
        )
    if not isinstance(data, dict):
        raise ValueError("The data file must hold an object with tickets and events")
    version = data.get("schema_version")
    if isinstance(version, bool) or version != SCHEMA_VERSION:
        raise ValueError(f"Unsupported schema_version {version!r}; expected {SCHEMA_VERSION}")
    if "tickets" not in data or "events" not in data:
        raise ValueError("The data file must have both 'tickets' and 'events'")

    check_data(data["tickets"], data["events"])
    return data["tickets"], data["events"]
