# GitHub Configuration

This directory contains GitHub-specific configuration files for the Travel Agency Enhanced project.

## Contents

### Workflows (`.github/workflows/`)

Automated CI/CD workflows for testing, quality checks, security scanning, and deployment.

- **`tests.yml`** - Automated testing on Python 3.9, 3.10, 3.11
- **`lint.yml`** - Code quality checks (flake8, black, isort, pylint, mypy)
- **`security.yml`** - Security scanning (Bandit, pip-audit, CodeQL, Trivy)
- **`coverage.yml`** - Code coverage reporting and threshold enforcement
- **`deploy-staging.yml`** - Automatic deployment to staging from develop branch
- **`deploy-production.yml`** - Manual production deployment with safety checks

### Templates (`.github/ISSUE_TEMPLATE/`)

Standardized issue templates for consistent bug reports and feature requests.

- **`bug_report.md`** - Report bugs and issues
- **`feature_request.md`** - Suggest new features or enhancements
- **`performance_issue.md`** - Report performance problems
- **`security_issue.md`** - Report security vulnerabilities responsibly
- **`config.yml`** - Configure issue template settings

### Pull Request Template (`.github/`)

- **`pull_request_template.md`** - Standardized PR description template

### Code Ownership (`.github/`)

- **`CODEOWNERS`** - Define code ownership and required reviewers

## Workflow Status

All workflows are production-ready and fully automated. Current status:

| Workflow | Trigger | Status |
|----------|---------|--------|
| Tests | Push/PR to main, develop | ✅ Active |
| Linting | Push/PR to main, develop | ✅ Active |
| Security | Push/PR + daily 2 AM UTC | ✅ Active |
| Coverage | Push/PR to main, develop | ✅ Active |
| Staging Deploy | Push to develop | ✅ Active |
| Production Deploy | Manual trigger on main | ✅ Active |

## Quick Links

- [Full CI/CD Guide](../CI_CD_PIPELINE_GUIDE.md)
- [GitHub Actions Setup](../GITHUB_ACTIONS_SETUP.md)
- [Production Readiness](../DEPLOYMENT_PRODUCTION_READINESS.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [Security Policy](../SECURITY.md)

## Setting Up

### 1. Enable Workflows

Workflows are automatically enabled when files are in `.github/workflows/`.

Verify in GitHub: Settings → Actions

### 2. Configure Secrets

For deployment workflows, add GitHub secrets:

```bash
PROD_HOST
PROD_USER
PROD_PATH
PROD_DEPLOY_KEY
PROD_URL
SLACK_WEBHOOK (optional)
```

See [GitHub Actions Setup](../GITHUB_ACTIONS_SETUP.md) for details.

### 3. Set Branch Protection

Configure branch protection rules on main:

- ✅ Require status checks to pass
- ✅ Require code review
- ✅ Require branches up to date

## Issue Templates

### Using Issue Templates

When creating an issue on GitHub, select the appropriate template:

1. Go to Issues → New Issue
2. Choose your template
3. Fill out all required fields
4. Submit

### Template Types

- **Bug Report** - Something isn't working properly
- **Feature Request** - Suggest a new feature or enhancement
- **Performance Issue** - Report slow or resource-heavy features
- **Security Issue** - Report vulnerabilities responsibly

## Pull Request Template

Every PR should use the template. It includes:

- Description of changes
- Type of change (bug fix, feature, etc.)
- Related issues
- Testing information
- Breaking changes
- Checklists for reviewers

## Code Owners

CODEOWNERS file specifies who should review changes to specific files:

```
routes/auth.py              @auth-team @backend-team
routes/admin.py             @admin-team
models/                     @database-team
```

When PRs are opened, code owners are automatically requested for review.

## Workflow Details

### Tests Workflow

```yaml
Runs on: Push, Pull Request
Python: 3.9, 3.10, 3.11
Database: PostgreSQL 14
Coverage: 70% minimum required
```

**Steps:**
1. Set up Python
2. Install dependencies
3. Run pytest with coverage
4. Upload to Codecov
5. Check coverage threshold

### Linting Workflow

```yaml
Runs on: Push, Pull Request
Tools: flake8, black, isort, pylint, mypy, pip-audit, bandit
```

**Steps:**
1. Lint with flake8
2. Format check with black
3. Sort check with isort
4. Type check with mypy
5. Security check with bandit

### Security Workflow

```yaml
Runs on: Push, Pull Request, Daily at 2 AM UTC
Scanners: 7 different security tools
```

**Scanners:**
- pip-audit - Dependency vulnerabilities
- Trivy - Filesystem scanning
- CodeQL - Code analysis
- Bandit - Python security
- Semgrep - SAST
- Safety - Dependency checker
- detect-secrets - Secret scanning

### Deployment Workflows

**Staging** - Automatic on develop push
**Production** - Manual trigger on main

Both include:
- Full test suite
- Security checks
- Database backup
- Health checks

## Monitoring Workflows

View workflow status in GitHub:

1. Go to Actions tab
2. Select workflow
3. View current/past runs
4. Check logs for details

## Troubleshooting

### Workflow Not Running

**Check:**
- Files are in `.github/workflows/`
- Branch matches trigger condition
- GitHub Actions is enabled (Settings → Actions)

### Tests Failing

**Check:**
- Python version matches workflow
- Dependencies installed correctly
- Environment variables set
- Database is accessible

### Deployment Failed

**Check:**
- GitHub Secrets are configured
- SSH keys have correct permissions
- Deployment server is accessible
- Health check endpoint works

## Status Badges

Add workflow status badges to README:

```markdown
![Tests](https://github.com/your-org/repo/workflows/Tests/badge.svg)
![Linting](https://github.com/your-org/repo/workflows/Linting/badge.svg)
![Security](https://github.com/your-org/repo/workflows/Security/badge.svg)
```

## Performance

Typical workflow execution times:

| Workflow | Duration | Frequency |
|----------|----------|-----------|
| Tests | 5-10 min | Every push/PR |
| Linting | 2-3 min | Every push/PR |
| Security | 3-5 min | Push/PR/daily |
| Coverage | 5-10 min | Every push/PR |
| Staging Deploy | 2-3 min | On develop push |
| Production Deploy | 3-5 min | Manual |

**Monthly Usage:** ~550 minutes (within GitHub Actions free tier of 2,000 min/month)

## Security

GitHub Actions workflows have access to secrets but:

- Secrets are not printed in logs
- Secrets are masked in output
- Secrets are only available to intended workflows
- Secrets are encrypted at rest

Never commit secrets to the repository.

## Next Steps

1. Verify all workflows in Actions tab
2. Configure GitHub Secrets for deployment
3. Set up branch protection rules
4. Test PR workflow
5. Monitor first deployment

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

## Support

For issues with GitHub Actions:

- Check workflow logs in Actions tab
- Review [CI/CD Pipeline Guide](../CI_CD_PIPELINE_GUIDE.md)
- See [GitHub Actions Setup](../GITHUB_ACTIONS_SETUP.md)
- Open an issue on GitHub

---

**Status:** ✅ Production Ready

*Last Updated: January 2024*
