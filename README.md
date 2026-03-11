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
- **Plan Mode Compatible** - Works safely without making code changes
- **Universal Compatibility** - Works with any LLM supporting Agent Skills

## 📦 Installation

### Option 1: Direct Clone (Universal)

Works with any AI assistant:

```bash
git clone https://github.com/felipereisdev/user-stories-skill.git
```

Then configure your AI assistant to load skills from the cloned directory.

### Option 2: Claude Code

```bash
# Clone into your global skills
mkdir -p ~/.claude/skills
ln -s "$(pwd)/user-stories" ~/.claude/skills/user-stories
```

### Option 3: OpenCode/Codex

```bash
# Clone into your global skills
mkdir -p ~/.codex/skills
ln -s "$(pwd)/user-stories" ~/.codex/skills/user-stories
```

### Option 4: Cursor

```bash
# Clone into your Cursor skills directory
mkdir -p ~/.cursor/skills
ln -s "$(pwd)/user-stories" ~/.cursor/skills/user-stories
```

## 🚀 Usage

Invoke the skill with your goal:

### Universal

```
/user-stories "implement user authentication with JWT"
```

### Claude Code

```bash
/user-stories "implement user authentication with JWT"
```

### OpenCode

```
@user-stories "implement user authentication with JWT"
```

### Cursor

```
/user-stories "implement user authentication with JWT"
```

## 📄 Output

Creates `.context/[goal-slug]-plan.md` with structured user stories:

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

## 🎯 Examples

| Goal | Generated File |
|------|----------------|
| "implement JWT authentication" | `.context/jwt-authentication-plan.md` |
| "create Stripe payment API" | `.context/stripe-payment-api-plan.md` |
| "add image upload feature" | `.context/image-upload-feature-plan.md` |

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

Runs in `context: fork` with `agent: Explore` for safe, read-only analysis.

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

- Inspired by Agile/Scrum best practices
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
