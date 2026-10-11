"""The command-line menu for CampusFlow.

Run it from the project folder with:  python3 -m campusflow.main

This is the only file that talks to the user (decision D4). Every menu action
has the same shape: action(tickets, ask, say) and returns True if it changed
the tickets, so the menu knows to save them.
"""

import sys

from campusflow.storage import DEFAULT_PATH, load_tickets, save_tickets
from campusflow.tickets import (
    CATEGORIES,
    URGENCIES,
    clean_affected_users,
    clean_category,
    clean_title,
    clean_urgency,
    create_ticket,
    format_ticket,
    get_ticket,
)


def ask_until_valid(ask, say, prompt, cleaner):
    """Keep asking until the cleaner accepts the answer, then return the clean value."""
    while True:
        try:
            return cleaner(ask(prompt))
        except ValueError as error:
            say(f"Error: {error}")


def create_action(tickets, ask, say):
    """Menu option 1: ask for the details and create a ticket."""
    title = ask_until_valid(ask, say, "Title: ", clean_title)
    category = ask_until_valid(
        ask, say, f"Category ({', '.join(CATEGORIES)}): ", clean_category
    )
    urgency = ask_until_valid(
        ask, say, f"Urgency ({', '.join(URGENCIES)}): ", clean_urgency
    )
    users = ask_until_valid(ask, say, "Affected users: ", clean_affected_users)

    ticket = create_ticket(tickets, title, category, urgency, users)
    say(f"Created {ticket['id']} with priority {ticket['priority']}.")
    return True


def list_action(tickets, ask, say):
    """Menu option 2: show every ticket on one line."""
    if not tickets:
        say("No tickets yet.")
        return False
    for ticket in tickets:
        say(format_ticket(ticket))
    return False


def view_action(tickets, ask, say):
    """Menu option 3: show every detail of one ticket."""
    ticket = get_ticket(tickets, ask("Ticket ID: "))
    say(f"ID:             {ticket['id']}")
    say(f"Title:          {ticket['title']}")
    say(f"Category:       {ticket['category']}")
    say(f"Urgency:        {ticket['urgency']}")
    say(f"Affected users: {ticket['affected_users']}")
    say(f"Priority:       {ticket['priority']}")
    say(f"Status:         {ticket['status']}")
    say(f"Assigned to:    {ticket['assigned_to'] or 'unassigned'}")
    return False


# Menu key -> (label, action). Engineer B adds her options here (keys "4" to "8").
ACTIONS = {
    "1": ("Create a ticket", create_action),
    "2": ("List all tickets", list_action),
    "3": ("View one ticket", view_action),
}
EXIT_KEY = "0"


def show_menu(say):
    say("")
    say("=== CampusFlow ===")
    for key, (label, _action) in ACTIONS.items():
        say(f"{key}. {label}")
    say(f"{EXIT_KEY}. Exit")


def run(path=DEFAULT_PATH, ask=input, say=print):
    """Load the tickets, run the menu until the user exits, and return an exit code."""
    try:
        tickets = load_tickets(path)
    except ValueError as error:
        # Stop without saving, so a damaged file is never overwritten (decision D11).
        say(f"Cannot start: {error}")
        say("Fix or move the data file and try again. Nothing was changed.")
        return 1

    try:
        while True:
            show_menu(say)
            choice = ask("Choose an option: ").strip()
            if choice == EXIT_KEY:
                break
            if choice not in ACTIONS:
                say("Please choose a number from the menu.")
                continue

            _label, action = ACTIONS[choice]
            try:
                changed = action(tickets, ask, say)
            except ValueError as error:
                say(f"Error: {error}")
                continue

            if changed:
                try:
                    save_tickets(tickets, path)
                except OSError as error:
                    say(f"WARNING: the change could not be saved: {error}")
    except (EOFError, KeyboardInterrupt):
        say("")

    say("Goodbye.")
    return 0


if __name__ == "__main__":
    sys.exit(run())