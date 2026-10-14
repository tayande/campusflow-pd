import copy
import inspect
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone

from campusflow.knowledge_lab import (
    QUESTIONS,
    REQUIRED_EXPLANATIONS,
    clean_choice,
    clean_participant,
    run_quiz,
    score_choices,
    session_path_for,
)

NOW = datetime(2026, 10, 14, 10, 0, tzinfo=timezone.utc)
CORRECT = {question["id"]: question["answer"] for question in QUESTIONS}
GOOD_EXPLANATION = "because the rule says so"


def wrong_choices():
    """One wrong letter for every question."""
    return {qid: ("A" if letter != "A" else "B") for qid, letter in CORRECT.items()}


def script(choices, explanation=GOOD_EXPLANATION):
    """Typed answers for the whole quiz: a letter, then an explanation, for each question."""
    answers = []
    for question in QUESTIONS:
        answers.append(choices[question["id"]])
        answers.append(explanation)
    return answers


class QuizTestCase(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = os.path.join(self.folder.name, "session.json")
        self.output = []

    def play(self, answers, participant="B", path=None):
        remaining = list(answers)

        def fake_ask(prompt):
            if not remaining:
                raise EOFError
            return remaining.pop(0)

        return run_quiz(fake_ask, self.output.append, participant, path or self.path, NOW)

    def text(self):
        return "\n".join(self.output)

    def saved(self):
        with open(self.path, encoding="utf-8") as file:
            return json.load(file)


class TestQuestionBank(unittest.TestCase):
    def test_ten_questions_with_ids_q1_to_q10(self):
        self.assertEqual([q["id"] for q in QUESTIONS], [f"Q{n}" for n in range(1, 11)])

    def test_every_question_has_four_options_a_to_d_and_a_valid_answer(self):
        for question in QUESTIONS:
            self.assertEqual(sorted(question["options"]), ["A", "B", "C", "D"])
            self.assertIn(question["answer"], question["options"])
            self.assertTrue(question["topic"].strip())
            self.assertTrue(question["explain"].strip())

    def test_answer_key_is_the_agreed_one(self):
        self.assertEqual("".join(q["answer"] for q in QUESTIONS), "BBCBCDBCBD")

    def test_required_explanations_are_at_least_three_real_questions(self):
        ids = [q["id"] for q in QUESTIONS]
        self.assertGreaterEqual(len(REQUIRED_EXPLANATIONS), 3)
        for qid in REQUIRED_EXPLANATIONS:
            self.assertIn(qid, ids)


class TestPureFunctions(unittest.TestCase):
    def test_perfect_choices_score_ten_with_no_topics(self):
        self.assertEqual(score_choices(CORRECT), (10, []))

    def test_all_wrong_choices_score_zero_with_every_topic_once(self):
        score, topics = score_choices(wrong_choices())
        self.assertEqual(score, 0)
        self.assertEqual(topics, [q["topic"] for q in QUESTIONS])

    def test_one_wrong_answer_costs_one_point_and_names_its_topic(self):
        choices = dict(CORRECT, Q5="A")
        self.assertEqual(score_choices(choices), (9, ["idempotent escalation"]))

    def test_a_missing_answer_counts_as_wrong(self):
        choices = dict(CORRECT)
        del choices["Q1"]
        self.assertEqual(score_choices(choices), (9, ["overdue boundary"]))

    def test_scoring_does_not_change_its_input(self):
        choices = dict(CORRECT, Q2="C")
        before = dict(choices)
        score_choices(choices)
        self.assertEqual(choices, before)

    def test_only_exact_capital_letters_are_valid_choices(self):
        for good in ["A", "B", "C", "D"]:
            self.assertEqual(clean_choice(good), good)
        for bad in ["E", "", " ", "a", " A", "A ", "AB", "1", None]:
            with self.assertRaises(ValueError):
                clean_choice(bad)

    def test_participant_must_be_a_or_b(self):
        self.assertEqual(clean_participant(" b "), "B")
        for bad in ["", "C", "AB", "x"]:
            with self.assertRaises(ValueError):
                clean_participant(bad)

    def test_session_file_name_uses_participant_and_utc_time(self):
        path = session_path_for("data", "B", NOW)
        self.assertEqual(os.path.basename(path), "knowledge_session_B_20261014T100000Z.json")


class TestRunQuiz(QuizTestCase):
    def test_invalid_answers_are_asked_again_until_exact(self):
        answers = ["E", "", "a", " B", "B", GOOD_EXPLANATION] + script(CORRECT)[2:]
        record = self.play(answers)
        self.assertEqual(record["choices"]["Q1"], "B")
        self.assertEqual(self.text().count("Error: Please type exactly A, B, C or D"), 4)
        self.assertEqual(record["score"], 10)

    def test_perfect_run_scores_ten_and_shows_no_revision_topics(self):
        record = self.play(script(CORRECT))
        self.assertEqual(record["score"], 10)
        self.assertEqual(record["revision_topics"], [])
        self.assertIn("Score: 10/10", self.output)
        self.assertIn("No topics to revise. Well done!", self.output)

    def test_all_wrong_run_scores_zero_and_lists_every_topic(self):
        record = self.play(script(wrong_choices()))
        self.assertEqual(record["score"], 0)
        self.assertIn("Score: 0/10", self.output)
        for question in QUESTIONS:
            self.assertIn(f"  - {question['topic']}", self.output)

    def test_results_show_answers_with_verdicts_and_the_explanations(self):
        self.play(script(dict(CORRECT, Q2="C")))
        self.assertIn("  Q1: B - correct", self.output)
        self.assertIn("  Q2: C - wrong (correct answer: B)", self.output)
        self.assertIn(f"  Q3: {GOOD_EXPLANATION}", self.output)

    def test_session_file_holds_participant_time_choices_score_and_explanations(self):
        self.play(script(dict(CORRECT, Q4="A")), participant="A")
        saved = self.saved()
        self.assertEqual(saved["participant"], "A")
        self.assertEqual(saved["timestamp"], "2026-10-14T10:00:00+00:00")
        self.assertEqual(saved["score"], 9)
        self.assertEqual(saved["total"], 10)
        self.assertEqual(saved["choices"], dict(CORRECT, Q4="A"))
        self.assertEqual(saved["explanations"]["Q1"], GOOD_EXPLANATION)
        self.assertEqual(saved["revision_topics"], ["reopening starts a new SLA cycle"])
        self.assertFalse(os.path.exists(self.path + ".tmp"))

    def test_wrong_participant_is_rejected_before_anything_happens(self):
        for bad in ["C", "", "a", None]:
            with self.assertRaises(ValueError):
                self.play(script(CORRECT), participant=bad)
        self.assertFalse(os.path.exists(self.path))
        self.assertEqual(self.output, [])

    def test_naive_time_is_rejected(self):
        with self.assertRaises(ValueError):
            run_quiz(lambda prompt: "A", self.output.append, "A", self.path,
                     datetime(2026, 10, 14, 10, 0))
        self.assertFalse(os.path.exists(self.path))

    def test_required_explanation_cannot_be_blank_or_too_short(self):
        # Q1 is required: blank, spaces and a single word are all refused.
        answers = ["B", "", "   ", "ok", GOOD_EXPLANATION] + script(CORRECT)[2:]
        record = self.play(answers)
        self.assertEqual(self.text().count("Error: This explanation is required"), 3)
        self.assertEqual(record["explanations"]["Q1"], GOOD_EXPLANATION)

    def test_optional_explanation_can_be_skipped_and_is_not_stored(self):
        answers = []
        for question in QUESTIONS:
            answers.append(question["answer"])
            answers.append(GOOD_EXPLANATION if question["id"] in REQUIRED_EXPLANATIONS else "")
        record = self.play(answers)
        self.assertEqual(sorted(record["explanations"]), sorted(REQUIRED_EXPLANATIONS))
        self.assertEqual(record["score"], 10)

    def test_score_comes_from_choices_only_not_from_explanations(self):
        record = self.play(script(wrong_choices(), explanation="a long and thoughtful explanation"))
        self.assertEqual(record["score"], 0)

    def test_quiz_cannot_touch_tickets_or_events(self):
        parameters = list(inspect.signature(run_quiz).parameters)
        self.assertEqual(parameters, ["ask", "say", "participant", "session_path", "now"])
        tickets = [{"id": "T001", "status": "open"}]
        events = [{"event_id": "E001"}]
        before = copy.deepcopy((tickets, events))
        self.play(script(CORRECT))
        self.assertEqual((tickets, events), before)

    def test_unwritable_session_path_warns_but_does_not_crash(self):
        blocker = os.path.join(self.folder.name, "blocker")
        with open(blocker, "w", encoding="utf-8") as file:
            file.write("a file, not a folder")
        record = self.play(script(CORRECT), path=os.path.join(blocker, "session.json"))
        self.assertEqual(record["score"], 10)
        self.assertIn("WARNING: the session could not be saved", self.text())

    def test_running_out_of_input_midway_saves_nothing(self):
        with self.assertRaises(EOFError):
            self.play(script(CORRECT)[:7])
        self.assertFalse(os.path.exists(self.path))

    def test_session_file_is_replaced_not_appended_on_a_second_run(self):
        self.play(script(CORRECT))
        self.play(script(wrong_choices()))
        self.assertEqual(self.saved()["score"], 0)


if __name__ == "__main__":
    unittest.main()
