# AGENTS.md

## Cursor Cloud specific instructions

This is a pure-Python (stdlib only) Space Debris Tracking & Collision Risk Dashboard using an MVC architecture. There are **no third-party dependencies** and no build step.

### Quick reference

| Task | Command |
|------|---------|
| Run app | `python3 main.py` |
| Run tests | `python3 -m unittest discover -s tests -q` |

- **Python 3.10+** is required (uses `dataclass(slots=True)` and modern type hints).
- There is no linter, formatter, or type-checker configured in the repo. Standard `python3 -m py_compile <file>` can be used to syntax-check individual files.
- The view layer (`view/`) is currently a print-only stub; the app prints `Space Debris Tracking Dashboard (skeleton)` and exits.
- Test fixtures live in `tests/testing_csvs/`. The sample catalog (`sample_catalog.csv`) has 2 debris objects and is used for integration-style testing.
- No database, web server, Docker, or external service is required.
