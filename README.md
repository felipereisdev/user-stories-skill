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
- **Atomic User Stories** - Breaks goals into 2-4 hour implementable chunks
- **Dependency Ordering** - Stories ordered so earlier ones enable later ones
- **Clear Acceptance Criteria** - Every story has verifiable completion criteria
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

## 📄 Output

Creates `.context/[goal-slug]-plan.md` with structured user stories.

### JSON Format (Default)

```json
[
  {
    "id": "US-001",
    "title": "Create user model and database schema",
    "description": "As a developer, I want...",
    "acceptanceCriteria": [...],
    "priority": 1,
    "complexity": "M",
    "dependencies": [],
    "filesToTouch": [...],
    "notes": "..."
  }
]
```

### Gherkin Format (BDD)

```gherkin
# Complexity: M
# Dependencies: []
# Files: prisma/schema.prisma, src/models/User.ts

Feature: Create user model and database schema
  As a developer
  I want a user model with authentication fields
  So that I can securely store login data

  Scenario: Prisma schema has all required fields
    Given the Prisma configuration exists
    When I define the User model in schema.prisma
    Then it should have fields: id, email, password_hash, name, created_at, updated_at

  Scenario: Database migration is created
    Given the User model is defined
    When I run prisma migrate dev
    Then a migration SQL file should be generated
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

Runs in `context: fork` with `agent: general-purpose`: an isolated subagent that reads your code and writes only the plan file (the read-only `Explore` agent cannot save it). In Claude Code the fork runs in the background by default; you are notified when the plan is saved.

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
