"""Saving and loading tickets as JSON for CampusFlow."""

import json
import os

from campusflow.tickets import CATEGORIES, PRIORITIES, STATUSES, URGENCIES

# data/tickets.json at the top of the project, wherever the program is started from.
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(PROJECT_FOLDER, "data", "tickets.json")

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