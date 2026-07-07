# Root-level documentation cleanup

**Date:** 2026-07-03

## What changed

Moved 27 loose implementation/status `.md` files from the project
root into `docs/`, where all other project documentation already
lives (activity logs, cleanup notes, etc.).

Moved:
- `AUTOMATED_BACKUPS_GUIDE.md`
- `BACKUP_SETUP_GUIDE.md`
- `CI_CD_PIPELINE_GUIDE.md`
- `CICD_FILE_MANIFEST.md`
- `CICD_FINAL_IMPLEMENTATION_CHECKLIST.md`
- `CICD_IMPLEMENTATION_SUMMARY.md`
- `CICD_PHASE2_COMPLETION_SUMMARY.md`
- `CICD_QUICK_REFERENCE.md`
- `CRITICAL_FIXES_IMPLEMENTED.md`
- `DATABASE_MIGRATION_GUIDE.md`
- `DEPLOYMENT_PRODUCTION_READINESS.md`
- `DOCKER_QUICK_START.md`
- `EMAIL_NOTIFICATIONS_GUIDE.md`
- `EMAIL_VERIFICATION_IMPLEMENTATION.md`
- `ENHANCEMENTS.md`
- `GITHUB_ACTIONS_SETUP.md`
- `IMAGE_METADATA_GUIDE.md`
- `IMPLEMENTATION_COMPLETE.md`
- `IMPLEMENTATION_PHASE1_AUTO_REPLY.md`
- `PHASE1_VISUAL_SUMMARY.md`
- `POSTGRES_COMPLETE.md`
- `POSTGRES_QUICK_REFERENCE.md`
- `POSTGRES_SETUP_GUIDE.md`
- `POSTGRESQL_WINDOWS_INSTALL.md`
- `PROFESSIONAL_CODE_ANALYSIS.md`
- `QUICK_DEPLOYMENT_GUIDE.md`
- `README_POSTGRES_MIGRATION.md`

Also deleted `test_image.jpg` from root — an unused stray file with
zero references anywhere in the codebase (confirmed via full-repo
grep before deletion).

**Kept at root** (convention-driven locations expected by GitHub or
tooling, not moved):
- `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
- `CLAUDE.md` (Claude Code convention)
- `docker-compose.yml`, `Dockerfile`, `Procfile`
- `pyproject.toml`, `pytest.ini`, `requirements.txt`
- `.flake8`, `.gitignore`, `.pre-commit-config.yaml`,
  `.env.example`, `.env.test`
- `flask.bat`, `setup.sh`
- All application `.py` modules

## Why

Root had grown to ~50 visible items mixing real application code,
standard config files, and 27 different implementation-phase
documentation files accumulated over the project's history. This made
it hard to tell at a glance what's actual project structure versus
historical notes. No code changes — purely a file location move, so
no risk to the running application.

## Follow-up (not done in this pass)

Several of the moved docs are clearly redundant now that they sit
next to each other in `docs/` — six separate Postgres-related files
(`POSTGRES_COMPLETE.md`, `POSTGRES_QUICK_REFERENCE.md`,
`POSTGRES_SETUP_GUIDE.md`, `POSTGRESQL_WINDOWS_INSTALL.md`,
`README_POSTGRES_MIGRATION.md`, `DATABASE_MIGRATION_GUIDE.md`) and
six CI/CD-related files. Worth consolidating each cluster into one
authoritative doc in a future pass — deliberately not attempted here
since it requires reading and judging content overlap rather than
just moving files.
