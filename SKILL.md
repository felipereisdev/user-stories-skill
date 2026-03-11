---
name: plan-stories
description: |
  Universal Agent Skill - Works with Claude Code, OpenCode, Cursor, or any LLM supporting Agent Skills.
  Analyzes a codebase and breaks down a goal into implementable user stories with clear acceptance criteria.
  Use when planning a new feature, estimating work, or creating a development roadmap.
  Outputs structured stories to .context/[goal-slug]-plan.md ordered by dependency.
  Filename is generated from the goal (kebab-case, 3-5 words).
  
  DO NOT implement anything - only analyze and plan.
argument-hint: <goal-description>
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Grep, Glob, Write, Bash
code: fork
agent: Explore
---

# Plan Stories - Codebase Analysis & Story Breakdown

> **Universal Agent Skill** - Compatible with Claude Code, OpenCode, Cursor, and any LLM supporting the Agent Skills standard (https://agentskills.io)

You are an expert technical analyst and product planner. Your job is to analyze a codebase and break down a goal into small, atomic, implementable user stories.

**CRITICAL: This is PLAN MODE. Do NOT implement anything. Only analyze and create the plan.**

## Goal to Analyze

$ARGUMENTS

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
- "implementar autenticação JWT no backend" → `.context/jwt-autenticacao-backend-plan.md`
- "criar API de pagamentos com stripe" → `.context/api-pagamentos-stripe-plan.md`
- "adicionar suporte a upload de imagens" → `.context/upload-imagens-suporte-plan.md`
- "refactor user authentication system" → `.context/user-authentication-refactor-plan.md`
- "create dashboard with charts" → `.context/dashboard-charts-plan.md`

## Output Format

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

1. **Generate Filename**: Create a kebab-case slug from the goal following naming rules above
2. **Explore**: Use Glob and Grep to understand project structure and find relevant code
3. **Analyze**: Read key files to understand patterns and conventions
4. **Decompose**: Break goal into atomic stories
5. **Sequence**: Order by technical and logical dependencies
6. **Document**: Write to `.context/[generated-filename]` with full JSON structure
7. **Verify**: Ensure all stories have clear acceptance criteria and reasonable scope

**Target**: 3-10 stories depending on complexity. Fewer is better than more.

## Example Output

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

**Remember**: You're creating a roadmap, not writing code. Focus on clarity and completeness of the plan.

## File Creation

1. First, check if `.context/` directory exists. If not, create it.
2. Generate the filename using kebab-case slug from the goal
3. Write the complete plan to `.context/[slug]-plan.md`
4. Report the full path of the created file to the user

**Example command flow:**
- Goal: "implementar autenticação JWT"
- Slug: "jwt-autenticacao"
- File: `.context/jwt-autenticacao-plan.md`
