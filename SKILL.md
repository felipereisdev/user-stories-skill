---
name: user-stories
description: "Analyzes a codebase and breaks down a goal into implementable user stories with clear acceptance criteria. Use when planning a new feature, estimating work, or creating a development roadmap. Explores the code before asking anything; when the goal is ambiguous, asks at most 5 blocking multiple-choice questions with a recommended answer, and records assumptions and open questions in the plan. Outputs structured stories to .context/[goal-slug]-plan.md ordered by dependency. Filename is generated from the goal (kebab-case, 3-5 words). Do NOT implement anything - only analyze and plan."
argument-hint: <goal-description> [--format=json|gherkin] [--answers="<choices>"]
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Grep, Glob, Write, Bash
context: fork
agent: general-purpose
---

# User Stories - Codebase Analysis & Story Breakdown

Analyze a codebase and break down a goal into small, atomic, implementable user stories. **Do NOT implement anything — only analyze and plan.** The plan file in `.context/` is the only file you write — never create, edit or delete any other file.

## Input

If `$ARGUMENTS` is empty, ask: "What goal would you like to break down into user stories? You can optionally add `--format=gherkin` for BDD-style output."

Otherwise, extract the goal, the optional format flag (`--format=json` default, or `--format=gherkin`) and the optional `--answers="..."`, which carries the user's answers to the clarifying questions of an earlier run (see [Clarification Protocol](#clarification-protocol)). If the format is invalid: "Invalid format. Use `--format=json` (default) or `--format=gherkin` for BDD-style output." The filename comes from the goal only, never from the flags.

## Workflow

1. **Explore** the codebase with Glob/Grep/Read: architecture, patterns, frameworks, similar existing features
2. **Clarify** what the code does not answer, following the [Clarification Protocol](#clarification-protocol): either stop with at most 5 blocking questions, or record assumptions and open questions and go on
3. **Decompose** the goal into 3–10 atomic user stories, each completable in one coding session (2–4 hours max)
4. **Sequence** stories by technical and logical dependency — earlier stories enable later ones
5. **Estimate** complexity per story: XS (<1h, single file), S (1–2h), M (2–4h), L (4–8h), XL (break it down further)
6. **Generate filename** from the goal (see [naming rules](#output-file-naming))
7. **Write** the plan to `.context/[slug]-plan.md` using JSON or Gherkin format
8. **Verify** all stories have clear acceptance criteria and reasonable scope, and the plan lists its assumptions and open questions

### Error Recovery

- **Goal too vague**: follow the [Clarification Protocol](#clarification-protocol); never ask more than 5 questions
- **Goal too broad** (>10 stories): suggest splitting into separate plans
- **No relevant codebase patterns found**: note in Context Summary and plan from first principles
- **Story too large** (XL+): decompose into sub-stories before continuing
- **Fewer than 3 stories**: verify granularity is sufficient for the goal

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
**Goal**: $ARGUMENTS

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
    "id": "US-001",
    "title": "Story title in user voice",
    "description": "As a [user type], I want [goal] so that [benefit]. Implementation details...",
    "acceptanceCriteria": [
      "Specific, verifiable criterion 1",
      "Specific, verifiable criterion 2",
      "Specific, verifiable criterion 3"
    ],
    "priority": 1,
    "complexity": "S",
    "dependencies": [],
    "filesToTouch": ["path/to/file1.ts", "path/to/file2.ts"],
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

Include `## Clarifications` only when questions were answered. Always include `## Assumptions` (never empty: at least the scope boundaries you chose) and `## Open Questions` (`None.` when there are none).

See [example-output.md](example-output.md) for a complete JSON example.

## Gherkin Format

When `--format=gherkin` is specified, output Feature/Scenario blocks instead of JSON. Each user story becomes a Feature with Scenarios for each acceptance criterion. Include metadata comments (`# Complexity`, `# Dependencies`, `# Files`) above each Feature block. All Gherkin output must be in English regardless of input language. Keep every other section of the template (Context Summary, Clarifications, Assumptions, Open Questions, Implementation Notes, Definition of Done).

See [example-gherkin-output.md](example-gherkin-output.md) for the complete template and a six-feature example.
