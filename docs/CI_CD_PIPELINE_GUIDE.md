# GitHub Actions CI/CD Pipeline

This repository uses GitHub Actions for continuous integration, testing, security scanning, and deployment.

## Workflows Overview

### 1. **Tests** (`.github/workflows/tests.yml`)

Runs on every push and pull request to main/develop branches.

**Features:**
- Tests on Python 3.9, 3.10, 3.11
- PostgreSQL test database
- Unit and integration tests
- Code coverage reporting
- Coverage upload to Codecov

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

**Jobs:**
- `test` - Unit tests with coverage
- `integration-test` - Integration tests
- `build` - Application startup check

**Example Output:**
```
✓ Tests passed (Python 3.11)
✓ Code coverage: 75%
✓ Application builds successfully
```

---

### 2. **Code Quality** (`.github/workflows/lint.yml`)

Runs linting and code quality checks.

**Tools:**
- **flake8** - PEP 8 style guide enforcement
- **black** - Code formatter check
- **isort** - Import sorting check
- **pylint** - Static code analysis
- **mypy** - Type checking
- **pip-audit** - Dependency vulnerability scan
- **bandit** - Security linter

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

**Jobs:**
- `lint` - Linting and style checks
- `type-check` - Static type checking
- `dependency-check` - Vulnerability scanning
- `security-lint` - Bandit security checks

---

### 3. **Security Scanning** (`.github/workflows/security.yml`)

Comprehensive security analysis and vulnerability scanning.

**Tools:**
- **pip-audit** - Python dependency security
- **Trivy** - Container and dependency scanning
- **detect-secrets** - Secret detection
- **CodeQL** - GitHub's code analysis engine
- **Bandit** - Python security linter
- **Semgrep** - SAST (Static Application Security Testing)
- **Safety** - Python dependency checker

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`
- Daily schedule at 2 AM UTC

**Jobs:**
- `dependency-scanning` - Check for vulnerable packages
- `trivy-scan` - Filesystem vulnerability scan
- `secret-scanning` - Detect hardcoded secrets
- `code-scanning` - CodeQL analysis
- `sast-analysis` - SAST with Bandit and Semgrep
- `safety-check` - Safety check on dependencies

---

### 4. **Code Coverage** (`.github/workflows/coverage.yml`)

Generates detailed code coverage reports.

**Features:**
- Coverage report generation
- Coverage badge creation
- PR comments with coverage results
- Coverage threshold enforcement (70%)
- HTML coverage reports

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

**Jobs:**
- `coverage` - Generate coverage report and upload artifacts
- `coverage-check` - Verify coverage meets minimum threshold

**Example Coverage Comment:**
```
Coverage Report
- Overall: 75%
- Models: 82%
- Routes: 70%
- Tests: 88%
```

---

### 5. **Deploy to Staging** (`.github/workflows/deploy-staging.yml`)

Automatic deployment to staging on develop branch.

**Triggers:**
- Push to `develop`
- Manual trigger via `workflow_dispatch`

**Jobs:**
- `deploy-staging` - Deploy to staging environment
- `health-check` - Verify staging is healthy

**Steps:**
1. Run all tests
2. Run linting checks
3. Prepare deployment package
4. Deploy via SSH/rsync
5. Run migrations
6. Restart services
7. Health check endpoint

**Environment Variables Needed:**
- `STAGING_HOST` - Staging server hostname
- `STAGING_USER` - SSH user
- `STAGING_PATH` - Deployment path
- `STAGING_DEPLOY_KEY` - SSH private key
- `STAGING_URL` - Health check URL

---

### 6. **Deploy to Production** (`.github/workflows/deploy-production.yml`)

Manual production deployment with full testing.

**Triggers:**
- Manual trigger via `workflow_dispatch` on main branch

**Parameters:**
- `version` - Release version (e.g., 1.0.0)
- `environment` - Target (staging/production)

**Jobs:**
- `deploy-production` - Deploy to production with full checks
- `post-deployment` - Health checks and smoke tests

**Steps:**
1. Comprehensive testing suite
2. Security checks (Bandit, Safety)
3. Version verification
4. Create git tag
5. Build deployment package
6. Database backup before deployment
7. Deploy via SSH/rsync
8. Database migrations
9. Service restart
10. Health check (20 attempts)
11. Smoke tests

**Environment Variables Needed:**
- `PROD_HOST` - Production server
- `PROD_USER` - SSH user
- `PROD_PATH` - Deployment path
- `PROD_DEPLOY_KEY` - SSH private key
- `PROD_URL` - Application URL
- `SLACK_WEBHOOK` - Slack notification webhook

---

## Status Badges

Add these badges to your README.md:

```markdown
![Tests](https://github.com/YOUR_ORG/travel_agency_enhanced/workflows/Tests/badge.svg)
![Code Quality](https://github.com/YOUR_ORG/travel_agency_enhanced/workflows/Code%20Quality/badge.svg)
![Security](https://github.com/YOUR_ORG/travel_agency_enhanced/workflows/Security%20Scanning/badge.svg)
![Coverage](https://codecov.io/gh/YOUR_ORG/travel_agency_enhanced/branch/main/graph/badge.svg)
```

## Setting Up CI/CD

### Prerequisites

1. **GitHub Repository** with these branches:
   - `main` - Production-ready code
   - `develop` - Development branch

2. **Codecov Account** (for coverage reports)
   - Sign up at https://codecov.io
   - Repository will be automatically found

3. **Deployment Servers** (for staging/production)
   - SSH access configured
   - PostgreSQL installed
   - Python 3.11 runtime

### Configuration Steps

#### 1. Configure Test Database

Tests use PostgreSQL. GitHub Actions spins up a temporary PostgreSQL container.

No configuration needed - handled automatically in `tests.yml`.

#### 2. Set GitHub Secrets

Go to Repository Settings → Secrets and Variables → Actions:

**For Staging Deployment:**
```
STAGING_HOST          = staging.example.com
STAGING_USER          = deploy
STAGING_PATH          = /var/www/travel-agency
STAGING_DEPLOY_KEY    = (SSH private key content)
STAGING_URL           = https://staging.example.com
```

**For Production Deployment:**
```
PROD_HOST             = prod.example.com
PROD_USER             = deploy
PROD_PATH             = /var/www/travel-agency
PROD_DEPLOY_KEY       = (SSH private key content)
PROD_URL              = https://travel-agency.com
SLACK_WEBHOOK         = https://hooks.slack.com/services/... (optional)
```

#### 3. Create SSH Deploy Keys

On deployment servers:

```bash
# Create deploy user
sudo useradd -m deploy

# Generate SSH key
ssh-keygen -t ed25519 -f deploy_key -N ""

# Add public key to authorized_keys
cat deploy_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Copy private key to GitHub (add as secret)
cat deploy_key
```

#### 4. Configure Database in Tests

Tests automatically use PostgreSQL via service container.

In your test fixtures, the database URL is:
```
postgresql://testuser:testpass@localhost:5432/test_travel_agency
```

#### 5. Enable CodeQL

CodeQL analysis runs automatically. Results appear under Security → Code scanning.

---

## Workflow Decisions

### Branch Protection Rules

Go to Repository Settings → Branches → Branch protection rules:

**For `main` branch:**
```
✓ Require status checks to pass before merging
  - Tests
  - Code Quality
  - Security Scanning
✓ Require code reviews before merging (at least 1)
✓ Dismiss stale pull request approvals
✓ Require branches to be up to date before merging
```

**For `develop` branch:**
```
✓ Require status checks to pass before merging
  - Tests
  - Code Quality
✓ Require code reviews before merging (at least 1)
```

### Required Checks

These workflows must pass before code can be merged:

1. **Tests** - All tests must pass
2. **Code Quality** - No critical linting errors
3. **Security Scanning** - No critical vulnerabilities
4. **Coverage** - Minimum 70% code coverage (for PRs)

---

## Local Testing

To test workflows locally before pushing:

### Run Tests Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v --cov=. --cov-report=term-missing

# Run with PostgreSQL (use docker)
docker run -d \
  -e POSTGRES_USER=testuser \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=test_travel_agency \
  -p 5432:5432 \
  postgres:14

# Run tests against PostgreSQL
DATABASE_URL=postgresql://testuser:testpass@localhost:5432/test_travel_agency \
pytest tests/ -v
```

### Run Linting Locally

```bash
# Install linting tools
pip install flake8 black isort pylint mypy

# Run checks
flake8 .
black --check .
isort --check-only .
pylint app.py routes/ models/
mypy app.py routes/ models/ --ignore-missing-imports
```

### Run Security Checks Locally

```bash
# Install security tools
pip install bandit safety pip-audit

# Run checks
bandit -r . --exclude ./tests
safety check
pip-audit
```

---

## Troubleshooting

### Tests Fail on PostgreSQL Connection

**Issue:** `psycopg2: could not translate host name "postgres"`

**Solution:** Ensure `DATABASE_URL` is set correctly in test environment:
```bash
DATABASE_URL=postgresql://testuser:testpass@localhost:5432/test_travel_agency
```

### Deployment Fails with SSH Error

**Issue:** `Permission denied (publickey)`

**Solution:**
1. Verify SSH key is in GitHub Secrets
2. Check public key is in `~/.ssh/authorized_keys` on server
3. Verify SSH key permissions: `chmod 600 ~/.ssh/authorized_keys`

### Coverage Threshold Not Met

**Issue:** "Coverage is below 70% threshold"

**Solution:**
1. Write tests for uncovered code
2. Or lower threshold in `coverage.yml`: `--fail-under=50`

### Security Scan False Positives

**Issue:** Bandit reports false positives

**Solution:**
1. Add inline comments to suppress: `# nosec`
2. Update Bandit configuration in `.bandit`

---

## Deployment Process

### Staging Deployment (Automatic)

```
Push to develop branch
    ↓
Tests run (must pass)
    ↓
Code quality checks (must pass)
    ↓
Security scan (warnings allowed)
    ↓
Deploy to staging
    ↓
Health check
    ↓
Done! Staging is updated
```

### Production Deployment (Manual)

```
Go to Actions → Deploy to Production → Run workflow
    ↓
Enter version number (e.g., 1.0.0)
    ↓
Select environment (staging/production)
    ↓
Comprehensive tests run (must pass)
    ↓
Security checks (must pass)
    ↓
Database backup created
    ↓
Deploy to production
    ↓
Health checks (20 attempts)
    ↓
Smoke tests
    ↓
Done! Production is updated
    ↓
Release notes created on GitHub
```

---

## Monitoring CI/CD

### GitHub Actions Dashboard

Visit: https://github.com/YOUR_ORG/travel_agency_enhanced/actions

View:
- Running workflows
- Recent workflow runs
- Success/failure history
- Log details for debugging

### Slack Notifications (Optional)

Configure Slack webhook to receive notifications:

1. Create Slack webhook: https://api.slack.com/messaging/webhooks
2. Add to GitHub Secrets: `SLACK_WEBHOOK`
3. Webhooks automatically notify on deployment

### Email Notifications (Default)

GitHub automatically emails on workflow failures.

Configure in Repository Settings → Notifications

---

## Performance Optimization

### Caching

Workflows use pip caching to speed up dependency installation:

```yaml
- uses: actions/setup-python@v4
  with:
    python-version: '3.11'
    cache: 'pip'  # Automatically caches pip packages
```

### Parallel Jobs

Jobs run in parallel when possible:
- Linting tests run in parallel
- Security scans run in parallel
- Only `deploy-staging` waits for `test` to complete

### Time Estimates

Typical workflow execution times:
- **Tests**: 5-10 minutes (with 3 Python versions)
- **Code Quality**: 2-3 minutes
- **Security Scan**: 3-5 minutes
- **Coverage**: 5-10 minutes
- **Staging Deploy**: 2-3 minutes
- **Production Deploy**: 3-5 minutes

---

## Cost Considerations

GitHub Actions free tier includes:
- ✅ 2,000 minutes per month for private repositories
- ✅ Unlimited for public repositories
- ✅ Sufficient for most development workflows

Current estimated usage: ~100-150 minutes/month for active development

---

## Next Steps

1. **Enable workflows**: Commit `.github/workflows/` files
2. **Configure secrets**: Add deployment credentials to GitHub
3. **Set branch rules**: Require status checks on main/develop
4. **Add badges**: Update README with workflow status
5. **Test pipeline**: Push to develop and watch workflow execute

---

## Useful Links

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Codecov Integration](https://github.com/codecov/codecov-action)
- [Setup Python Action](https://github.com/actions/setup-python)

---

**Status:** ✅ CI/CD pipeline configured and ready to use!
