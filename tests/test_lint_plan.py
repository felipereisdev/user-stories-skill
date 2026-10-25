"""Tests for scripts/lint_plan.py (standard library only: python3 -m unittest discover -s tests -v)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import lint_plan  # noqa: E402
from lint_plan import lint_text, parse_plan  # noqa: E402

JSON_EXAMPLE = (ROOT / "example-output.md").read_text(encoding="utf-8")
GHERKIN_EXAMPLE = (ROOT / "example-gherkin-output.md").read_text(encoding="utf-8")
JSON_BLOCK = re.compile(r"```json\n(.*?)\n```", re.S)


def rules(problems):
    return [p.rule for p in problems]


def messages(problems, rule):
    return [p.message for p in problems if p.rule == rule]


def json_plan(mutate):
    m = JSON_BLOCK.search(JSON_EXAMPLE)
    stories = json.loads(m.group(1))
    mutate(stories)
    return JSON_EXAMPLE[: m.start(1)] + json.dumps(stories, indent=2) + JSON_EXAMPLE[m.end(1):]


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "lint_plan.py"), *args],
        capture_output=True, text=True, cwd=ROOT,
    )


def line_containing(text, needle):
    for n, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return n
    raise AssertionError(f"{needle!r} not found")


def write_temp(test, text, name="plan.md", newline=None):
    d = tempfile.TemporaryDirectory()
    test.addCleanup(d.cleanup)
    path = Path(d.name) / name
    with open(path, "w", encoding="utf-8", newline=newline) as f:
        f.write(text)
    return str(path)


def gherkin(test, old, new):
    text = GHERKIN_EXAMPLE.replace(old, new, 1)
    test.assertNotEqual(text, GHERKIN_EXAMPLE)
    return text


class HeaderAndParsingTests(unittest.TestCase):
    def test_examples_have_no_problems(self):
        self.assertEqual(lint_text(JSON_EXAMPLE, new=True), [])
        self.assertEqual(lint_text(GHERKIN_EXAMPLE, new=True), [])

    def test_json_example_parses_six_stories(self):
        p = parse_plan(JSON_EXAMPLE)
        self.assertEqual(p.format, "json")
        self.assertEqual(len(p.stories), 6)
        self.assertEqual(p.stories[0].data["id"], "US-001")
        self.assertEqual(p.stories[5].line, line_containing(JSON_EXAMPLE, '    "id": "US-006"'))

    def test_missing_schema_header(self):
        probs = lint_text(JSON_EXAMPLE.replace("**Schema**: v2", "**Schema**: v1"))
        self.assertIn("header", rules(probs))
        self.assertIn("missing '**Schema**: v2' header line", messages(probs, "header"))

    def test_missing_assumptions_section(self):
        probs = lint_text(JSON_EXAMPLE.replace("## Assumptions", "## Notes"))
        self.assertIn("missing '## Assumptions' section", messages(probs, "sections"))

    def test_empty_assumptions_section(self):
        start = JSON_EXAMPLE.index("## Assumptions\n") + len("## Assumptions\n")
        end = JSON_EXAMPLE.index("## Open Questions")
        probs = lint_text(JSON_EXAMPLE[:start] + "\n" + JSON_EXAMPLE[end:])
        self.assertIn("'## Assumptions' section is empty", messages(probs, "sections"))

    def test_missing_open_questions_section(self):
        probs = lint_text(JSON_EXAMPLE.replace("## Open Questions", "## Questions"))
        self.assertIn("missing '## Open Questions' section", messages(probs, "sections"))

    def test_no_json_block(self):
        probs = lint_text(JSON_EXAMPLE.replace("```json", "```text"))
        self.assertEqual(messages(probs, "stories-block"), ["no json block with the stories"])

    def test_two_json_blocks(self):
        m = JSON_BLOCK.search(JSON_EXAMPLE)
        text = JSON_EXAMPLE + "\n" + m.group(0) + "\n"
        probs = lint_text(text)
        self.assertEqual(messages(probs, "stories-block"), ["found 2 json blocks; expected exactly 1"])

    def test_invalid_json_reports_file_line(self):
        text = JSON_EXAMPLE.replace('"notes": "Simple route', '"notes": Simple route')
        probs = [p for p in lint_text(text) if p.rule == "stories-block"]
        self.assertEqual(len(probs), 1)
        self.assertTrue(probs[0].message.startswith("invalid JSON:"))
        self.assertEqual(probs[0].line, line_containing(text, '"notes": Simple route'))

    def test_json_not_array_of_objects(self):
        for body in ("[1, 2]", "{}"):
            text = JSON_BLOCK.sub("```json\n" + body + "\n```", JSON_EXAMPLE)
            self.assertEqual(messages(lint_text(text), "stories-block"),
                             ["the stories block must be a JSON array of objects"])

    def test_json_empty_array(self):
        text = JSON_BLOCK.sub("```json\n[]\n```", JSON_EXAMPLE)
        self.assertEqual(messages(lint_text(text), "stories-block"), ["the stories array is empty"])

    def test_crlf_and_bom_are_accepted(self):
        path = write_temp(self, "﻿" + JSON_EXAMPLE.replace("\n", "\r\n"), newline="")
        r = run_cli("--new", "--skip-files", path)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class CliTests(unittest.TestCase):
    def test_cli_ok_line_and_exit_0(self):
        r = run_cli("--skip-files", "example-output.md")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK example-output.md: 6 stories (json)", r.stdout)

    def test_cli_problem_line_format_and_exit_1(self):
        path = write_temp(self, JSON_EXAMPLE.replace("**Schema**: v2", "**Schema**: v1"))
        r = run_cli("--skip-files", path)
        self.assertEqual(r.returncode, 1)
        lines = r.stdout.splitlines()
        self.assertTrue(any(re.match(r"^.+:\d+: plan: header: missing '\*\*Schema\*\*: v2' header line$", l)
                            for l in lines), r.stdout)
        self.assertEqual(lines[-1], f"{path}: 1 problem(s)")

    def test_unreadable_file_exits_2_and_others_still_linted(self):
        r = run_cli("--skip-files", "nope.md", "example-output.md")
        self.assertEqual(r.returncode, 2)
        self.assertIn("lint_plan: cannot read nope.md", r.stderr)
        self.assertIn("OK example-output.md", r.stdout)
        self.assertNotIn("Traceback", r.stderr)

    def test_skip_files_and_root_are_exclusive(self):
        r = run_cli("--skip-files", "--root", ".", "example-output.md")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)


class StoryRuleTests(unittest.TestCase):
    def lint(self, mutate, new=False):
        return lint_text(json_plan(mutate), new=new)

    def test_missing_field(self):
        probs = self.lint(lambda s: s[5].pop("independentTest"))
        self.assertIn("missing field 'independentTest'", messages(probs, "fields"))

    def test_unknown_field(self):
        probs = self.lint(lambda s: s[0].update(epic="x"))
        self.assertIn("unknown field 'epic'", messages(probs, "fields"))

    def test_fields_out_of_order(self):
        def m(s):
            d = s[0]
            keys = ["id", "title", "type"] + [k for k in d if k not in ("id", "title", "type")]
            s[0] = {k: d[k] for k in keys}
        probs = self.lint(m)
        self.assertEqual(messages(probs, "fields"),
                         ["fields out of order: expected 'type' at position 2, found 'title'"])

    def test_bad_enum_type(self):
        probs = self.lint(lambda s: s[0].update(type="epic"))
        self.assertIn("'type' must be one of feature, enabler, bug, spike; got 'epic'", messages(probs, "field-type"))

    def test_complexity_xl(self):
        probs = self.lint(lambda s: s[0].update(complexity="XL"))
        self.assertIn("'complexity' is XL: break the story down (allowed: XS, S, M, L)",
                      messages(probs, "field-type"))

    def test_priority_string(self):
        probs = self.lint(lambda s: s[5].update(priority="6"))
        self.assertIn("'priority' must be an integer, got '6'", messages(probs, "field-type"))

    def test_priority_bool_is_rejected(self):
        probs = self.lint(lambda s: s[0].update(priority=True))
        self.assertTrue(any(m.startswith("'priority' must be an integer") for m in messages(probs, "field-type")))

    def test_priority_not_a_permutation(self):
        probs = self.lint(lambda s: s[1].update(priority=1))
        prio = [p for p in probs if p.rule == "priority"]
        self.assertEqual(len(prio), 1)
        self.assertEqual(prio[0].story, "plan")
        self.assertEqual(prio[0].message, "priorities must be 1..6 with each number once; missing [2], repeated [1]")

    def test_id_format(self):
        probs = self.lint(lambda s: s[0].update(id="US-1"))
        self.assertIn("id 'US-1' must look like US-001", messages(probs, "id-format"))

    def test_duplicate_id(self):
        text = json_plan(lambda s: s[2].update(id="US-002"))
        probs = lint_text(text)
        first = line_containing(text, '    "id": "US-002"')
        self.assertIn(f"duplicate id US-002 (also at line {first})", messages(probs, "id-unique"))
        self.assertIn("id US-002 is story 3 in the plan; expected US-003", messages(probs, "id-sequence"))

    def test_criterion_shape(self):
        probs = self.lint(lambda s: s[0]["acceptanceCriteria"][1].pop("verify"))
        self.assertIn("acceptance criterion 2: missing 'verify'", messages(probs, "criteria"))
        probs = self.lint(lambda s: s[0]["acceptanceCriteria"][0].update(kind="sad"))
        self.assertIn("acceptance criterion 1: 'kind' must be one of happy, edge, error; got 'sad'",
                      messages(probs, "criteria"))
        probs = self.lint(lambda s: s[0]["acceptanceCriteria"][2].update(verify=""))
        self.assertIn("acceptance criterion 3: 'verify' must be a non-empty string", messages(probs, "criteria"))

    def test_empty_criteria_list(self):
        probs = self.lint(lambda s: s[0].update(acceptanceCriteria=[]))
        self.assertIn("field-type", rules(probs))

    def test_no_happy(self):
        probs = self.lint(lambda s: s[5]["acceptanceCriteria"][0].update(kind="edge"))
        p = [p for p in probs if p.rule == "criteria-min"]
        self.assertEqual([x.message for x in p], ["no 'happy' acceptance criterion"])
        self.assertEqual(p[0].story, "US-006")

    def test_feature_without_edge_or_error(self):
        def m(type_):
            def f(s):
                s[5]["acceptanceCriteria"][1]["kind"] = "happy"
                s[5]["type"] = type_
            return f
        self.assertIn("a feature needs at least one 'edge' or 'error' criterion",
                      messages(self.lint(m("feature")), "criteria-min"))
        self.assertIn("a bug needs at least one 'edge' or 'error' criterion",
                      messages(self.lint(m("bug")), "criteria-min"))
        self.assertEqual(messages(self.lint(m("enabler")), "criteria-min"), [])

    def test_empty_files_only_for_spike(self):
        probs = self.lint(lambda s: s[5].update(filesToTouch=[]))
        self.assertIn("only a spike may have an empty 'filesToTouch'", messages(probs, "spike"))
        probs = self.lint(lambda s: s[5].update(filesToTouch=[], type="spike"))
        self.assertEqual(messages(probs, "spike"), [])

    def test_spike_at_most_m(self):
        probs = self.lint(lambda s: s[5].update(type="spike", complexity="L"))
        self.assertIn("a spike must be at most M, got L", messages(probs, "spike"))

    def test_new_plan_flag(self):
        text = json_plan(lambda s: s[0].update(status="done"))
        self.assertIn("a new plan must have status 'todo', got 'done'", messages(lint_text(text, new=True), "new-plan"))
        self.assertEqual(lint_text(text, new=False), [])
        text = json_plan(lambda s: s[0].update(passes=True))
        self.assertIn("a new plan must have passes false, got true", messages(lint_text(text, new=True), "new-plan"))
        text = json_plan(lambda s: s[0].update(status="doing"))
        self.assertIn("field-type", rules(lint_text(text)))

    def test_problem_line_is_story_id_line(self):
        text = json_plan(lambda s: s[5]["acceptanceCriteria"][0].update(kind="edge"))
        p = [p for p in lint_text(text) if p.rule == "criteria-min"][0]
        self.assertEqual(p.line, line_containing(text, '    "id": "US-006"'))

    def test_malformed_values_never_crash(self):
        for field in lint_plan.SCHEMA_FIELDS:
            for value in (None, {"x": 1}):
                with self.subTest(field=field, value=value):
                    probs = self.lint(lambda s: s[1].update({field: value}))
                    self.assertTrue(probs)
        for field, value in (("acceptanceCriteria", ["texto"]), ("dependencies", "US-001")):
            with self.subTest(field=field):
                self.assertTrue(self.lint(lambda s: s[1].update({field: value})))


class GraphRuleTests(unittest.TestCase):
    def lint(self, mutate):
        return lint_text(json_plan(mutate))

    @staticmethod
    def dep(s, k, target, reason="x"):
        s[k - 1]["dependencies"].append({"id": target, "reason": reason})

    def test_dependency_missing(self):
        probs = self.lint(lambda s: s[5].update(dependencies=[{"id": "US-009", "reason": "x"}]))
        p = [p for p in probs if p.rule == "dependency-missing"]
        self.assertEqual([x.message for x in p], ["depends on US-009, which is not in the plan"])
        self.assertEqual(p[0].story, "US-006")

    def test_dependency_order(self):
        probs = self.lint(lambda s: self.dep(s, 2, "US-004"))
        self.assertIn("depends on US-004 (priority 4), which does not come earlier (this story's priority is 2)",
                      messages(probs, "dependency-order"))

    def test_dependency_duplicate(self):
        probs = self.lint(lambda s: self.dep(s, 4, "US-001"))
        self.assertIn("lists dependency US-001 more than once", messages(probs, "dependency-duplicate"))

    def test_cycle_two_nodes(self):
        def m(s):
            self.dep(s, 2, "US-004")
            self.dep(s, 4, "US-002")
        p = [p for p in self.lint(m) if p.rule == "dependency-cycle"]
        self.assertEqual([x.message for x in p], ["dependency cycle: US-002 -> US-004 -> US-002"])
        self.assertEqual(p[0].story, "US-002")

    def test_self_dependency_is_a_cycle(self):
        probs = self.lint(lambda s: self.dep(s, 3, "US-003"))
        self.assertIn("dependency cycle: US-003 -> US-003", messages(probs, "dependency-cycle"))

    def test_cycles_are_normalized_and_unique(self):
        def m(s):
            self.dep(s, 1, "US-003")
            self.dep(s, 3, "US-005")
        stories = json.loads(JSON_BLOCK.search(json_plan(m)).group(1))
        deps = {x["id"]: {d["id"] for d in x["dependencies"]} for x in stories}
        msgs = messages(self.lint(m), "dependency-cycle")
        self.assertTrue(msgs)
        self.assertEqual(len(msgs), len(set(msgs)))
        for msg in msgs:
            ids = msg[len("dependency cycle: "):].split(" -> ")
            self.assertEqual(ids[0], min(ids))
            self.assertEqual(ids[0], ids[-1])
            for a, b in zip(ids, ids[1:]):
                self.assertIn(b, deps[a])

    def test_conflicts_must_match_derived(self):
        probs = self.lint(lambda s: s[5]["filesToTouch"].append("src/routes/auth.routes.ts"))
        c = {p.story: p.message for p in probs if p.rule == "conflicts"}
        self.assertEqual(c["US-006"], "conflictsWith is [] but the stories that share a file in filesToTouch are "
                                      "[US-002, US-004]")
        self.assertIn("US-002", c)
        self.assertIn("US-004", c)

    def test_conflicts_glob_counts(self):
        probs = self.lint(lambda s: s[2]["filesToTouch"].append("prisma/migrations/001/migration.sql"))
        self.assertEqual(sorted(p.story for p in probs if p.rule == "conflicts"), ["US-001", "US-003"])

    def test_conflicts_sorted(self):
        def m(s):
            s[5]["filesToTouch"].append("src/routes/auth.routes.ts")
            s[5]["conflictsWith"] = ["US-004", "US-002"]
            s[5]["parallel"] = False
            s[1]["conflictsWith"] = ["US-004", "US-006"]
            s[3]["conflictsWith"] = ["US-002", "US-006"]
        probs = self.lint(m)
        self.assertEqual(messages(probs, "conflicts"), ["conflictsWith must be sorted by id"])

    def test_parallel_must_follow_conflicts(self):
        probs = self.lint(lambda s: s[0].update(parallel=False))
        self.assertIn("parallel must be true exactly when conflictsWith is []", messages(probs, "parallel"))

    def test_graph_ignores_malformed_values(self):
        def m(s):
            s[1]["dependencies"] = [{"id": 3, "reason": "x"}]
            s[2]["filesToTouch"] = "a.ts"
            s[3]["conflictsWith"] = None
        probs = self.lint(m)
        self.assertIn("field-type", rules(probs))

    def test_examples_have_no_graph_problems(self):
        self.assertEqual(lint_plan.check_graph(parse_plan(JSON_EXAMPLE)), [])


class GherkinTests(unittest.TestCase):
    def test_gherkin_example_matches_json_example(self):
        g = parse_plan(GHERKIN_EXAMPLE).stories
        j = parse_plan(JSON_EXAMPLE).stories
        self.assertEqual(len(g), 6)
        for a, b in zip(g, j):
            for f in ("id", "type", "priority", "complexity", "dependencies", "interfaces", "filesToTouch",
                      "leverage", "parallel", "conflictsWith", "source", "status", "passes"):
                self.assertEqual(a.data[f], b.data[f], (a.data["id"], f))

    def test_label_out_of_order(self):
        text = gherkin(self, "# Priority: 6\n# Complexity: XS", "# Complexity: XS\n# Priority: 6")
        probs = lint_text(text)
        g = [p for p in probs if p.rule == "gherkin"]
        self.assertEqual(g[0].story, "US-006")
        self.assertEqual(g[0].message, "expected '# Priority:' line, found '# Complexity: XS'")
        stories = parse_plan(text).stories
        self.assertEqual([s.data["id"] for s in stories], ["US-001", "US-002", "US-003", "US-004", "US-005"])
        self.assertEqual(rules(probs), ["gherkin"])

    def test_dropped_feature_in_middle_counts_only_read_stories(self):
        text = gherkin(self, "# Priority: 3\n# Complexity: S", "# Complexity: S\n# Priority: 3")
        self.assertEqual(len(parse_plan(text).stories), 5)
        probs = lint_text(text)
        self.assertIn("US-003", [p.story for p in probs if p.rule == "gherkin"])
        self.assertIn(("US-004", "id US-004 is story 3 in the plan; expected US-003"),
                      [(p.story, p.message) for p in probs if p.rule == "id-sequence"])
        self.assertIn(("plan", "priorities must be 1..5 with each number once; missing [3], repeated []"),
                      [(p.story, p.message) for p in probs if p.rule == "priority"])
        missing = [(p.story, p.message) for p in probs if p.rule == "dependency-missing"]
        self.assertIn(("US-004", "depends on US-003, which is not in the plan"), missing)
        self.assertIn(("US-005", "depends on US-003, which is not in the plan"), missing)

    def test_blank_line_between_labels(self):
        text = gherkin(self, "# ID: US-006\n", "# ID: US-006\n\n")
        self.assertIn("expected '# Type:' line, found ''", messages(lint_text(text), "gherkin"))

    def test_feature_must_follow_notes(self):
        text = gherkin(self, "\nFeature: Create user profile endpoint", "\n\nFeature: Create user profile endpoint")
        self.assertIn("the 'Feature:' line must come right after '# Notes:'", messages(lint_text(text), "gherkin"))

    def test_missing_tag(self):
        text = gherkin(self, "  @error\n  Scenario: Reject unauthenticated request",
                       "  Scenario: Reject unauthenticated request")
        self.assertIn("Scenario 'Reject unauthenticated request' must have a @happy, @edge or @error tag on the "
                      "line above", messages(lint_text(text), "gherkin"))

    def test_missing_verify(self):
        text = gherkin(self, "  # Verify: npm test -- users.me\n  @error\n", "  @error\n")
        self.assertIn("the tag above Scenario 'Reject unauthenticated request' must have a '# Verify: <check>' "
                      "line above it", messages(lint_text(text), "gherkin"))

    def test_missing_so_that(self):
        text = gherkin(self, "  So that I can confirm my information\n", "")
        self.assertIn("Feature description must have 'As a', 'I want' and 'So that' lines",
                      messages(lint_text(text), "gherkin"))

    def test_gherkin_dependency_missing_line(self):
        text = gherkin(self, "# Dependencies: US-005 (needs authMiddleware to populate req.user)",
                       "# Dependencies: US-009 (needs authMiddleware to populate req.user)")
        p = [p for p in lint_text(text) if p.rule == "dependency-missing"]
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].line, line_containing(text, "# Dependencies: US-009"))

    def test_dependency_reason_with_parentheses_and_semicolon(self):
        block = re.search(r"```gherkin\n(.*?)\n```", GHERKIN_EXAMPLE, re.S).group(1)
        block = block.replace("# Dependencies: none",
                              "# Dependencies: US-001 (needs User.findByEmail() to look up; then cache); "
                              "US-003 (needs generateToken())")
        story, _ = lint_plan.parse_gherkin_feature(block.splitlines(), 1)
        self.assertEqual(story.data["dependencies"], [
            {"id": "US-001", "reason": "needs User.findByEmail() to look up; then cache"},
            {"id": "US-003", "reason": "needs generateToken()"},
        ])

    def test_bad_dependency_item(self):
        text = gherkin(self, "# Dependencies: US-001 (needs User model)", "# Dependencies: US-001 needs model")
        self.assertIn("dependency 'US-001 needs model' must look like 'US-001 (reason)'",
                      messages(lint_text(text), "gherkin"))

    def test_gherkin_value_types(self):
        text = gherkin(self, "# Priority: 6\n", "# Priority: six\n")
        self.assertIn("'priority' must be an integer, got 'six'", messages(lint_text(text), "field-type"))
        text = gherkin(self, "# Parallel: true\n# Conflicts With: none\n# Source: inferred\n# Status: todo\n"
                             "# Passes: false\n# Notes: Simple",
                       "# Parallel: yes\n# Conflicts With: none\n# Source: inferred\n# Status: todo\n"
                       "# Passes: false\n# Notes: Simple")
        self.assertTrue(any(m.startswith("'parallel'") for m in messages(lint_text(text), "field-type")))

    def test_gherkin_duplicate_id(self):
        text = gherkin(self, "# ID: US-003", "# ID: US-002")
        self.assertIn("id-unique", rules(lint_text(text)))

    def test_no_gherkin_block(self):
        text = GHERKIN_EXAMPLE.replace("```gherkin", "```text")
        self.assertEqual(messages(lint_text(text), "stories-block"), ["no gherkin Feature block found"])


class FileRuleTests(unittest.TestCase):
    def make_root(self, dirs=("src", "prisma"), files=("src/config/database.ts", "src/validators/base.validator.ts")):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        root = Path(d.name)
        for x in dirs:
            (root / x).mkdir(parents=True, exist_ok=True)
        for f in files:
            (root / f).parent.mkdir(parents=True, exist_ok=True)
            (root / f).write_text("")
        return root

    def test_full_tree_passes(self):
        root = self.make_root()
        self.assertEqual(lint_text(JSON_EXAMPLE, root=root), [])
        self.assertEqual(lint_text(GHERKIN_EXAMPLE, root=root), [])

    def test_leverage_missing(self):
        root = self.make_root(files=())
        probs = lint_text(JSON_EXAMPLE, root=root)
        lev = {p.story: p.message for p in probs if p.rule == "leverage-missing"}
        self.assertEqual(lev["US-001"], f"leverage path 'src/config/database.ts' does not exist under {root}")
        self.assertIn("src/validators/base.validator.ts", lev["US-002"])
        self.assertNotIn("file-unanchored", rules(probs))

    def test_leverage_symbol_suffix_is_ignored(self):
        root = self.make_root()
        text = json_plan(lambda s: s[0].update(leverage=["src/config/database.ts#connect"]))
        self.assertEqual(lint_text(text, root=root), [])

    def test_unanchored_file(self):
        root = self.make_root(dirs=("src",))
        msgs = messages(lint_text(JSON_EXAMPLE, root=root), "file-unanchored")
        self.assertIn(f"filesToTouch path 'prisma/schema.prisma' does not exist and neither does its top-level "
                      f"directory 'prisma/' under {root}", msgs)
        self.assertTrue(any("'prisma/migrations/*/migration.sql'" in m for m in msgs))

    def test_new_file_under_existing_top_dir_is_anchored(self):
        root = self.make_root()
        self.assertFalse((root / "src/utils").exists())
        self.assertFalse((root / ".env.example").exists())
        self.assertEqual(lint_text(JSON_EXAMPLE, root=root), [])

    def test_glob_paths(self):
        root = self.make_root(files=("src/config/database.ts", "src/validators/base.validator.ts",
                                     "prisma/migrations/001/migration.sql"))
        self.assertEqual(lint_text(JSON_EXAMPLE, root=root), [])
        text = json_plan(lambda s: s[0]["filesToTouch"].append("db/*/x.sql"))
        msgs = messages(lint_text(text, root=root), "file-unanchored")
        self.assertEqual(len(msgs), 1)
        self.assertIn("'db/*/x.sql'", msgs[0])

    def test_path_outside_always_checked(self):
        for bad in ("../outside/jwt.ts", "/src/utils/jwt.ts"):
            text = json_plan(lambda s: s[2]["filesToTouch"].__setitem__(0, bad))
            probs = lint_text(text)
            self.assertIn(f"path '{bad}' in filesToTouch must be relative to the project root, without '..'",
                          messages(probs, "path-outside"))
            self.assertFalse({"leverage-missing", "file-unanchored"} & set(rules(probs)))

    def test_cli_root_and_skip_files(self):
        r = run_cli("--new", "example-output.md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("file-unanchored", r.stdout)
        self.assertEqual(run_cli("--new", "--skip-files", "example-output.md").returncode, 0)
        root = self.make_root()
        r = run_cli("--new", "--root", str(root), "example-output.md")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_root_not_a_directory_exits_2(self):
        r = run_cli("--root", "README.md", "example-output.md")
        self.assertEqual(r.returncode, 2)
        self.assertIn("is not a directory", r.stderr)
        self.assertNotIn("Traceback", r.stderr)


class ReviewRegressionTests(unittest.TestCase):
    def test_lone_surrogate_never_tracebacks(self):
        text = json_plan(lambda s: s[0].update(type="\ud800"))
        r = run_cli("--skip-files", write_temp(self, text))
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    @unittest.skipIf(os.name != "posix" or os.geteuid() == 0, "needs a non-root POSIX user")
    def test_disk_error_keeps_the_other_problems(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        root = Path(d.name)
        for x in ("src/config", "src/validators", "prisma", "locked"):
            (root / x).mkdir(parents=True)
        (root / "src/config/database.ts").write_text("")
        (root / "src/validators/base.validator.ts").write_text("")
        (root / "locked").chmod(0)
        self.addCleanup((root / "locked").chmod, 0o755)
        text = json_plan(lambda s: (s[0]["filesToTouch"].append("locked/inner/x.py"), s[1].update(type="nope")))
        probs = lint_text(text, root=root)
        self.assertIn("field-type", rules(probs))

    def test_story_without_id_does_not_shift_lines(self):
        text = json_plan(lambda s: (s[1].pop("id"), s[3].update(type="nope")))
        p = [p for p in lint_text(text) if p.rule == "field-type" and p.story == "US-004"][0]
        self.assertEqual(p.line, line_containing(text, '    "id": "US-004"'))

    def test_gherkin_non_ascii_digit_priority(self):
        text = gherkin(self, "# Priority: 6\n", "# Priority: \u00b2\n")
        self.assertIn("'priority' must be an integer, got '\u00b2'", messages(lint_text(text), "field-type"))


if __name__ == "__main__":
    unittest.main()
