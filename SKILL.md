---
name: user-stories
description: "Analyzes a codebase and breaks down a goal into implementable user stories with clear acceptance criteria. Use when planning a new feature, estimating work, or creating a development roadmap. Explores the code before asking anything; when the goal is ambiguous, asks at most 5 blocking multiple-choice questions with a recommended answer, and records assumptions and open questions in the plan. Outputs execution-ready stories (schema v2: type, status, a verify check per criterion, dependencies with reasons, interfaces, files to reuse, file conflicts for parallel work) to .context/[goal-slug]-plan.md ordered by dependency. Checks the plan with its bundled standard-library Python linter (scripts/lint_plan.py) when python3 is available. Filename is generated from the goal (kebab-case, 3-5 words). Do NOT implement anything - only analyze and plan."
argument-hint: <goal-description> [--format=json|gherkin] [--answers="<choices>"]
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Grep, Glob, Write, Bash
context: fork
agent: general-purpose
---

# User Stories - Codebase Analysis & Story Breakdown

Analyze a codebase and break down a goal into small, atomic, implementable user stories. **Do NOT implement anything — only analyze and plan.** The plan file in `.context/` (written first as a `.draft.md` and then renamed) is the only file you write — never create, edit or delete any other file.

## Input

If `$ARGUMENTS` is empty (no goal), do not explore the code and do not write any file. End your response with only this: "What goal would you like to break down into user stories? You can optionally add `--format=gherkin` for BDD-style output." followed by the line "_Calling agent: show this question to the user. When the user replies, run this skill again with their goal as the argument. Do not write the plan yourself._"

Otherwise, extract the goal, the optional format flag (`--format=json` default, or `--format=gherkin`) and the optional `--answers="..."`, which carries the user's answers to the clarifying questions of an earlier run (see [Clarification Protocol](#clarification-protocol)). If the format is invalid: "Invalid format. Use `--format=json` (default) or `--format=gherkin` for BDD-style output." The filename comes from the goal only, never from the flags.

## Workflow

1. **Explore** the codebase with Glob/Grep/Read: architecture, patterns, frameworks, similar existing features. Note the project's own test, lint and build commands (from `package.json`, `Makefile`, `pyproject.toml` and the like, for `verify`) and the existing files and helpers a story should reuse (for `leverage`)
2. **Clarify** what the code does not answer, following the [Clarification Protocol](#clarification-protocol): either stop with at most 5 blocking questions, or record assumptions and open questions and go on
3. **Decompose** the goal into 3–10 atomic user stories, each completable in one coding session (2–4 hours max). Give each story a `type`, a `source` and an `independentTest`, and write its acceptance criteria as `{kind, text, verify}`
4. **Sequence** stories by technical and logical dependency — earlier stories enable later ones. Give every dependency a `reason`, and write `interfaces`: each item a story `consumes` is produced by one of its dependencies or already exists in the code
5. **Estimate** complexity per story: XS (<1h, single file), S (1–2h), M (2–4h), L (4–8h), XL (break it down further)
6. **Derive** `conflictsWith` and `parallel` after the stories are final: compare the `filesToTouch` of every pair of stories; when two share a path, list each in the other's `conflictsWith`; set `parallel` to `true` only when `conflictsWith` is `[]` (see [Schema v2 fields](#schema-v2-fields)). Derive again if any `filesToTouch` changes
7. **Generate filename** from the goal (see [naming rules](#output-file-naming))
8. **Write** the plan to `.context/[slug]-plan.draft.md` using JSON or Gherkin format, with `status` `todo` and `passes` `false` on every story
9. **Lint** the draft: from the project root, run `python3 <skill-folder>/scripts/lint_plan.py --new .context/[slug]-plan.draft.md`, where `<skill-folder>` is the folder that holds this SKILL.md. Each output line is `file:line: story: rule: message`; fix every problem in the draft and run it again, at most 3 runs in all. Then rename the draft: `mv .context/[slug]-plan.draft.md .context/[slug]-plan.md`. If problems remain after the third run, rename it anyway and list the remaining lines in your response
10. **Verify** the plan against the [Schema v2 checklist](#schema-v2-checklist) — the linter already checked the items marked (linted); check the others yourself — and that it lists its assumptions and open questions

### Error Recovery

- **Goal too vague**: follow the [Clarification Protocol](#clarification-protocol); never ask more than 5 questions
- **Goal too broad** (>10 stories): suggest splitting into separate plans
- **No relevant codebase patterns found**: note in Context Summary and plan from first principles
- **Story too large** (XL+): decompose into sub-stories before continuing
- **Fewer than 3 stories**: verify granularity is sufficient for the goal
- **Linter not available**: if `python3` is not found, or the linter says it needs a newer Python, rename the draft to the plan, check the whole Schema v2 checklist yourself, and say in your response that the plan was not linted

## Clarification Protocol

Explore before asking: never ask what the goal, the code or the docs already answer. Then sort every doubt you still have:

- **Blocking**: the code does not answer it, different answers produce different stories or `filesToTouch`, and no default is safe to assume. Ask it.
- **Assumable**: a reasonable default exists and a wrong guess is cheap to fix. Take the default and record it under Assumptions in the plan.
- **Deferrable**: the answer does not change this plan's stories (it can be settled during implementation or later). Record it under Open Questions in the plan.

**Nothing blocking**: ask nothing and write the plan.

**Something blocking**: ask at most 5 questions, highest impact first (scope, then data and security, then integrations, then UX). Blocking doubts beyond the fifth become Open Questions, with your recommended option recorded as an assumption. Do not write the plan while questions are open: end your response with this block and nothing after it.

```markdown
## Clarifying Questions

I explored the code, and these questions block the plan. Reply with a number and a letter per question (for example `1A, 2C`), with `recommended` to accept every recommendation, or in your own words.

**1. [The question, in one sentence]**
Found: [what the code shows that leaves this open, with file paths]
- **A)** [option]
- **B)** [option]
- **C)** [option]

**Recommended: B** — [why, in one line]

_Calling agent: show these questions to the user as written. When the user replies, run this skill again with the same goal and `--answers="..."`, spelling out each choice (for example `--answers="1A: in-app only; 2C: keep the current schema"`). Do not write the plan yourself: if you cannot run the skill, give the user that command to run._
```

Each question has 2 to 4 options (A–D) and exactly one recommendation.

**Answers arrive** (as the user's reply in this conversation, or in `--answers`): ask nothing new. Apply each answer. `recommended` accepts every recommendation, in this run or in a new one (mark each `recommended, accepted`). An answer you cannot match to a question (such as a bare `2C` in a new run) falls back to your recommendation (mark it `unmatched answer, recommended used`). Record every answer under Clarifications, and turn any remaining doubt into an Assumption or an Open Question.

## Output File Naming

Generate a kebab-case slug from the goal:
- Remove articles (a, an, the, um, uma, o, a, os, as)
- Keep 3–5 keywords (nouns, verbs, key technologies)
- Lowercase, hyphens for spaces, append `-plan.md`
- Save to `.context/` directory (create if needed)

| Goal | File |
|------|------|
| "implement JWT authentication in the backend" | `.context/jwt-authentication-backend-plan.md` |
| "create payment API with stripe" | `.context/payment-api-stripe-plan.md` |
| "add image upload support" | `.context/image-upload-support-plan.md` |

## JSON Format (Default)

Create the plan file with this structure:

```markdown
# Development Plan: [Goal Summary]

**Generated**: [ISO Date]  
**Goal**: [the goal, without the `--format` and `--answers` flags]  
**Schema**: v2

## Context Summary

[Current codebase state, relevant technologies, key architectural decisions]

## Clarifications

- **Q1.** [Question] → **B)** [Chosen option] (answered | recommended, accepted | unmatched answer, recommended used)

## Assumptions

- [Assumption, including what is left out of scope] — based on [file, pattern or reasoning]

## Open Questions

- [Question] — affects [US-00X]; assumed for now: [default]

## User Stories

```json
[
  {
    "id": "US-002",
    "type": "feature",
    "title": "Story title in user voice",
    "description": "As a [user type], I want [goal] so that [benefit]. Implementation details...",
    "independentTest": "One sentence: how to prove this story works on its own, with its dependencies done",
    "acceptanceCriteria": [
      {"kind": "happy", "text": "Specific, verifiable criterion for the expected path", "verify": "the project's own test command for this criterion, or manual: steps"},
      {"kind": "edge", "text": "Specific, verifiable criterion for a boundary or unusual valid input", "verify": "the project's own test command for this criterion, or manual: steps"},
      {"kind": "error", "text": "Specific, verifiable criterion for invalid input or a failure, and the response", "verify": "the project's own test command for this criterion, or manual: steps"}
    ],
    "priority": 2,
    "complexity": "S",
    "dependencies": [{"id": "US-001", "reason": "What this story needs from US-001"}],
    "interfaces": {"consumes": ["Contract from a dependency or the existing code"], "produces": ["Contract this story creates"]},
    "filesToTouch": ["path/to/file1.ts", "path/to/file2.ts"],
    "leverage": ["path/to/existing/helper.ts"],
    "parallel": true,
    "conflictsWith": [],
    "source": "explicit",
    "status": "todo",
    "passes": false,
    "notes": "Any technical notes or gotchas"
  }
]
```

## Implementation Notes

- [Key insight about architecture]
- [Potential risks or blockers]
- [Suggested testing approach]

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Tests written and passing
- [ ] Code reviewed
- [ ] Documentation updated (if needed)
```

### Schema v2 fields

Every story has these 18 fields, in this order. The rules apply to the JSON and Gherkin formats alike.

| Field | Type | Rule |
|---|---|---|
| `id` | string | `US-001`, `US-002`, … in plan order |
| `type` | `feature` \| `enabler` \| `bug` \| `spike` | `feature`: behavior the user sees. `enabler`: technical groundwork another story needs (model, configuration, utility). `bug`: fixes existing wrong behavior; the `description` states the current and the expected behavior. `spike`: time-boxed investigation that ends in a decision; it produces no product code, its criteria are the questions it answers, its `complexity` is at most `M`, and only a spike may have an empty `filesToTouch` |
| `title` | string | User voice |
| `description` | string | "As a [user type], I want [goal] so that [benefit]." plus details |
| `independentTest` | string | One sentence: how to prove this story works on its own, with its dependencies done and no later story |
| `acceptanceCriteria` | array of `{kind, text, verify}` | `kind`: `happy` (expected path), `edge` (valid input at a boundary or unusual), `error` (invalid input or a failure, and what the system answers). At least one `happy`; a `feature` or `bug` also has at least one `edge` or `error` |
| `verify` | string | A command that checks the criterion with the project's own tools (the test script found in `package.json`, `Makefile`, `pyproject.toml` etc., a CLI, an HTTP call), or `manual: <steps>` when no command can. Never a tool the project does not have; a test file the story itself creates is allowed. You write it; you never run it |
| `priority` | integer | 1..N, each once, in execution order |
| `complexity` | `XS` \| `S` \| `M` \| `L` | An `XL` story is broken down |
| `dependencies` | array of `{id, reason}` | `id` of an earlier story in this plan (a smaller `priority` number); `reason` says what this story needs from it; `[]` when none |
| `interfaces` | `{consumes: [string], produces: [string]}` | Concrete contracts: function or method signature, endpoint (`POST /api/x`), event, table, environment variable, command. Each `consumes` item is produced by a story in `dependencies` or already exists in the code |
| `filesToTouch` | array of string | Real paths the story creates or changes; `[]` only for a `spike` |
| `leverage` | array of string | Existing files (or `path#symbol`) to reuse; you read each one while exploring; `[]` when nothing applies |
| `parallel` | boolean | Derived: `true` exactly when `conflictsWith` is `[]` |
| `conflictsWith` | array of id | Derived: the other stories in the plan whose `filesToTouch` shares at least one path with this story's (a glob counts when it matches the path); symmetric (if A lists B, B lists A); sorted by id |
| `source` | `explicit` \| `inferred` | `explicit`: the goal or a clarification answer asks for the story. `inferred`: you added it because the code or another story needs it |
| `status` | `todo` \| `in_progress` \| `done` \| `blocked` | You always write `todo`; the executor updates it |
| `passes` | boolean | You always write `false`; the executor sets `true` only when every `verify` of the story passes |
| `notes` | string | Technical notes or gotchas; `""` when there are none |

### Schema v2 checklist

Before you finish, check every story:

- [ ] All 18 fields are present, in the order of [Schema v2 fields](#schema-v2-fields) (linted)
- [ ] Each criterion has `kind`, `text` and `verify`; there is at least one `happy`; each `feature` and `bug` has an `edge` or `error` (linted)
- [ ] `priority` runs 1..N with no repeats (linted)
- [ ] Each dependency points to an earlier story (a smaller `priority` number) and has a `reason` (linted)
- [ ] Each `consumes` item is produced by a dependency or exists in the code
- [ ] Each `leverage` path exists (linted), and you read it
- [ ] `filesToTouch` is empty only in a `spike`, and a `spike` is at most `M` (linted)
- [ ] `conflictsWith` lists exactly the other stories that share a file, on both sides, and `parallel` is `true` only when it is empty (linted)
- [ ] `status` is `todo` and `passes` is `false` (linted)
- [ ] No `verify` names a tool the project does not have

Include `## Clarifications` only when questions were answered. Always include `## Assumptions` (never empty: at least the scope boundaries you chose) and `## Open Questions` (`None.` when there are none).

See [example-output.md](example-output.md) for a complete JSON example.

## Gherkin Format

When `--format=gherkin` is specified, output Feature/Scenario blocks instead of JSON. Each user story becomes a Feature with a Scenario for each acceptance criterion; the [Schema v2 fields](#schema-v2-fields) rules and the [Schema v2 checklist](#schema-v2-checklist) apply unchanged. All Gherkin output must be in English regardless of input language. Keep every other section of the template (Context Summary, Clarifications, Assumptions, Open Questions, Implementation Notes, Definition of Done), and start the plan header with `**Format**: Gherkin (BDD)` followed by `**Schema**: v2`.

Mapping:

- Put each Feature in its own ` ```gherkin ` fenced block, under a `### Feature N: [title]` heading.
- Above the `Feature:` line, write one comment line per field, in this order and with these exact labels: `# ID:`, `# Type:`, `# Independent Test:`, `# Priority:`, `# Complexity:`, `# Dependencies:`, `# Consumes:`, `# Produces:`, `# Files:`, `# Leverage:`, `# Parallel:`, `# Conflicts With:`, `# Source:`, `# Status:`, `# Passes:`, `# Notes:`. The `Feature:` line comes right after `# Notes:`, with no blank line between them.
- An empty list or empty note is written `none`.
- `# Dependencies:` is `US-001 (reason)` items separated by `; `. `# Consumes:` and `# Produces:` separate items with `; `. `# Files:` (the `filesToTouch`), `# Leverage:` and `# Conflicts With:` separate items with `, `.
- `title` becomes the `Feature:` line, and `description` the As a / I want / So that lines.
- Each `Scenario:` is one criterion. The line right above it is its kind tag, `@happy`, `@edge` or `@error`, and the line above the tag is `# Verify: <check>`.

```gherkin
# ID: US-002
# Type: feature
# Independent Test: POST /api/items creates an item and returns 201
# Priority: 2
# Complexity: S
# Dependencies: US-001 (needs the Item model)
# Consumes: Item.create()
# Produces: POST /api/items
# Files: src/routes/items.ts, src/controllers/ItemController.ts
# Leverage: src/validators/base.validator.ts
# Parallel: true
# Conflicts With: none
# Source: explicit
# Status: todo
# Passes: false
# Notes: none
Feature: User creates an item
  As a user
  I want to create an item
  So that I can track it later

  # Verify: npm test -- items.create
  @happy
  Scenario: Valid payload creates the item
    Given I am a user
    When I send POST /api/items with a valid name
    Then I receive 201 with the created item

  # Verify: npm test -- items.create
  @error
  Scenario: Missing name is rejected
    Given I am a user
    When I send POST /api/items without a name
    Then I receive 400 with a message about the name
```

See [example-gherkin-output.md](example-gherkin-output.md) for the complete template and a six-feature example.
