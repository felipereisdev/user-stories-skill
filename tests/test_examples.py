"""Checks the example plans against the Schema v2 rules the linter leaves to the checklist.

Standard library only: python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lint_plan import parse_plan  # noqa: E402

EXAMPLES = ("example-output.md", "example-gherkin-output.md")
NPM_LS = re.compile(r"^npm ls \S+")
GATE = {"kind": "happy", "text": "Typecheck and tests pass", "verify": "npx tsc --noEmit && npm test"}
MINIMUM = {"XS": 3, "S": 3, "M": 4, "L": 5}
STEP = re.compile(r"^\s+(Given|When|Then|And|But)\s")
LITERAL = re.compile(r"`[^`]*`|\"[^\"]*\"")


def load(name):
    text = (ROOT / name).read_text(encoding="utf-8")
    return text, {s.data["id"]: s.data for s in parse_plan(text).stories}


def vague_words():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    words = []
    for m in re.finditer(r"^\s*- (?:English|Portuguese) vague words: (.+)$", skill, re.M):
        words += re.findall(r"`([^`]+)`", m.group(1))
    return words


def vague_in(text, words):
    plain = LITERAL.sub(" ", text)
    return [w for w in dict.fromkeys(words) if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", plain, re.I)]


def section(text, title):
    m = re.search(rf"^## {title}\n(.*?)(?=^## )", text, re.S | re.M)
    return m.group(1).strip()


class ExampleCoherenceTests(unittest.TestCase):
    def test_every_consumes_is_produced_by_a_dependency(self):
        for name in EXAMPLES:
            _, stories = load(name)
            for sid, story in stories.items():
                produced = {p for d in story["dependencies"] for p in stories[d["id"]]["interfaces"]["produces"]}
                for item in story["interfaces"]["consumes"]:
                    with self.subTest(example=name, story=sid, consumes=item):
                        self.assertIn(item, produced)

    def test_register_consumes_the_email_lookup_its_409_needs(self):
        for name in EXAMPLES:
            _, stories = load(name)
            with self.subTest(example=name):
                self.assertIn("User.findByEmail()", stories["US-002"]["interfaces"]["consumes"])

    def test_package_install_touches_the_npm_manifest_and_lockfile(self):
        for name in EXAMPLES:
            _, stories = load(name)
            for sid, story in stories.items():
                if any(NPM_LS.match(c["verify"]) for c in story["acceptanceCriteria"]):
                    with self.subTest(example=name, story=sid):
                        self.assertIn("package.json", story["filesToTouch"])
                        self.assertIn("package-lock.json", story["filesToTouch"])

    def test_assumptions_and_open_questions_name_stories_by_id(self):
        for name in EXAMPLES:
            text, stories = load(name)
            for title in ("Assumptions", "Open Questions"):
                body = section(text, title)
                with self.subTest(example=name, section=title):
                    self.assertEqual(re.findall(r"\bFeature \d+", body), [])
                    for sid in re.findall(r"\bUS-\d{3}\b", body):
                        self.assertIn(sid, stories)

    def test_assumptions_and_open_questions_match_between_formats(self):
        json_text, _ = load(EXAMPLES[0])
        gherkin_text, _ = load(EXAMPLES[1])
        for title in ("Assumptions", "Open Questions"):
            with self.subTest(section=title):
                self.assertEqual(section(gherkin_text, title), section(json_text, title))


class AcceptanceCriteriaRuleTests(unittest.TestCase):
    def test_skill_md_lists_vague_words_in_both_languages(self):
        words = vague_words()
        for word in ("appropriate", "fast", "etc.", "and so on", "adequado", "rápido", "conforme esperado"):
            with self.subTest(word=word):
                self.assertIn(word, words)

    def test_literal_values_are_not_vague(self):
        words = vague_words()
        self.assertEqual(vague_in("Search is FAST, etc.", words), ["fast", "etc."])
        self.assertEqual(vague_in("Header `Authorization: Basic x` is sent", words), [])
        self.assertEqual(vague_in('Cookie flag "Secure" is set', words), [])
        self.assertEqual(vague_in("Breakfast for someone", words), [])


if __name__ == "__main__":
    unittest.main()
