---
name: user-stories
description: "Analyzes a codebase and breaks down a goal into implementable user stories with clear acceptance criteria. Use when planning a new feature, estimating work, or creating a development roadmap. Outputs structured stories to .context/[goal-slug]-plan.md ordered by dependency. Filename is generated from the goal (kebab-case, 3-5 words). Do NOT implement anything - only analyze and plan."
argument-hint: <goal-description> [--format=json|gherkin]
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

Otherwise, extract the goal and optional format flag (`--format=json` default, or `--format=gherkin`). If the format is invalid: "Invalid format. Use `--format=json` (default) or `--format=gherkin` for BDD-style output."

## Workflow

1. **Explore** the codebase with Glob/Grep/Read: architecture, patterns, frameworks, similar existing features
2. **Decompose** the goal into 3–10 atomic user stories, each completable in one coding session (2–4 hours max)
3. **Sequence** stories by technical and logical dependency — earlier stories enable later ones
4. **Estimate** complexity per story: XS (<1h, single file), S (1–2h), M (2–4h), L (4–8h), XL (break it down further)
5. **Generate filename** from the goal (see [naming rules](#output-file-naming))
6. **Write** the plan to `.context/[slug]-plan.md` using JSON or Gherkin format
7. **Verify** all stories have clear acceptance criteria and reasonable scope

### Error Recovery

- **Goal too vague**: ask the user to clarify scope before proceeding
- **Goal too broad** (>10 stories): suggest splitting into separate plans
- **No relevant codebase patterns found**: note in Context Summary and plan from first principles
- **Story too large** (XL+): decompose into sub-stories before continuing
- **Fewer than 3 stories**: verify granularity is sufficient for the goal

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

See [example-output.md](example-output.md) for a complete JSON example.

## Gherkin Format

When `--format=gherkin` is specified, output Feature/Scenario blocks instead of JSON. Each user story becomes a Feature with Scenarios for each acceptance criterion. Include metadata comments (`# Complexity`, `# Dependencies`, `# Files`) above each Feature block. All Gherkin output must be in English regardless of input language.

See [example-gherkin-output.md](example-gherkin-output.md) for the complete template and a six-feature example.
