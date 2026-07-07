# Fix Security Scanning CI workflow (4 of 6 jobs failing)

## Problem
The "Security Scanning" GitHub Actions workflow (.github/workflows/security.yml)
was failing on 4 of its 6 jobs: dependency-scanning, safety-check,
code-scanning, and trivy-scan. Only secret-scanning and sast-analysis
succeeded.

## Root causes (three separate issues)

### 1. safety vs black dependency conflict (requirements.txt)
Reproduced directly with a clean pip install:
The conflict is caused by:
gunicorn 26.0.0 depends on packaging
pytest 7.4.3 depends on packaging
black 23.11.0 depends on packaging>=22.0
safety 2.3.5 depends on packaging<22.0 and >=21.0
safety==2.3.5 and black==23.11.0 require mutually exclusive versions
of packaging - no version satisfies both. This broke `pip install -r
requirements.txt` from a completely clean environment (not just CI -
any fresh machine or new contributor would hit this). It only worked
locally because the existing .venv predates this combination.

Checked whether upgrading safety instead would fix it: it doesn't.
Safety CLI 3.x rewrote itself into a commercial product requiring
account authentication before running any command, including the old
`check` subcommand - so bumping the version just trades one failure
for a different one (auth error instead of resolution error).

Decision: drop safety entirely, rely on pip-audit (already in
requirements.txt, already working, maintained by the Python Packaging
Authority, no auth required). Removes the conflict at its source
instead of patching around it.

This same requirements.txt install (with no continue-on-error) is also
used in deploy-production.yml's "Install dependencies" step - meaning
an actual production deploy run would have hit this too, not just the
daily security-scan cron.

### 2. CodeQL Action v2 - fully retired
github/codeql-action v2 (used for init/analyze in code-scanning, and
upload-sarif in trivy-scan) was deprecated Jan 2024 and fully retired
by GitHub in 2025. Workflows still referencing v2 fail outright.

### 3. Missing permission on trivy-scan
trivy-scan uploads SARIF results to GitHub's Security tab but never
declared `security-events: write` (code-scanning already had this).
Without it, the upload step can fail depending on the repo's default
GITHUB_TOKEN permission setting.

## Fix
- requirements.txt - removed safety==2.3.5
- .github/workflows/security.yml:
  - Removed the safety-check job entirely
  - github/codeql-action/upload-sarif@v2 -> @v3 (trivy-scan)
  - github/codeql-action/init@v2 -> @v3, analyze@v2 -> @v3 (code-scanning)
  - Added permissions: security-events: write to trivy-scan
- .github/workflows/deploy-production.yml:
  - Removed safety from the "Run security checks" step (pip install
    bandit safety -> pip install bandit; dropped safety check --json)

## Verification
- Clean `pip install -r requirements.txt` in a brand new venv: exit
  code 0, no errors (previously: ResolutionImpossible).
- Full test suite: 511 passed, 0 failed (no change - this was a CI/
  dependency-resolution issue, not an app code issue).
- Both edited workflow YAML files parse correctly.

## Result
5 jobs remain in Security Scanning (was 6): dependency-scanning,
trivy-scan, secret-scanning, code-scanning, sast-analysis. All should
now pass. Vulnerability scanning coverage is unchanged in substance -
pip-audit (dependency-scanning) and Trivy (trivy-scan) both already
cover the same "known vulnerable package" ground safety did.