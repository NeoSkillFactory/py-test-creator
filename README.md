# py-test-creator

![Audit](https://img.shields.io/badge/audit%3A%20PASS-brightgreen) ![License](https://img.shields.io/badge/license-MIT-blue) ![OpenClaw](https://img.shields.io/badge/OpenClaw-skill-orange)

> Automatically generates pytest-compatible unit test templates from Python function signatures and docstrings

## Usage

Trigger the skill with natural language:

- "Create unit tests for this Python function"
- "Generate test templates from these function signatures"
- "Write pytest tests for my Python methods"
- "Create unit test scaffolding from docstrings"

The skill expects a Python file or code snippet as input and produces a corresponding test file.

## Configuration

No configuration required. The skill uses default pytest conventions.

**Optional environment variables:**
- `PYTEST_STRICT`: Set to `true` to enable strict mark handling
- `TEST_COVERAGE`: Set to `true` to include coverage hints in generated tests

## Quick Start
## Installation

Dependencies are managed via `package.json`. Install with:

```bash
npm install
```

This will install the required Python packages (pytest, ast-parser utilities) and Node.js dependencies for the skill runner.

## GitHub

Source code: [github.com/NeoSkillFactory/py-test-creator](https://github.com/NeoSkillFactory/py-test-creator)

**Price suggestion:** $19.99 USD

## License

MIT © NeoSkillFactory
