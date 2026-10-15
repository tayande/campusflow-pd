
"""The command-line menu for CampusFlow.

Run with: python3 -m campusflow.main

Each menu action has the shape action(ctx, ask, say).
It returns True if ticket data changed, so the menu knows to save.
"""

import sys
from dataclasses import dataclass
from datetime import datetime

from campusflow.duplicates import detect_duplicates
from campusflow.history import (
    clean_actor,
    format_event,
    get_history,
    record_event,
)
from campusflow.knowledge_lab import run_quiz, session_path_for
from campusflow.reports import (
    build_metrics,
    build_report,
    format_sla_ticket,
    get_sla_attention_queue,
)
from campusflow.sla import escalate_overdue
from campusflow.storage import DEFAULT_PATH, load_data, save_data
from campusflow.tickets import (
    CATEGORIES,
    STATUSES,
    URGENCIES,
    clean_affected_users,
    clean_category,
    clean_title,
    clean_urgency,
    create_ticket,
    format_ticket,
    get_ticket,
)
from campusflow.timeutil import utc_now
from campusflow.workflow import (
    assign_ticket,
    change_status,
    get_work_queue,
    reopen_ticket,
)

STATUS_EVENTS = {
    "in_progress": "START",
    "resolved": "RESOLVE",
}

KNOWLEDGE_SESSION_FOLDER = "data/knowledge_sessions"


@dataclass
class Context:
    """Data available to menu actions."""

    tickets: list
    events: list
    actor: str = ""
    now: datetime = None


def ask_until_valid(ask, say, prompt, cleaner):
    """Repeat a prompt until its answer passes validation."""
    while True:
        try:
            return cleaner(ask(prompt))
        except ValueError as error:
            say(f"Error: {error}")


def confirm(ask, say, prompt):
    """Ask for a clear yes or no."""
    while True:
        answer = ask(prompt).strip().lower()

        if answer in ("yes", "y"):
            return True

        if answer in ("no", "n"):
            return False

        say("Please answer yes or no.")


def clean_participant_label(value):
    """Accept participant A or B, ignoring case and surrounding spaces."""
    if not isinstance(value, str):
        raise ValueError("Participant must be A or B")

    participant = value.strip().upper()

    if participant not in ("A", "B"):
        raise ValueError("Participant must be A or B")

    return participant


def create_action(ctx, ask, say):
    """Create a ticket, warning about matching unresolved tickets."""
    title = ask_until_valid(
        ask, say, "Title: ", clean_title
    )
    category = ask_until_valid(
        ask, say, f"Category ({', '.join(CATEGORIES)}): ",
        clean_category,
    )
    urgency = ask_until_valid(
        ask, say, f"Urgency ({', '.join(URGENCIES)}): ",
        clean_urgency,
    )
    users = ask_until_valid(
        ask, say, "Affected users: ", clean_affected_users
    )

    matches = detect_duplicates(ctx.tickets, category, title)

    if matches:
        say(
            "Warning: similar unresolved ticket(s) already exist: "
            f"{', '.join(matches)}."
        )

        if not confirm(ask, say, "Create it anyway? (yes/no): "):
            say("Cancelled. No ticket was created.")
            return False

    ticket = create_ticket(
        ctx.tickets,
        title,
        category,
        urgency,
        users,
        now=ctx.now,
    )

    record_event(
        ctx.events,
        ticket["id"],
        "CREATE",
        ctx.actor,
        ctx.now,
        None,
        "open",
        {"priority": ticket["priority"]},
    )

    say(f"Created {ticket['id']} with priority {ticket['priority']}.")
    return True


def list_action(ctx, ask, say):
    """List every ticket."""
    if not ctx.tickets:
        say("No tickets yet.")
        return False

    for ticket in ctx.tickets:
        say(format_ticket(ticket))

    return False


def view_action(ctx, ask, say):
    """Display one ticket."""
    ticket = get_ticket(ctx.tickets, ask("Ticket ID: "))

    say(f"ID:             {ticket['id']}")
    say(f"Title:          {ticket['title']}")
    say(f"Category:       {ticket['category']}")
    say(f"Urgency:        {ticket['urgency']}")
    say(f"Affected users: {ticket['affected_users']}")
    say(f"Priority:       {ticket['priority']}")
    say(f"Status:         {ticket['status']}")
    say(f"Assigned to:    {ticket['assigned_to'] or 'unassigned'}")

    return False


def assign_action(ctx, ask, say):
    """Assign a ticket and record the successful operation."""
    ticket_id = ask("Ticket ID: ")
    staff_name = ask("Assign to: ")

    ticket = assign_ticket(
        ctx.tickets,
        ticket_id,
        staff_name,
        now=ctx.now,
    )

    record_event(
        ctx.events,
        ticket["id"],
        "ASSIGN",
        ctx.actor,
        ctx.now,
        ticket["status"],
        ticket["status"],
        {"assigned_to": ticket["assigned_to"]},
    )

    say(f"{ticket['id']} is now assigned to {ticket['assigned_to']}.")
    return True


def status_action(ctx, ask, say):
    """Change ticket status and record the successful transition."""
    ticket_id = ask("Ticket ID: ")
    new_status = ask(f"New status ({', '.join(STATUSES)}): ")

    # Capture the original status before attempting the transition.
    before = get_ticket(ctx.tickets, ticket_id)["status"]

    ticket = change_status(
        ctx.tickets,
        ticket_id,
        new_status,
        now=ctx.now,
    )

    record_event(
        ctx.events,
        ticket["id"],
        STATUS_EVENTS[ticket["status"]],
        ctx.actor,
        ctx.now,
        before,
        ticket["status"],
    )

    say(f"{ticket['id']} is now {ticket['status']}.")
    return True


def reopen_action(ctx, ask, say):
    """Reopen a resolved ticket."""
    ticket = reopen_ticket(
        ctx.tickets,
        ask("Ticket ID: "),
        now=ctx.now,
    )

    record_event(
        ctx.events,
        ticket["id"],
        "REOPEN",
        ctx.actor,
        ctx.now,
        "resolved",
        "open",
    )

    say(f"{ticket['id']} is open again.")
    return True


def queue_action(ctx, ask, say):
    """Display the original work queue."""
    queue = get_work_queue(ctx.tickets)

    if not queue:
        say("The work queue is empty.")
        return False

    say("Work queue (most urgent first):")

    for number, ticket in enumerate(queue, start=1):
        say(f"{number}. {format_ticket(ticket)}")

    return False


def report_action(ctx, ask, say):
    """Display the existing ticket report."""
    report = build_report(ctx.tickets)

    say(f"Total tickets: {report['total']}")
    say("By status:")

    for status, count in report["by_status"].items():
        say(f"  {status}: {count}")

    say("By priority:")

    for priority, count in report["by_priority"].items():
        say(f"  {priority}: {count}")

    return False


def sla_escalation_action(ctx, ask, say):
    """Escalate overdue tickets and report the results."""
    result = escalate_overdue(
        ctx.tickets,
        ctx.events,
        ctx.now,
        ctx.actor,
    )

    say(f"Newly escalated: {result['newly_escalated']}")
    say(f"Already escalated in this cycle: {result['already_escalated']}")

    # Ticket data changes when a new escalation is recorded.
    return result["newly_escalated"] > 0


def sla_queue_action(ctx, ask, say):
    """Display unresolved tickets in SLA attention order."""
    queue = get_sla_attention_queue(ctx.tickets, ctx.now)

    if not queue:
        say("No unresolved tickets.")
        return False

    say("SLA attention queue (overdue tickets first):")

    for number, ticket in enumerate(queue, start=1):
        say(f"{number}. {format_sla_ticket(ticket, ctx.now)}")

    return False


def metrics_action(ctx, ask, say):
    """Display ticket and SLA metrics."""
    metrics = build_metrics(ctx.tickets, ctx.now)

    say(f"Total tickets: {metrics['total']}")
    say(f"Open: {metrics['open']}")
    say(f"In progress: {metrics['in_progress']}")
    say(f"Resolved: {metrics['resolved']}")
    say(f"Overdue unresolved: {metrics['overdue_unresolved']}")
    say(
        "Escalated in current cycle: "
        f"{metrics['escalated_current_cycle']}"
    )

    say("By priority:")
    for priority, count in metrics["by_priority"].items():
        say(f"  {priority}: {count}")

    return False


def knowledge_lab_action(ctx, ask, say):
    """Run the Engineering Knowledge Lab without changing tickets."""
    participant = ask_until_valid(
        ask,
        say,
        "Participant (A or B): ",
        clean_participant_label,
    )

    session_path = session_path_for(
        KNOWLEDGE_SESSION_FOLDER,
        participant,
        ctx.now,
    )

    run_quiz(
        ask=ask,
        say=say,
        participant=participant,
        session_path=session_path,
        now=ctx.now,
    )

    # Quiz sessions do not change ticket data or create ticket events.
    return False


def history_action(ctx, ask, say):
    """Display a ticket's in-memory event history."""
    ticket = get_ticket(ctx.tickets, ask("Ticket ID: "))
    history = get_history(ctx.events, ticket["id"])

    if not history:
        say(f"No history recorded for {ticket['id']}.")
        return False

    say(f"History of {ticket['id']} (oldest first):")

    for event in history:
        say(format_event(event))

    return False


ACTIONS = {
    "1": ("Create a ticket", create_action),
    "2": ("List all tickets", list_action),
    "3": ("View one ticket", view_action),
    "4": ("Assign a ticket", assign_action),
    "5": ("Change a ticket's status", status_action),
    "6": ("Reopen a resolved ticket", reopen_action),
    "7": ("Show the work queue", queue_action),
    "8": ("Show the report", report_action),
    "9": ("Escalate overdue tickets", sla_escalation_action),
    "10": ("Show the SLA attention queue", sla_queue_action),
    "11": ("Show ticket and SLA metrics", metrics_action),
    "12": ("Show a ticket's history", history_action),
    "13": ("Engineering Knowledge Lab", knowledge_lab_action),
}

EXIT_KEY = "0"


def show_menu(say):
    """Display available menu actions."""
    say("")
    say("=== CampusFlow ===")

    for key, (label, _action) in ACTIONS.items():
        say(f"{key}. {label}")

    say(f"{EXIT_KEY}. Exit")


def run(path=DEFAULT_PATH, ask=input, say=print, clock=utc_now):
    """Load the tickets and the event history, run the menu, and return an exit code."""
    try:
        tickets, events = load_data(path)
    except (ValueError, OSError) as error:
        say(f"Cannot start: {error}")
        say("Fix or move the data file and try again. Nothing was changed.")
        return 1

    ctx = Context(tickets=tickets, events=events)

    try:
        ctx.actor = ask_until_valid(
            ask,
            say,
            "Your name (recorded in the history): ",
            clean_actor,
        )

        while True:
            show_menu(say)
            choice = ask("Choose an option: ").strip()

            if choice == EXIT_KEY:
                break

            if choice not in ACTIONS:
                say("Please choose a number from the menu.")
                continue

            _label, action = ACTIONS[choice]
            ctx.now = clock()

            try:
                changed = action(ctx, ask, say)
            except ValueError as error:
                say(f"Error: {error}")
                continue

            if changed:
                try:
                    save_data(path, ctx.tickets, ctx.events)
                except (OSError, ValueError) as error:
                    say(
                        "WARNING: the change could not be saved: "
                        f"{error}"
                    )

    except (EOFError, KeyboardInterrupt):
        say("")

    say("Goodbye.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
