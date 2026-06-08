# GitHub Actions Setup Instructions

## Quick Start

Complete these steps to enable CI/CD for your Travel Agency application:

## Step 1: Push Code to GitHub

Ensure your repository is on GitHub with the correct branch structure:

```bash
git push origin main
git push origin develop
```

## Step 2: Enable Workflows

GitHub Actions should automatically detect the workflow files. To verify:

1. Go to your repository on GitHub
2. Click on **Actions** tab
3. You should see workflows:
   - Tests
   - Code Quality
   - Security Scanning
   - Code Coverage

## Step 3: Configure GitHub Secrets

### For Testing (Automatic)

Tests use GitHub Actions service containers, so no manual configuration needed.

### For Staging Deployment (Optional)

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add:

```
STAGING_HOST          staging.example.com
STAGING_USER          deploy
STAGING_PATH          /var/www/travel-agency
STAGING_DEPLOY_KEY    (paste SSH private key)
STAGING_URL           https://staging.example.com
```

### For Production Deployment (Optional)

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add:

```
PROD_HOST             prod.example.com
PROD_USER             deploy
PROD_PATH             /var/www/travel-agency
PROD_DEPLOY_KEY       (paste SSH private key)
PROD_URL              https://travel-agency.com
SLACK_WEBHOOK         https://hooks.slack.com/services/... (optional)
```

## Step 4: Configure Branch Protection Rules

### For Main Branch (Production)

1. Go to **Settings** → **Branches**
2. Click **Add rule** under Branch protection rules
3. Enter branch name: `main`
4. Configure:
   - ✓ Require a pull request before merging
   - ✓ Require status checks to pass before merging
   - ✓ Require branches to be up to date
   
5. Select required status checks:
   - `test (3.9)`
   - `test (3.10)`
   - `test (3.11)`
   - `lint` (optional)
   - `coverage` (optional)

6. ✓ Dismiss stale pull request approvals when new commits are pushed
7. ✓ Require code review from at least 1 person

### For Develop Branch (Development)

1. Go to **Settings** → **Branches**
2. Click **Add rule** under Branch protection rules
3. Enter branch name: `develop`
4. Configure same as main but with fewer reviewers if desired

## Step 5: Set up Codecov (Optional)

For detailed code coverage reports:

1. Visit https://codecov.io
2. Sign in with GitHub
3. Select this repository
4. Codecov will automatically receive coverage reports from Actions

## Step 6: Create SSH Deploy Keys (For Deployment)

### Generate Keys

```bash
ssh-keygen -t ed25519 -f deploy_key -N ""
```

This creates:
- `deploy_key` (private key - goes to GitHub)
- `deploy_key.pub` (public key - goes to server)

### Add Public Key to Server

SSH into your deployment server:

```bash
# Create deploy user (if not exists)
sudo useradd -m deploy
sudo su - deploy

# Add public key
mkdir -p ~/.ssh
cat deploy_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### Add Private Key to GitHub

1. Cat the private key content:
   ```bash
   cat deploy_key
   ```

2. Go to GitHub **Settings** → **Secrets and variables** → **Actions**

3. Create secret:
   - Name: `STAGING_DEPLOY_KEY` (or `PROD_DEPLOY_KEY`)
   - Value: (paste entire private key including -----BEGIN/END lines)

## Step 7: Test the Pipeline

### Trigger Tests

1. Create a new branch:
   ```bash
   git checkout -b feature/test-ci-cd
   ```

2. Make a small change:
   ```bash
   echo "# CI/CD Test" >> README.md
   git add README.md
   git commit -m "Test CI/CD pipeline"
   git push origin feature/test-ci-cd
   ```

3. Create Pull Request on GitHub
4. Watch the workflows run under the **Checks** section
5. Merge PR once checks pass

### Monitor Workflow Execution

1. Go to **Actions** tab
2. Click on the workflow run
3. View job details and logs

## Step 8: Add Status Badges

Add these to your README.md to show workflow status:

```markdown
## Status

[![Tests](https://github.com/YOUR_ORG/travel_agency_enhanced/workflows/Tests/badge.svg)](https://github.com/YOUR_ORG/travel_agency_enhanced/actions/workflows/tests.yml)
[![Code Quality](https://github.com/YOUR_ORG/travel_agency_enhanced/workflows/Code%20Quality/badge.svg)](https://github.com/YOUR_ORG/travel_agency_enhanced/actions/workflows/lint.yml)
[![Security](https://github.com/YOUR_ORG/travel_agency_enhanced/workflows/Security%20Scanning/badge.svg)](https://github.com/YOUR_ORG/travel_agency_enhanced/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/YOUR_ORG/travel_agency_enhanced/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_ORG/travel_agency_enhanced)
```

Replace `YOUR_ORG` with your GitHub organization name.

## Workflow Triggers

### Automatic (Always Active)

- **Tests**: Push or PR to main/develop
- **Code Quality**: Push or PR to main/develop
- **Security Scanning**: Push or PR to main/develop, daily schedule

### Manual (On Demand)

- **Staging Deploy**: Push to develop OR click "Run workflow" in Actions
- **Production Deploy**: Click "Run workflow" on main branch

## Troubleshooting

### Workflows Not Running

**Check:**
1. Are files in `.github/workflows/` committed?
2. Is the branch push-protected? (workflows don't run on protected branches without PRs)
3. Are you on the correct branch (main/develop)?

### Tests Failing Locally But Passing in CI

**Cause:** Different environment or database

**Solution:**
1. Use same Python version locally as in CI (3.11)
2. Use PostgreSQL locally instead of SQLite for tests
3. Check `.env` file has TEST configuration

### Deployment Fails with SSH Error

**Check:**
1. SSH key is in GitHub Secrets
2. Public key is in `~/.ssh/authorized_keys` on server
3. SSH key has correct format (includes BEGIN/END lines)
4. User has write permissions to deploy path

### Coverage Lower Than Expected

**Cause:** Incomplete test coverage

**Solution:**
1. Write tests for uncovered code paths
2. Or temporarily lower threshold in `coverage.yml`
3. Or exclude certain files from coverage

## Advanced Configuration

### Environment Variables

Add environment-specific variables to **Settings** → **Environments**:

```
Environment: staging
Variables:
  DEBUG=false
  LOG_LEVEL=INFO

Environment: production
Variables:
  DEBUG=false
  LOG_LEVEL=WARNING
```

### Notifications

Configure Slack notifications:

1. Create Slack App: https://api.slack.com/messaging/webhooks
2. Add incoming webhook
3. Add `SLACK_WEBHOOK` secret to GitHub
4. Workflows will notify on deployment

### Custom Workflow Runs

Manually trigger any workflow:

1. Go to **Actions** → Select Workflow
2. Click **Run workflow** dropdown
3. Select branch and inputs
4. Click **Run workflow**

## Monitoring

### GitHub Actions Dashboard

- **URL:** https://github.com/YOUR_ORG/travel_agency_enhanced/actions
- **View:** All workflows, runs, success rate
- **Alerts:** Failures automatically notify via email

### Workflow Run Details

- Click on any run to see job details
- View real-time logs for each job
- Download artifacts (coverage reports, etc.)

### Performance Metrics

- Typical test run: 5-10 minutes
- Linting: 2-3 minutes
- Security scan: 3-5 minutes
- Total PR check time: ~15 minutes

## Best Practices

1. **Always use pull requests** - Never push directly to main
2. **Keep branches updated** - Rebase develop into feature branches
3. **Review test results** - Check coverage and linting before merging
4. **Document changes** - Use meaningful commit messages
5. **Tag releases** - Use semantic versioning (v1.0.0)
6. **Backup before deploy** - Always create database backup before production deploy

## Cost Calculation

GitHub Actions free tier: 2,000 minutes/month

Estimated monthly usage:
- Tests (3 versions): 10 min × 20 runs = 200 min
- Linting: 3 min × 20 runs = 60 min
- Security: 5 min × 20 runs = 100 min
- Coverage: 8 min × 20 runs = 160 min
- Staging deploy: 3 min × 10 runs = 30 min
- **Total: ~550 minutes** ✓ Within free tier

## Support

For issues with GitHub Actions:

- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Help & Feedback](https://github.com/actions/setup-python/issues)

## Checklist

- [ ] Code pushed to GitHub on main and develop branches
- [ ] Workflow files created in `.github/workflows/`
- [ ] Branch protection rules configured for main
- [ ] GitHub Secrets configured (if using deployment)
- [ ] SSH keys generated and added to servers (if using deployment)
- [ ] First test run completed successfully
- [ ] Coverage threshold met
- [ ] Status badges added to README
- [ ] Team notified of CI/CD setup

---

✅ **CI/CD Pipeline is ready!**

Your Travel Agency application now has:
- ✓ Automated testing on every commit
- ✓ Code quality checks
- ✓ Security scanning
- ✓ Code coverage tracking
- ✓ Automatic staging deployment
- ✓ Manual production deployment with safeguards
