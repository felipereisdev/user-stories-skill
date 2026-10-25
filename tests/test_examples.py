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


def load(name):
    text = (ROOT / name).read_text(encoding="utf-8")
    return text, {s.data["id"]: s.data for s in parse_plan(text).stories}


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


if __name__ == "__main__":
    unittest.main()
