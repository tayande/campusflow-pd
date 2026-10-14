
"""Duplicate-ticket detection for CampusFlow."""


def normalize_title(title):
    """Trim, collapse whitespace, and normalize title casing."""
    return " ".join(title.split()).casefold()


def detect_duplicates(tickets, category, title):
    """Return IDs of matching unresolved tickets, preserving list order."""
    wanted_title = normalize_title(title)
    wanted_category = category.strip().casefold()

    return [
        ticket["id"]
        for ticket in tickets
        if ticket["status"] != "resolved"
        and ticket["category"].strip().casefold() == wanted_category
        and normalize_title(ticket["title"]) == wanted_title
    ]
