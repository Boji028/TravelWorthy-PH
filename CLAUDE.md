Guidance for Claude Code working with code in this repo.

## Project Overview
- Travel Worthy PH: Flask app for a real travel agency (Batangas City), inquiry-based, no payments
- Python 3.14, SQLAlchemy, Flask-Login, Flask-WTF
- PostgreSQL in prod, SQLite for local dev/tests
- Cloudinary for image storage
- Windows dev environment; venv at `..\.venv`, activate with `..\.venv\Scripts\activate`
- Run tests: `pytest` (from `fixed/` directory)

## Known Pitfalls
- Any new db.relationship() pointing at a NOT NULL foreign key needs
  cascade='all, delete-orphan' (or passive_deletes=True) on the parent side.
  Without it, deleting the parent crashes with IntegrityError instead of
  cascading. This caused a real production 500 on Inquiry/Notification,
  Package/Image, Package/Review, and User/Review - check new relationships
  against this before committing.

## General Principles
- Generate concise, short solutions for new modules or code.
- Watch for over-engineering, oversized files needing refactor.
- Watch for weird syntax/style mismatching rest of codebase.
- Watch for obvious bugs and blast radius of errors.
- No emojis or special characters in comments.
- Write activity-log.md in /docs to refer back if confused.
- Run major changes by user first dont execute blindly.
- Review existing files before refactor or change.
- Markdown files use kebab naming (ex. some-description-changes.md).
- Comments: one-liner, one sentence.

## Code Quality
- Right data structures and algorithms for problem.
- Don't expose data needlessly (least privilege).
- No external libraries unless absolutely necessary.
- Use project dependency file for correct versions.
- Avoid redundancy unless improves usability.

## Version Control
- Commit after significant changes, clear messages.
- Keep commits focused, atomic.
- No auto-push any branch.
- Don't auto-commit activity logs and docs.
- Access only these repositories: <REPO_ALLOWLIST>

## AI Restrictions
- No customer personal data - names, contacts, account numbers, transactions (unless approved exemption).
- No credentials - passwords, API keys, tokens, connection strings.
- Always check npm/yarn install/download safe, verify via <PACKAGE_REGISTRY_HOST>