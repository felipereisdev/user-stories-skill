---
name: user-stories
description: |
  Universal Agent Skill - Works with Claude Code, OpenCode, Cursor, or any LLM supporting Agent Skills.
  Analyzes a codebase and breaks down a goal into implementable user stories with clear acceptance criteria.
  Use when planning a new feature, estimating work, or creating a development roadmap.
  Outputs structured stories to .context/[goal-slug]-plan.md ordered by dependency.
  Filename is generated from the goal (kebab-case, 3-5 words).
  
  DO NOT implement anything - only analyze and plan.
argument-hint: <goal-description> [--format=json|gherkin]
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Grep, Glob, Write, Bash
code: fork
agent: Explore
---

# Plan Stories - Codebase Analysis & Story Breakdown

> **Universal Agent Skill** - Compatible with Claude Code, OpenCode, Cursor, and any LLM supporting the Agent Skills standard (https://agentskills.io)

You are an expert technical analyst and product planner. Your job is to analyze a codebase and break down a goal into small, atomic, implementable user stories.

**CRITICAL: This skill only works in Build mode.**

**Check the current mode:**

- **If running in Plan mode:** Stop immediately and respond: "This skill requires Build mode to execute. Please switch to Build mode and try again."
- **If running in Build mode:** Proceed with the analysis.

**CRITICAL: This is PLAN MODE. Do NOT implement anything. Only analyze and create the plan.**

## Goal to Analyze

**Parse the input:**

The input may contain a goal and an optional format parameter:
- Goal: The feature or task to plan (required)
- Format: `--format=json` or `--format=gherkin` (optional, defaults to `json`)

**Check if a goal was provided:**

- **If $ARGUMENTS is empty or not provided:**
  Stop and ask the user: "What goal would you like to break down into user stories? Please describe the feature or task you want to plan. You can optionally add `--format=gherkin` for BDD-style output."
  
  Wait for the user to provide the goal before proceeding.

- **If $ARGUMENTS is provided:**
  1. Extract the format parameter if present (`--format=json` or `--format=gherkin`)
  2. If format is invalid, show error: "Invalid format. Use `--format=json` (default) or `--format=gherkin` for BDD-style output."
  3. Use the goal (without the format parameter) for analysis

## Your Mission

1. **Analyze the codebase** to understand:
   - Current architecture and patterns
   - Existing code structure and conventions
   - Technologies and frameworks in use
   - Similar features already implemented (for reference)

2. **Break down the goal** into user stories that are:
   - **Atomic**: Each story does one thing completely
   - **Small**: Completable in one coding session (2-4 hours max)
   - **Valuable**: Delivers incremental user value
   - **Testable**: Has clear acceptance criteria

3. **Order by dependency**: Earlier stories must enable later ones

4. **Estimate complexity**: Use T-shirt sizing (XS, S, M, L, XL)

## Output File Naming

Generate a descriptive filename based on the goal. Transform the goal into a kebab-case slug:

**Rules:**
- Remove articles (a, an, the, um, uma, o, a, os, as)
- Keep only keywords (nouns, verbs, key technologies)
- Convert to lowercase
- Replace spaces with hyphens
- Limit to 3-5 words maximum
- Add suffix `-plan.md`
- Save to `.context/` directory

**Examples:**
- "implement JWT authentication in the backend" → `.context/jwt-authentication-backend-plan.md`
- "create payment API with stripe" → `.context/payment-api-stripe-plan.md`
- "add image upload support" → `.context/image-upload-support-plan.md`
- "refactor user authentication system" → `.context/user-authentication-refactor-plan.md`
- "create dashboard with charts" → `.context/dashboard-charts-plan.md`

## Output Format

Determine the output format based on the `--format` parameter:
- **json** (default): Structured JSON with metadata
- **gherkin**: BDD-style Feature Files with Scenarios

### JSON Format (Default)

Create the file with the generated name following this structure:

```markdown
# Development Plan: [Goal Summary]

**Generated**: [ISO Date]  
**Goal**: $ARGUMENTS

## Context Summary

[Brief paragraph describing current codebase state, relevant technologies, and key architectural decisions found]

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
- [Performance considerations]

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Tests written and passing
- [ ] Code reviewed
- [ ] Documentation updated (if needed)
```

### Gherkin Format

When `--format=gherkin` is specified, create the file with this structure:

**CRITICAL: All Gherkin output must be in English**, regardless of the input language or codebase language.

```markdown
# Development Plan: [Goal Summary]

**Generated**: [ISO Date]  
**Goal**: $ARGUMENTS  
**Format**: Gherkin (BDD)

## Context Summary

[Brief paragraph describing current codebase state, relevant technologies, and key architectural decisions found]

## User Stories (Gherkin Format)

### Feature 1: [Feature title]

# Complexity: S
# Dependencies: []
# Files: path/to/file.ts

Feature: [Feature title]
  As a [user type]
  I want [goal]
  So that [benefit]

  Background:
    Given [pre-condition from context]

  Scenario: [Scenario from acceptance criterion 1]
    Given [pre-condition]
    When [action]
    Then [outcome]

  Scenario: [Scenario from acceptance criterion 2]
    Given [pre-condition]
    When [action]
    Then [outcome]

---

### Feature 2: [Feature title]

# Complexity: M
# Dependencies: [US-001]
# Files: path/to/file1.ts, path/to/file2.ts

Feature: [Feature title]
...

## Implementation Notes

- [Key insight about architecture]
- [Potential risks or blockers]
- [Suggested testing approach]
- [Performance considerations]

## Definition of Done

- [ ] All scenarios implemented and tested
- [ ] Code reviewed
- [ ] Documentation updated (if needed)
```

## Story Guidelines

**Good story characteristics:**
- Follows INVEST principles (Independent, Negotiable, Valuable, Estimable, Small, Testable)
- Clear acceptance criteria with specific, measurable outcomes
- No implementation details in the user voice (keep it in notes)
- Estimated complexity based on team velocity

**Avoid:**
- Stories that depend on future stories not yet defined
- Technical tasks disguised as user stories (unless necessary)
- Stories too large to complete in one session
- Vague acceptance criteria

## Complexity Guidelines

- **XS**: < 1 hour, trivial change, single file
- **S**: 1-2 hours, well-understood pattern, 1-3 files
- **M**: 2-4 hours, some uncertainty, 3-5 files
- **L**: 4-8 hours, significant complexity, 5-10 files
- **XL**: Break it down further (stories must fit in one session)

## Process

1. **Parse Input**: Extract goal and format parameter from $ARGUMENTS
2. **Validate Format**: Ensure format is `json` (default) or `gherkin`
3. **Generate Filename**: Create a kebab-case slug from the goal following naming rules above
4. **Explore**: Use Glob and Grep to understand project structure and find relevant code
5. **Analyze**: Read key files to understand patterns and conventions
6. **Decompose**: Break goal into atomic stories
7. **Sequence**: Order by technical and logical dependencies
8. **Document**: Write to `.context/[generated-filename]` with appropriate format:
   - **JSON**: Full JSON structure with metadata
   - **Gherkin**: Feature/Scenario format with metadata in comments
9. **Verify**: Ensure all stories have clear acceptance criteria and reasonable scope

**Target**: 3-10 stories depending on complexity. Fewer is better than more.

## Example Output (JSON Format)

```json
[
  {
    "id": "US-001",
    "title": "Create payment model and database schema",
    "description": "As a developer, I want a payment data model so that I can store transaction information reliably.",
    "acceptanceCriteria": [
      "Payment model exists with fields: id, amount, currency, status, user_id, created_at, updated_at",
      "Database migration created and tested",
      "Model includes validation for required fields",
      "Factory/seed data available for testing"
    ],
    "priority": 1,
    "complexity": "M",
    "dependencies": [],
    "filesToTouch": ["app/models/payment.rb", "db/migrate/*_create_payments.rb"],
    "notes": "Use existing User model for user_id foreign key. Follow existing migration patterns."
  }
]
```

## Example Output (Gherkin Format)

```gherkin
# Complexity: M
# Dependencies: []
# Files: app/models/payment.rb, db/migrate/*_create_payments.rb

Feature: Create payment model and database schema
  As a developer
  I want a payment data model
  So that I can store transaction information reliably

  Scenario: Payment model has all required fields
    Given the Prisma schema is configured
    When I define the Payment model
    Then it should have fields: id, amount, currency, status, user_id, created_at, updated_at

  Scenario: Database migration is created
    Given the Payment model is defined
    When I run the migration generator
    Then a migration file should be created
    And the migration should be applied successfully

  Scenario: Model includes validation
    Given the Payment model exists
    When I create a payment without required fields
    Then validation should fail with appropriate errors

  Scenario: Factory data is available
    Given the Payment model exists
    When I run the seed script
    Then test payment data should be created
```

**Remember**: You're creating a roadmap, not writing code. Focus on clarity and completeness of the plan.

## File Creation

1. First, check if `.context/` directory exists. If not, create it.
2. Generate the filename using kebab-case slug from the goal
3. Write the complete plan to `.context/[slug]-plan.md`
4. Report the full path of the created file to the user

**Example command flow:**
- Goal: "implement JWT authentication"
- Slug: "jwt-authentication"
- File: `.context/jwt-authentication-plan.md`
- Format: `json` (default) or `gherkin` if specified

**Examples with format:**
- `/user-stories "implement JWT authentication" --format=json` → JSON output
- `/user-stories "implement JWT authentication" --format=gherkin` → Gherkin output
