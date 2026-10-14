"""The Engineering Knowledge Lab: ten scenario questions, explanations and a saved session.

Nothing here receives tickets or events, so running the quiz cannot change them.
"""

import json
import os
from datetime import datetime, timezone

PARTICIPANTS = ("A", "B")
LETTERS = ("A", "B", "C", "D")
MIN_EXPLANATION_WORDS = 3
# Explanations that cannot be skipped: the boundary, the invariant and idempotency.
REQUIRED_EXPLANATIONS = ("Q1", "Q3", "Q5")

QUESTIONS = [
    {
        "id": "Q1", "topic": "overdue boundary", "answer": "B",
        "text": "Critical SLA: A critical ticket is created at 10:00 UTC. "
                "At 11:00 UTC, is it overdue?",
        "options": {"A": "Yes", "B": "No, only strictly after 11:00",
                    "C": "Only if assigned", "D": "Only if reopened"},
        "explain": "Explain the difference between 'due' and 'overdue'.",
    },
    {
        "id": "Q2", "topic": "priority rule order", "answer": "B",
        "text": "Priority order: urgency=low and affected_users=10. What priority?",
        "options": {"A": "Critical", "B": "High", "C": "Medium", "D": "Low"},
        "explain": "Explain which rule applies first.",
    },
    {
        "id": "Q3", "topic": "rejected changes and invariants", "answer": "C",
        "text": "Illegal transition: an unassigned open ticket moves directly to "
                "in_progress. What should happen?",
        "options": {"A": "Transition succeeds", "B": "Status changes but history stays",
                    "C": "Reject without changing ticket or events", "D": "Delete the ticket"},
        "explain": "Explain the invariant.",
    },
    {
        "id": "Q4", "topic": "reopening starts a new SLA cycle", "answer": "B",
        "text": "Reopening: a resolved high-priority ticket is reopened. "
                "Which SLA behavior is correct?",
        "options": {"A": "Keep old due_at always",
                    "B": "Start a fresh SLA cycle while preserving created_at",
                    "C": "Reset created_at to today's date", "D": "Delete previous events"},
        "explain": "Explain why.",
    },
    {
        "id": "Q5", "topic": "idempotent escalation", "answer": "C",
        "text": "Escalation repeated: an overdue ticket is checked three times within "
                "one SLA cycle. How many new ESCALATE events?",
        "options": {"A": "Three", "B": "Two", "C": "One", "D": "Zero"},
        "explain": "Explain idempotency.",
    },
    {
        "id": "Q6", "topic": "safe JSON loading", "answer": "D",
        "text": "JSON corrupted: the saved file has invalid JSON. What is the safest action?",
        "options": {"A": "Replace data with empty list", "B": "Use eval()",
                    "C": "Ignore and keep running with partial data",
                    "D": "Reject load and preserve existing valid state"},
        "explain": "Explain your choice.",
    },
    {
        "id": "Q7", "topic": "code review and boundary tests", "answer": "B",
        "text": "Code review: a PR changes SLA calculations but adds no boundary tests. "
                "What should a reviewer do?",
        "options": {"A": "Approve because it runs locally",
                    "B": "Request focused tests and explanation",
                    "C": "Merge and test next week", "D": "Ask AI to approve automatically"},
        "explain": "Explain your reasoning.",
    },
    {
        "id": "Q8", "topic": "verifying AI suggestions", "answer": "C",
        "text": "AI suggestion: an assistant says 'use eval() to parse stored JSON'. "
                "What should you do?",
        "options": {"A": "Copy it", "B": "Disable tests",
                    "C": "Reject and use JSON parsing with validation",
                    "D": "Share the whole file publicly"},
        "explain": "Explain how you verified.",
    },
    {
        "id": "Q9", "topic": "duplicate warning versus blocking", "answer": "B",
        "text": "Duplicate warning: titles ' Wi-Fi   Down ' and 'wi-fi down' share "
                "category, both unresolved. What should the CLI do?",
        "options": {"A": "Silently delete original", "B": "Warn and require confirmation",
                    "C": "Silently block forever", "D": "Ignore normalization"},
        "explain": "Explain the trade-off.",
    },
    {
        "id": "Q10", "topic": "append-only audit log", "answer": "D",
        "text": "Audit log: an invalid return/status operation is rejected. "
                "What should happen to event count?",
        "options": {"A": "Increase by one", "B": "Increase twice",
                    "C": "Reset to zero", "D": "Stay unchanged"},
        "explain": "Explain the reason.",
    },
]


def clean_participant(text):
    """Return 'A' or 'B' (letter case and outer spaces forgiven). Raise ValueError otherwise."""
    participant = text.strip().upper()
    if participant not in PARTICIPANTS:
        raise ValueError("Participant must be A or B")
    return participant


def clean_choice(text):
    """Return the answer only if it is exactly A, B, C or D. No forgiveness here."""
    if text not in LETTERS:
        raise ValueError("Please type exactly A, B, C or D (capital letter)")
    return text


def score_choices(choices):
    """Return (score, revision_topics). Pure: it looks only at the choices.

    A missing answer counts as wrong. Topics appear once each, in question order.
    """
    score = 0
    topics = []
    for question in QUESTIONS:
        if choices.get(question["id"]) == question["answer"]:
            score += 1
        elif question["topic"] not in topics:
            topics.append(question["topic"])
    return score, topics


def clean_explanation(text, required):
    """Return the explanation without outer spaces.

    A required explanation must have at least MIN_EXPLANATION_WORDS words,
    so a blank or a single character cannot satisfy it.
    """
    text = text.strip()
    if required and len(text.split()) < MIN_EXPLANATION_WORDS:
        raise ValueError(
            f"This explanation is required: please write at least {MIN_EXPLANATION_WORDS} words"
        )
    return text


def session_path_for(folder, participant, now):
    """Return a file path for this session, e.g. knowledge_session_B_20261014T100000Z.json."""
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return os.path.join(folder, f"knowledge_session_{participant}_{stamp}.json")


def save_session(path, record):
    """Write the session record as JSON, via a side file so a crash cannot leave half a file."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(record, file, indent=2)
    os.replace(temp_path, path)


def ask_until_valid(ask, say, prompt, cleaner):
    """Keep asking until the cleaner accepts the answer, then return the clean value."""
    while True:
        try:
            return cleaner(ask(prompt))
        except ValueError as error:
            say(f"Error: {error}")


def run_quiz(ask, say, participant, session_path, now):
    """Run the quiz, show the results, save the session and return the session record."""
    if participant not in PARTICIPANTS:
        raise ValueError("Participant must be A or B")
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("Time must be a timezone-aware datetime")

    say(f"Engineering Knowledge Lab - participant {participant}")
    choices = {}
    explanations = {}
    for number, question in enumerate(QUESTIONS, start=1):
        say("")
        say(f"Question {number}/{len(QUESTIONS)}: {question['text']}")
        for letter in LETTERS:
            say(f"  {letter}. {question['options'][letter]}")
        choices[question["id"]] = ask_until_valid(
            ask, say, "Your answer (A/B/C/D): ", clean_choice
        )

        required = question["id"] in REQUIRED_EXPLANATIONS
        note = "required" if required else "optional, press Enter to skip"
        text = ask_until_valid(
            ask, say, f"{question['explain']} (1-2 sentences, {note}): ",
            lambda answer, required=required: clean_explanation(answer, required),
        )
        if text:
            explanations[question["id"]] = text

    score, topics = score_choices(choices)
    say("")
    say(f"Score: {score}/{len(QUESTIONS)}")
    if topics:
        say("Topics to revise:")
        for topic in topics:
            say(f"  - {topic}")
    else:
        say("No topics to revise. Well done!")
    say("Your answers:")
    for question in QUESTIONS:
        letter = choices[question["id"]]
        verdict = "correct" if letter == question["answer"] else (
            f"wrong (correct answer: {question['answer']})")
        say(f"  {question['id']}: {letter} - {verdict}")
    say("Your explanations:")
    for question in QUESTIONS:
        if question["id"] in explanations:
            say(f"  {question['id']}: {explanations[question['id']]}")

    record = {
        "participant": participant,
        "timestamp": now.astimezone(timezone.utc).isoformat(),
        "score": score,
        "total": len(QUESTIONS),
        "choices": choices,
        "explanations": explanations,
        "revision_topics": topics,
    }
    try:
        save_session(session_path, record)
        say(f"Session saved to {session_path}")
    except OSError as error:
        say(f"WARNING: the session could not be saved: {error}")
    return record
