#!/usr/bin/env python3
"""Deterministic linter for user-stories plans (schema v2, JSON or Gherkin).

Usage:
    python3 scripts/lint_plan.py [--new] [--root DIR | --skip-files] PLAN [PLAN ...]

Standard library only, Python 3.9 or newer. It reads the plan and nothing else:
it never writes, renames or deletes a file, and never runs a `verify` check.
Each problem is printed as `<file>:<line>: <US-00X|plan>: <rule>: <message>`.
Exit codes: 0 no problems, 1 rule problems, 2 usage or read error.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 9):
    sys.stderr.write("lint_plan: needs Python 3.9 or newer\n")
    sys.exit(2)

import argparse
import fnmatch
import glob
import json
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import List, Optional, Tuple

SCHEMA_FIELDS = (
    "id", "type", "title", "description", "independentTest", "acceptanceCriteria", "priority",
    "complexity", "dependencies", "interfaces", "filesToTouch", "leverage", "parallel",
    "conflictsWith", "source", "status", "passes", "notes",
)

GHERKIN_LABELS = (
    "ID", "Type", "Independent Test", "Priority", "Complexity", "Dependencies", "Consumes",
    "Produces", "Files", "Leverage", "Parallel", "Conflicts With", "Source", "Status", "Passes",
    "Notes",
)

# Field each Gherkin label feeds, for line numbers.
LABEL_FIELDS = {
    "ID": "id", "Type": "type", "Independent Test": "independentTest", "Priority": "priority",
    "Complexity": "complexity", "Dependencies": "dependencies", "Consumes": "interfaces",
    "Files": "filesToTouch", "Leverage": "leverage", "Parallel": "parallel",
    "Conflicts With": "conflictsWith", "Source": "source", "Status": "status", "Passes": "passes",
    "Notes": "notes",
}

TYPES = ("feature", "enabler", "bug", "spike")
COMPLEXITIES = ("XS", "S", "M", "L")
KINDS = ("happy", "edge", "error")
SOURCES = ("explicit", "inferred")
STATUSES = ("todo", "in_progress", "done", "blocked")
ID_RE = re.compile(r"^US-\d{3}$")
DEP_SPLIT_RE = re.compile(r";\s+(?=US-\d+\s*\()")
DEP_ITEM_RE = re.compile(r"^(US-\d+)\s*\((.*)\)$")
JSON_ID_RE = re.compile(r'^(\s*)"id"\s*:')


@dataclass(frozen=True)
class Problem:
    line: int
    story: str
    rule: str
    message: str

    def format(self, path: str) -> str:
        return f"{path}:{self.line}: {self.story}: {self.rule}: {self.message}"


@dataclass
class Story:
    data: dict
    line: int
    field_lines: dict = field(default_factory=dict)

    def line_of(self, name: str) -> int:
        return self.field_lines.get(name, self.line)

    @property
    def sid(self) -> str:
        value = self.data.get("id")
        return value if isinstance(value, str) and value else "plan"


@dataclass
class Plan:
    format: str
    stories: list
    problems: list


# ---------------------------------------------------------------- helpers

def show(value) -> str:
    if isinstance(value, str):
        return f"'{value}'"
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return repr(value)


def id_list(items) -> str:
    return "[" + ", ".join(str(x) for x in items) + "]"


def is_list_of_str(value) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_glob(path: str) -> bool:
    return any(c in path for c in "*?[")


def fenced_blocks(lines: List[str]) -> List[Tuple[str, int, List[str]]]:
    """(language, 1-based line of the opening fence, content lines)."""
    blocks = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("```"):
            lang = lines[i][3:].strip()
            start = i + 1
            j = start
            while j < len(lines) and lines[j].rstrip() != "```":
                j += 1
            blocks.append((lang, i + 1, lines[start:j]))
            i = j + 1
        else:
            i += 1
    return blocks


# ---------------------------------------------------------------- parsing

def parse_plan(text: str) -> Plan:
    lines = text.lstrip("﻿").splitlines()
    blocks = fenced_blocks(lines)
    if any(l.rstrip() == "**Format**: Gherkin (BDD)" for l in lines):
        return _parse_gherkin_plan(blocks)
    return _parse_json_plan(blocks)


def _parse_json_plan(blocks) -> Plan:
    plan = Plan("json", [], [])
    json_blocks = [b for b in blocks if b[0] == "json"]
    if not json_blocks:
        plan.problems.append(Problem(0, "plan", "stories-block", "no json block with the stories"))
        return plan
    if len(json_blocks) > 1:
        plan.problems.append(Problem(json_blocks[1][1], "plan", "stories-block",
                                     f"found {len(json_blocks)} json blocks; expected exactly 1"))
        return plan
    _, opening, content = json_blocks[0]
    try:
        stories = json.loads("\n".join(content))
    except ValueError as err:
        msg = getattr(err, "msg", str(err))
        plan.problems.append(Problem(opening + getattr(err, "lineno", 0), "plan", "stories-block",
                                     f"invalid JSON: {msg}"))
        return plan
    if not isinstance(stories, list) or not all(isinstance(s, dict) for s in stories):
        plan.problems.append(Problem(opening, "plan", "stories-block",
                                     "the stories block must be a JSON array of objects"))
        return plan
    if not stories:
        plan.problems.append(Problem(opening, "plan", "stories-block", "the stories array is empty"))
        return plan
    id_lines = []
    indent = None
    for n, line in enumerate(content):
        m = JSON_ID_RE.match(line)
        if m:
            if indent is None:
                indent = m.group(1)
            if m.group(1) == indent:
                id_lines.append(opening + 1 + n)
    for k, data in enumerate(stories):
        plan.stories.append(Story(data, id_lines[k] if k < len(id_lines) else opening))
    return plan


def _parse_gherkin_plan(blocks) -> Plan:
    plan = Plan("gherkin", [], [])
    features = [b for b in blocks if b[0] == "gherkin"]
    if not features:
        plan.problems.append(Problem(0, "plan", "stories-block", "no gherkin Feature block found"))
        return plan
    for _, opening, content in features:
        story, problems = parse_gherkin_feature(content, opening + 1)
        plan.problems.extend(problems)
        if story is not None:
            plan.stories.append(story)
    return plan


def _split(value: str, sep: str) -> list:
    if value == "none":
        return []
    return [x.strip() for x in value.split(sep)]


def parse_gherkin_feature(lines: List[str], first_line: int) -> Tuple[Optional[Story], List[Problem]]:
    problems: List[Problem] = []
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    values = {}
    label_lines = {}
    sid = "plan"
    for j, label in enumerate(GHERKIN_LABELS):
        pos = idx + j
        ln = first_line + pos
        found = lines[pos].strip() if pos < len(lines) else ""
        prefix = f"# {label}:"
        if not found.startswith(prefix):
            problems.append(Problem(ln, sid, "gherkin", f"expected '{prefix}' line, found '{found}'"))
            return None, problems
        values[label] = found[len(prefix):].strip()
        label_lines[label] = ln
        if label == "ID" and values[label]:
            sid = values[label]
    pos = idx + len(GHERKIN_LABELS)
    feature_ln = first_line + pos
    feature = lines[pos].strip() if pos < len(lines) else ""
    if not feature.startswith("Feature:"):
        problems.append(Problem(feature_ln, sid, "gherkin", "the 'Feature:' line must come right after '# Notes:'"))
        return None, problems
    title = feature[len("Feature:"):].strip()

    rest = lines[pos + 1:]
    desc = []
    for line in rest:
        if not line.strip():
            break
        desc.append(line.strip())
    if not (any(d.startswith(("As a ", "As an ")) for d in desc)
            and any(d.startswith("I want") for d in desc)
            and any(d.startswith("So that") for d in desc)):
        problems.append(Problem(feature_ln, sid, "gherkin",
                                "Feature description must have 'As a', 'I want' and 'So that' lines"))

    criteria = []
    first_scenario = None
    for n, line in enumerate(rest):
        s = line.strip()
        head = next((h for h in ("Scenario Outline:", "Scenario:") if s.startswith(h)), None)
        if head is None:
            continue
        ln = feature_ln + 1 + n
        if first_scenario is None:
            first_scenario = ln
        name = s[len(head):].strip()
        tag = rest[n - 1].strip() if n >= 1 else ""
        if tag not in ("@happy", "@edge", "@error"):
            problems.append(Problem(ln, sid, "gherkin",
                                    f"Scenario '{name}' must have a @happy, @edge or @error tag on the line above"))
            continue
        verify = rest[n - 2].strip() if n >= 2 else ""
        if not verify.startswith("# Verify:"):
            problems.append(Problem(ln, sid, "gherkin",
                                    f"the tag above Scenario '{name}' must have a '# Verify: <check>' line above it"))
            continue
        criteria.append({"kind": tag[1:], "text": name, "verify": verify[len("# Verify:"):].strip()})

    dependencies = []
    raw = values["Dependencies"]
    if raw != "none":
        for item in DEP_SPLIT_RE.split(raw):
            m = DEP_ITEM_RE.match(item.strip())
            if not m:
                problems.append(Problem(label_lines["Dependencies"], sid, "gherkin",
                                        f"dependency '{item.strip()}' must look like 'US-001 (reason)'"))
                continue
            dependencies.append({"id": m.group(1), "reason": m.group(2).strip()})

    def boolean(v):
        return {"true": True, "false": False}.get(v, v)

    priority = values["Priority"]
    data = {
        "id": values["ID"],
        "type": values["Type"],
        "title": title,
        "description": " ".join(desc),
        "independentTest": values["Independent Test"],
        "acceptanceCriteria": criteria,
        "priority": int(priority) if priority.isdigit() else priority,
        "complexity": values["Complexity"],
        "dependencies": dependencies,
        "interfaces": {"consumes": _split(values["Consumes"], ";"), "produces": _split(values["Produces"], ";")},
        "filesToTouch": _split(values["Files"], ","),
        "leverage": _split(values["Leverage"], ","),
        "parallel": boolean(values["Parallel"]),
        "conflictsWith": _split(values["Conflicts With"], ","),
        "source": values["Source"],
        "status": values["Status"],
        "passes": boolean(values["Passes"]),
        "notes": "" if values["Notes"] == "none" else values["Notes"],
    }
    field_lines = {f: label_lines[label] for label, f in LABEL_FIELDS.items()}
    field_lines["title"] = field_lines["description"] = feature_ln
    field_lines["acceptanceCriteria"] = first_scenario or feature_ln
    return Story(data, label_lines["ID"], field_lines), problems


# ---------------------------------------------------------------- rules

def check_header(text: str) -> List[Problem]:
    lines = text.lstrip("﻿").splitlines()
    problems = []
    if not any(l.rstrip() == "**Schema**: v2" for l in lines):
        ln = next((n for n, l in enumerate(lines, 1) if l.startswith("**Schema**:")), 0)
        problems.append(Problem(ln, "plan", "header", "missing '**Schema**: v2' header line"))
    heading = next((n for n, l in enumerate(lines) if l.rstrip() == "## Assumptions"), None)
    if heading is None:
        problems.append(Problem(0, "plan", "sections", "missing '## Assumptions' section"))
    else:
        body = []
        for l in lines[heading + 1:]:
            if l.startswith("## "):
                break
            body.append(l)
        if not any(l.strip() for l in body):
            problems.append(Problem(heading + 1, "plan", "sections", "'## Assumptions' section is empty"))
    if not any(l.rstrip() == "## Open Questions" for l in lines):
        problems.append(Problem(0, "plan", "sections", "missing '## Open Questions' section"))
    return problems


def _type_problems(d: dict) -> List[Tuple[str, str]]:
    """(field, message) for every present field with a wrong type or value."""
    out = []

    def bad(f, desc):
        out.append((f, f"'{f}' must be {desc}, got {show(d[f])}"))

    def enum(f, allowed):
        out.append((f, f"'{f}' must be one of {', '.join(allowed)}; got {show(d[f])}"))

    for f in ("id", "title", "description", "independentTest"):
        if f in d and not (isinstance(d[f], str) and d[f]):
            bad(f, "a non-empty string")
    if "notes" in d and not isinstance(d["notes"], str):
        bad("notes", "a string")
    for f, allowed in (("type", TYPES), ("source", SOURCES), ("status", STATUSES)):
        if f in d and d[f] not in allowed:
            enum(f, allowed)
    if "complexity" in d:
        if d["complexity"] == "XL":
            out.append(("complexity", "'complexity' is XL: break the story down (allowed: XS, S, M, L)"))
        elif not isinstance(d["complexity"], str) or d["complexity"] not in COMPLEXITIES:
            enum("complexity", COMPLEXITIES)
    if "priority" in d and not is_int(d["priority"]):
        bad("priority", "an integer")
    if "acceptanceCriteria" in d and not (isinstance(d["acceptanceCriteria"], list) and d["acceptanceCriteria"]):
        bad("acceptanceCriteria", "a non-empty list")
    if "dependencies" in d:
        deps = d["dependencies"]
        ok = isinstance(deps, list) and all(
            isinstance(x, dict) and set(x) == {"id", "reason"} and isinstance(x["id"], str)
            and isinstance(x["reason"], str) and x["reason"] for x in deps)
        if not ok:
            bad("dependencies", "a list of objects with 'id' and a non-empty 'reason'")
    if "interfaces" in d:
        i = d["interfaces"]
        if not (isinstance(i, dict) and set(i) == {"consumes", "produces"}
                and is_list_of_str(i["consumes"]) and is_list_of_str(i["produces"])):
            bad("interfaces", "an object with 'consumes' and 'produces' lists of strings")
    for f in ("filesToTouch", "leverage", "conflictsWith"):
        if f in d and not is_list_of_str(d[f]):
            bad(f, "a list of strings")
    for f in ("parallel", "passes"):
        if f in d and not isinstance(d[f], bool):
            bad(f, "true or false")
    return out


def _criteria_problems(crits: list) -> List[str]:
    out = []
    for i, c in enumerate(crits, 1):
        pre = f"acceptance criterion {i}: "
        if not isinstance(c, dict):
            out.append(pre + f"must be an object with 'kind', 'text' and 'verify', got {show(c)}")
            continue
        for k in ("kind", "text", "verify"):
            if k not in c:
                out.append(pre + f"missing '{k}'")
        for k in c:
            if k not in ("kind", "text", "verify"):
                out.append(pre + f"unknown field '{k}'")
        if "kind" in c and c["kind"] not in KINDS:
            out.append(pre + f"'kind' must be one of happy, edge, error; got {show(c['kind'])}")
        for k in ("text", "verify"):
            if k in c and not (isinstance(c[k], str) and c[k]):
                out.append(pre + f"'{k}' must be a non-empty string")
    return out


def check_stories(plan: Plan, new: bool) -> List[Problem]:
    problems: List[Problem] = []
    seen_ids = {}
    priorities = []
    for k, st in enumerate(plan.stories, 1):
        d, sid = st.data, st.sid

        def add(rule, msg, f=None):
            problems.append(Problem(st.line_of(f) if f else st.line, sid, rule, msg))

        if plan.format == "json":
            missing = [f for f in SCHEMA_FIELDS if f not in d]
            unknown = [f for f in d if f not in SCHEMA_FIELDS]
            for f in missing:
                add("fields", f"missing field '{f}'")
            for f in unknown:
                add("fields", f"unknown field '{f}'")
            if not missing and not unknown:
                for n, (want, got) in enumerate(zip(SCHEMA_FIELDS, d), 1):
                    if want != got:
                        add("fields", f"fields out of order: expected '{want}' at position {n}, found '{got}'")
                        break
        for f, msg in _type_problems(d):
            add("field-type", msg, f)

        sid_value = d.get("id")
        if isinstance(sid_value, str) and sid_value:
            if not ID_RE.match(sid_value):
                add("id-format", f"id '{sid_value}' must look like US-001", "id")
            if sid_value in seen_ids:
                add("id-unique", f"duplicate id {sid_value} (also at line {seen_ids[sid_value]})", "id")
            else:
                seen_ids[sid_value] = st.line_of("id")
            expected = f"US-{k:03d}"
            if sid_value != expected:
                add("id-sequence", f"id {sid_value} is story {k} in the plan; expected {expected}", "id")

        if is_int(d.get("priority")):
            priorities.append(d["priority"])

        crits = d.get("acceptanceCriteria")
        if isinstance(crits, list) and crits:
            for msg in _criteria_problems(crits):
                add("criteria", msg, "acceptanceCriteria")
            kinds = {c.get("kind") for c in crits if isinstance(c, dict) and isinstance(c.get("kind"), str)}
            if "happy" not in kinds:
                add("criteria-min", "no 'happy' acceptance criterion", "acceptanceCriteria")
            if d.get("type") in ("feature", "bug") and not kinds & {"edge", "error"}:
                add("criteria-min", f"a {d['type']} needs at least one 'edge' or 'error' criterion",
                    "acceptanceCriteria")

        if d.get("filesToTouch") == [] and d.get("type") != "spike":
            add("spike", "only a spike may have an empty 'filesToTouch'", "filesToTouch")
        if d.get("type") == "spike" and d.get("complexity") in ("L", "XL"):
            add("spike", f"a spike must be at most M, got {d['complexity']}", "complexity")

        if new:
            if "status" in d and d["status"] != "todo":
                add("new-plan", f"a new plan must have status 'todo', got {show(d['status'])}", "status")
            if "passes" in d and d["passes"] is not False:
                add("new-plan", f"a new plan must have passes false, got {show(d['passes'])}", "passes")

    if plan.stories:
        n = len(plan.stories)
        missing = [x for x in range(1, n + 1) if x not in priorities]
        repeated = sorted({x for x in priorities if priorities.count(x) > 1})
        if missing or repeated:
            problems.append(Problem(plan.stories[0].line, "plan", "priority",
                                    f"priorities must be 1..{n} with each number once; "
                                    f"missing {id_list(missing)}, repeated {id_list(repeated)}"))
    return problems


def shares_file(a: List[str], b: List[str]) -> bool:
    return any(p == q or fnmatch.fnmatchcase(p, q) or fnmatch.fnmatchcase(q, p) for p in a for q in b)


def _dep_ids(story: Story) -> List[str]:
    deps = story.data.get("dependencies")
    if not isinstance(deps, list):
        return []
    return [x["id"] for x in deps if isinstance(x, dict) and isinstance(x.get("id"), str)]


def check_graph(plan: Plan) -> List[Problem]:
    problems: List[Problem] = []
    index = {}
    for st in plan.stories:
        sid = st.data.get("id")
        if isinstance(sid, str) and sid and sid not in index:
            index[sid] = st

    for st in plan.stories:
        line = st.line_of("dependencies")
        seen = set()
        reported = set()
        own = st.data.get("priority")
        for did in _dep_ids(st):
            if did in seen:
                if did not in reported:
                    problems.append(Problem(line, st.sid, "dependency-duplicate",
                                            f"lists dependency {did} more than once"))
                    reported.add(did)
                continue
            seen.add(did)
            if did not in index:
                problems.append(Problem(line, st.sid, "dependency-missing",
                                        f"depends on {did}, which is not in the plan"))
                continue
            theirs = index[did].data.get("priority")
            if is_int(own) and is_int(theirs) and not theirs < own:
                problems.append(Problem(line, st.sid, "dependency-order",
                                        f"depends on {did} (priority {theirs}), which does not come earlier "
                                        f"(this story's priority is {own})"))

    # Cycles: DFS in plan order; each back edge gives one cycle, normalized to start at its smallest id.
    graph = {sid: list(dict.fromkeys(d for d in _dep_ids(st) if d in index)) for sid, st in index.items()}
    color = {sid: 0 for sid in graph}
    stack: List[str] = []
    cycles = []

    def visit(node):
        color[node] = 1
        stack.append(node)
        for nxt in graph[node]:
            if color[nxt] == 1:
                nodes = stack[stack.index(nxt):]
                start = nodes.index(min(nodes))
                cyc = tuple(nodes[start:] + nodes[:start])
                if cyc not in cycles:
                    cycles.append(cyc)
            elif color[nxt] == 0:
                visit(nxt)
        stack.pop()
        color[node] = 2

    for sid in graph:
        if color[sid] == 0:
            visit(sid)
    for cyc in cycles:
        st = index[cyc[0]]
        problems.append(Problem(st.line_of("dependencies"), cyc[0], "dependency-cycle",
                                "dependency cycle: " + " -> ".join(cyc + (cyc[0],))))

    for st in plan.stories:
        files = st.data.get("filesToTouch")
        actual = st.data.get("conflictsWith")
        if not is_list_of_str(files) or not is_list_of_str(actual):
            continue
        expected = sorted({o.sid for o in plan.stories
                           if o is not st and o.sid != "plan" and is_list_of_str(o.data.get("filesToTouch"))
                           and shares_file(files, o.data["filesToTouch"])})
        line = st.line_of("conflictsWith")
        if sorted(actual) != expected:
            problems.append(Problem(line, st.sid, "conflicts",
                                    f"conflictsWith is {id_list(actual)} but the stories that share a file "
                                    f"in filesToTouch are {id_list(expected)}"))
        elif actual != sorted(actual):
            problems.append(Problem(line, st.sid, "conflicts", "conflictsWith must be sorted by id"))
        parallel = st.data.get("parallel")
        if isinstance(parallel, bool) and parallel != (actual == []):
            problems.append(Problem(st.line_of("parallel"), st.sid, "parallel",
                                    "parallel must be true exactly when conflictsWith is []"))
    return problems


def check_files(plan: Plan, root: Optional[Path]) -> List[Problem]:
    problems: List[Problem] = []
    for st in plan.stories:
        for name in ("filesToTouch", "leverage"):
            paths = st.data.get(name)
            if not is_list_of_str(paths):
                continue
            line = st.line_of(name)
            for p in paths:
                parts = PurePosixPath(p).parts
                if PurePosixPath(p).is_absolute() or ".." in parts:
                    problems.append(Problem(line, st.sid, "path-outside",
                                            f"path '{p}' in {name} must be relative to the project root, "
                                            f"without '..'"))
                    continue
                if root is None or not parts:
                    continue
                target = p.split("#", 1)[0] if name == "leverage" else p
                if (root / target).exists() or (is_glob(target) and glob.glob(str(root / target))):
                    continue
                if name == "leverage":
                    problems.append(Problem(line, st.sid, "leverage-missing",
                                            f"leverage path '{target}' does not exist under {root}"))
                    continue
                top = parts[0]
                if len(parts) == 1 or is_glob(top) or (root / top).is_dir():
                    continue
                problems.append(Problem(line, st.sid, "file-unanchored",
                                        f"filesToTouch path '{p}' does not exist and neither does its "
                                        f"top-level directory '{top}/' under {root}"))
    return problems


# ---------------------------------------------------------------- entry points

def lint(text: str, root: Optional[Path] = None, new: bool = False) -> Tuple[Plan, List[Problem]]:
    plan = parse_plan(text)
    problems = check_header(text) + list(plan.problems)
    if not any(p.rule == "stories-block" for p in plan.problems):
        problems += check_stories(plan, new) + check_graph(plan) + check_files(plan, root)
    return plan, sorted(problems, key=lambda p: p.line)


def lint_text(text: str, root: Optional[Path] = None, new: bool = False) -> List[Problem]:
    return lint(text, root, new)[1]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lint_plan.py",
        description="Check user-stories plans (schema v2, JSON or Gherkin). Reads the plans; writes nothing.")
    parser.add_argument("plans", nargs="+", metavar="PLAN", help="plan file(s), e.g. .context/my-goal-plan.md")
    parser.add_argument("--new", action="store_true",
                        help="the plan was just generated: every story must be status todo and passes false")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--root", metavar="DIR", help="project root for the file rules (default: current directory)")
    group.add_argument("--skip-files", action="store_true",
                       help="skip the rules that look at the disk (leverage-missing, file-unanchored)")
    args = parser.parse_args(argv)

    root: Optional[Path] = None
    if not args.skip_files:
        root = Path(args.root or ".")
        if not root.is_dir():
            sys.stderr.write(f"lint_plan: --root {args.root} is not a directory\n")
            return 2

    code = 0
    for path in args.plans:
        try:
            text = Path(path).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as err:
            reason = getattr(err, "strerror", None) or str(err)
            sys.stderr.write(f"lint_plan: cannot read {path}: {reason}\n")
            code = max(code, 2)
            continue
        try:
            plan, problems = lint(text, root, args.new)
        except Exception as err:  # never show a traceback
            sys.stderr.write(f"lint_plan: internal error on {path}: {err!r}\n")
            code = max(code, 2)
            continue
        for p in problems:
            print(p.format(path))
        if problems:
            print(f"{path}: {len(problems)} problem(s)")
            code = max(code, 1)
        else:
            print(f"OK {path}: {len(plan.stories)} stories ({plan.format})")
    return code


if __name__ == "__main__":
    sys.exit(main())
