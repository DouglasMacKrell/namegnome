# Contributing to NameGnome

Thank you for your interest in contributing! Please follow these guidelines to ensure a smooth workflow and high-quality codebase.

## Commit Style
- Use the format: `NGN-###: concise action description`
  - Example: `NGN-012: add support for multi-segment episodes`
- Reference the relevant ticket or task in `TASK.md` when possible.

## Code Style & Standards
- **Language:** Python ≥ 3.12 with type hints
- **Formatting:** Use `black`
- **Linting:** Use `ruff`
- **Static types:** `mypy --strict`
- **Tests:** Pytest only; all new code must include tests (expected, edge, failure)
- **Docstrings:** Google style for all public functions/classes
- **Imports:** Use absolute imports rooted at `namegnome`
- **No file > 500 lines**; split into focused modules
- **Filesystem operations:** All file moves/renames must use
  `namegnome.fs.operations.atomic_move`. See [docs/fs-operations.md](docs/fs-operations.md)
  for API, usage, and guarantees.

## Test Requirements
- Every new function/class requires:
  - 1 expected-flow test
  - 1 edge case
  - 1 failure case
  - If your code moves or renames files, you must use and test atomic_move.
- Tests must pass on Windows, macOS, and Linux
- Coverage threshold: 80% (enforced in CI)

## Onboarding Checklist
- Read `README.md` for install and usage
- Review `PLANNING.md` for project vision and architecture
- Check `TASK.md` for current and upcoming work
- Run `pre-commit run --all-files` before pushing
- Ensure all tests pass locally (`pytest`)
- Update documentation if you add commands, flags, or dependencies

## Submitting a Pull Request
- Fork the repo and create a feature branch from `develop`
- Make your changes with clear, atomic commits
- Ensure CI passes and code coverage is maintained
- Add or update tests as needed
- Reference the relevant task or ticket in your PR description

Thank you for helping make NameGnome better! 