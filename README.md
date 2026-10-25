# User Stories Skill 🎯

[![GitHub stars](https://img.shields.io/github/stars/felipereisdev/user-stories-skill?style=social)](https://github.com/felipereisdev/user-stories-skill)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-purple)](https://agentskills.io)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-blue)](https://claude.ai)
[![OpenCode](https://img.shields.io/badge/OpenCode-compatible-green)](https://opencode.ai)

> An Agent Skill that analyzes codebases and breaks down goals into implementable user stories with clear acceptance criteria.

**Compatible with any LLM that supports the [Agent Skills Standard](https://agentskills.io)** - Claude Code, OpenCode, Cursor, and any other AI coding assistant that implements the skills protocol.

## 🌟 Features

- **Automatic Codebase Analysis** - Understands your project architecture and patterns
- **Clarify Before Planning** - Explores the code first, then asks at most 5 blocking multiple-choice questions, each with a recommended answer, and only when the goal is ambiguous
- **Recorded Assumptions** - Every plan lists the assumptions it made and the open questions left for later
- **Atomic User Stories** - Breaks goals into 2-4 hour implementable chunks
- **Dependency Ordering** - Stories ordered so earlier ones enable later ones
- **Clear Acceptance Criteria** - Every story has verifiable completion criteria
- **Execution-Ready Stories** - Schema v2: each story has a type, an independent test, a `verify` check per criterion, dependencies with reasons, interfaces, files to reuse, and `parallel`/`conflictsWith` derived from the files it touches
- **Dynamic File Naming** - Generates descriptive filenames based on your goal
- **Multiple Output Formats** - Choose between JSON (default) or Gherkin (BDD)
- **Plan-Only Output** - Never changes your code; the only file it writes is the plan in `.context/` (so it needs a mode that allows file writes, not Plan Mode)
- **Universal Compatibility** - Works with any LLM supporting Agent Skills

## 📦 Installation

Clone the repository once, then link the clone into the skills folder of each assistant you use. Run every link command **from the root of the clone** (`user-stories-skill/`, the folder that holds `SKILL.md`): the link points at `$(pwd)`.

```bash
git clone https://github.com/felipereisdev/user-stories-skill.git
cd user-stories-skill
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
ln -sfn "$(pwd)" ~/.claude/skills/user-stories
```

### Codex

```bash
mkdir -p ~/.agents/skills
ln -sfn "$(pwd)" ~/.agents/skills/user-stories
```

### OpenCode

```bash
mkdir -p ~/.config/opencode/skills
ln -sfn "$(pwd)" ~/.config/opencode/skills/user-stories
```

OpenCode also reads `~/.claude/skills` and `~/.agents/skills`. If you already linked the skill for Claude Code or Codex, OpenCode finds it there: do not create a second link, or the skill shows up twice.

### Cursor

```bash
mkdir -p ~/.cursor/skills
ln -sfn "$(pwd)" ~/.cursor/skills/user-stories
```

### Other assistants

Link the clone into the skills folder your assistant reads, with the name `user-stories`. Cursor and the Agent Skills standard require the folder name to match the skill's `name`.

### Check the link

```bash
ls ~/.claude/skills/user-stories/SKILL.md
```

Replace the path with the skills folder you used; the file must exist.

`ln -sfn` replaces an earlier link, so running the commands again is safe. If a real folder (not a link) already exists at that path, remove it first.

## 🚀 Usage

Invoke the skill with your goal and optional format:

### Universal

```bash
# JSON format (default)
/user-stories "implement user authentication with JWT"

# Gherkin format (BDD)
/user-stories "implement user authentication with JWT" --format=gherkin
```

### Claude Code

```bash
# JSON format (default)
/user-stories "implement user authentication with JWT"

# Gherkin format (BDD)
/user-stories "implement user authentication with JWT" --format=gherkin
```

### OpenCode

OpenCode loads skills through its `skill` tool from your request:

```text
Use the user-stories skill to plan: implement user authentication with JWT

Use the user-stories skill to plan: implement user authentication with JWT --format=gherkin
```

### Codex

Type `$` to mention the skill:

```text
$user-stories "implement user authentication with JWT"

$user-stories "implement user authentication with JWT" --format=gherkin
```

### Cursor

```bash
# JSON format (default)
/user-stories "implement user authentication with JWT"

# Gherkin format (BDD)
/user-stories "implement user authentication with JWT" --format=gherkin
```

### Clarifying questions

The skill reads your code before asking anything. A clear goal gets no questions: the plan is written and records the assumptions it made. An ambiguous goal gets at most 5 questions, only the ones that block the plan, each with lettered options and a recommended answer, and no plan is written yet:

```text
**1. Which notification channel should the first version support?**
Found: no mail or push provider in package.json; todos live in memory in src/routes/todos.js
- **A)** In-app notifications served by a new /notifications route
- **B)** Email
- **C)** Both

**Recommended: A** — needs no new dependency or credentials
```

Reply with a number and a letter per question, for example `1A, 2C`, or `recommended` to accept every recommendation. You can also answer in your own words.

In Claude Code the skill runs in a forked subagent, which cannot wait for your reply: it returns the questions and stops, and when you answer, Claude runs the skill again with your choices in `--answers`. You can pass them yourself too, spelling out each choice:

```bash
/user-stories "add notifications" --answers="1A: in-app only; 2B: notify when a todo is created or completed"
/user-stories "add notifications" --answers=recommended
```

Running `/user-stories` with no goal works the same way: the skill only asks for the goal and writes nothing; in Claude Code, Claude runs it again with the goal you give.

Doubts that do not block the plan never become questions: they go into the plan's Assumptions and Open Questions sections.

## 📄 Output

Creates `.context/[goal-slug]-plan.md` with structured user stories, the assumptions the plan made and its open questions (plus your answers under Clarifications, when the skill asked any).

The stories follow schema v2, ready for an executor: see [Schema v2 fields](SKILL.md#schema-v2-fields) for every field and its rule. The skill writes every story with `status` `todo` and `passes` `false`; the executor (a Ralph-style loop, Task Master, a CI job) updates them as it works. The skill never runs the `verify` checks.

### JSON Format (Default)

```json
[
  {
    "id": "US-002",
    "type": "feature",
    "title": "User registers with email and password",
    "description": "As a visitor, I want to register so that I can access the app.",
    "independentTest": "POST /api/auth/register creates a user and returns 201",
    "acceptanceCriteria": [
      {"kind": "happy", "text": "Valid payload returns 201 without password_hash", "verify": "npm test -- auth.register"},
      {"kind": "edge", "text": "Duplicate email returns 409", "verify": "npm test -- auth.register"},
      {"kind": "error", "text": "Password under 8 chars returns 400 with message", "verify": "npm test -- auth.register"}
    ],
    "priority": 2,
    "complexity": "M",
    "dependencies": [
      {"id": "US-001", "reason": "needs User model"}
    ],
    "interfaces": {
      "consumes": [
        "User.create()"
      ],
      "produces": [
        "POST /api/auth/register"
      ]
    },
    "filesToTouch": [
      "src/controllers/AuthController.ts",
      "src/routes/auth.routes.ts",
      "src/validators/auth.validator.ts"
    ],
    "leverage": [
      "src/validators/base.validator.ts"
    ],
    "parallel": false,
    "conflictsWith": [
      "US-004"
    ],
    "source": "explicit",
    "status": "todo",
    "passes": false,
    "notes": "Use `express-validator` library for validation (already installed). Follow existing JSON response pattern in the application."
  }
]
```

### Gherkin Format (BDD)

```gherkin
# ID: US-002
# Type: feature
# Independent Test: POST /api/auth/register creates a user and returns 201
# Priority: 2
# Complexity: M
# Dependencies: US-001 (needs User model)
# Consumes: User.create()
# Produces: POST /api/auth/register
# Files: src/controllers/AuthController.ts, src/routes/auth.routes.ts, src/validators/auth.validator.ts
# Leverage: src/validators/base.validator.ts
# Parallel: false
# Conflicts With: US-004
# Source: explicit
# Status: todo
# Passes: false
# Notes: Use `express-validator` library for validation (already installed). Follow existing JSON response pattern in the application.
Feature: User registers with email and password
  As a visitor
  I want to register
  So that I can access the app

  # Verify: npm test -- auth.register
  @happy
  Scenario: Successfully register with valid data
    Given I provide a valid email format
    And I provide a password with at least 8 characters
    And I provide a non-empty name
    When I submit a POST request to /api/auth/register
    Then I should receive a 201 status code
    And my password should be hashed in the database
    And the response should not include password_hash

  # Verify: npm test -- auth.register
  @error
  Scenario: Reject registration with weak password
    Given I provide a password with less than 8 characters
    When I submit a POST request to /api/auth/register
    Then I should receive a 400 status code
    And I should see an error message about password length

  # Verify: npm test -- auth.register
  @edge
  Scenario: Reject registration with duplicate email
    Given a user with my email already exists
    When I submit a POST request to /api/auth/register
    Then I should receive a 409 status code
    And I should see an error message about email already in use
```

## 🎯 Examples

| Goal | Generated File | Format |
|------|----------------|--------|
| "implement JWT authentication" | `.context/jwt-authentication-plan.md` | JSON (default) |
| "implement JWT authentication --format=gherkin" | `.context/jwt-authentication-plan.md` | Gherkin |
| "create Stripe payment API" | `.context/stripe-payment-api-plan.md` | JSON (default) |
| "add image upload feature" | `.context/image-upload-feature-plan.md` | JSON (default) |

### When to Use Each Format

- **JSON**: Best for technical planning, estimation, and integration with tools
- **Gherkin**: Best for BDD workflows, test automation, and stakeholder communication

## 🔧 How It Works

This skill follows the [Agent Skills Standard](https://agentskills.io), making it compatible with any AI assistant that supports:

- **Tool Calling**: Read, Grep, Glob, Write, Bash
- **Subagents**: Forked execution for safe analysis
- **Skill Discovery**: Automatic loading from skills directories

### Supported Tools

- `Read` - Codebase exploration
- `Grep` - Pattern searching  
- `Glob` - File discovery
- `Write` - Plan generation
- `Bash` - Directory operations

Runs in `context: fork` with `agent: general-purpose`: an isolated subagent that reads your code and writes only the plan file (the read-only `Explore` agent cannot save it). In Claude Code the fork runs in the background by default; you are notified when the plan is saved. Because the fork cannot wait for an answer, an ambiguous goal ends the run with the questions; see [Clarifying questions](#clarifying-questions).

## 📚 Example Files

See the example output files for reference:

- **JSON Format**: [`example-output.md`](example-output.md)
- **Gherkin Format**: [`example-gherkin-output.md`](example-gherkin-output.md)

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by Agile/Scrum best practices and Polyscope's autopilot mode
- Clarification protocol inspired by spec-kit's `/clarify`, Ralph's PRD skill, bobchao and superpowers
- Schema v2 inspired by Ralph, Task Master, ccpm, cc-sdd, spec-workflow-mcp, superpowers and SprintiQ
- Built following the [Agent Skills Standard](https://agentskills.io)
- Compatible with Claude Code, OpenCode, Cursor, and any Agent Skills-compatible AI
- Community-driven development

## 🔗 Links

- [Agent Skills Standard](https://agentskills.io)
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code/skills)
- [OpenCode Documentation](https://opencode.ai/docs/skills)
- [Cursor Documentation](https://cursor.sh)

## 💡 Request Support for Your AI Assistant

If your favorite AI assistant doesn't support Agent Skills yet, open an issue or reach out to their team! This skill is designed to work with any tool that implements the standard.

---

⭐ Star this repo if it helps you plan better!

**Made with ❤️ for the AI coding community**
