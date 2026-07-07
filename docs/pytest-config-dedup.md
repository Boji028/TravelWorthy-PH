# Remove duplicate/dead pytest config from pyproject.toml

**Date:** 2026-07-03

## What changed

Removed the `[tool.pytest.ini_options]` block from `pyproject.toml`.

`pytest.ini` and `pyproject.toml` both defined pytest configuration.
`pytest.ini` always won silently (confirmed by `configfile: pytest.ini`
in every test run), so the `pyproject.toml` block was fully dead —
never actually applied. It also had a mismatched, unused marker set
(`unit`, `admin`, `email`, `backup`) versus the real markers used
throughout `tests/` (`auth`, `bookings`, `models`, `forms`,
`integration`, `slow`, `real_async_email`, all defined in `pytest.ini`).

All other `pyproject.toml` sections (Black, isort, coverage, mypy,
pylint) were left untouched.

## Why

Config defined in two places with one silently overriding the other
is a trap for future edits — someone could reasonably update the
`pyproject.toml` block expecting it to take effect and get no error,
no warning, and no actual change. Removing the dead copy makes
`pytest.ini` the single source of truth for test configuration.

## Verification

Ran the full suite after removal:
```
pytest --tb=short -q
```
Result: 485 passed, `configfile: pytest.ini` with no more warning
about `pyproject.toml` config being ignored.

## Note for later (not addressed here)

Coverage config still exists in *two* places too — `[coverage:run]` /
`[coverage:report]` in `pytest.ini`, and `[tool.coverage.run]` /
`[tool.coverage.report]` in `pyproject.toml`. These aren't in direct
conflict the way the pytest blocks were — `coverage.py` doesn't read
config from `pytest.ini` at all, so the copy sitting there is already
inert and `pyproject.toml`'s version is the one that actually applies
whenever `pytest --cov=.` is run. Left alone in this pass since it's
not causing any active problem, but worth cleaning up whenever the
`pytest.ini` file gets touched again.
