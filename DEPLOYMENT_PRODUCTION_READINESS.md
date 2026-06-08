# Deployment & Production Readiness Guide

This document provides step-by-step instructions for deploying the Travel Agency application to production.

## Pre-Deployment Checklist

### Code Quality & Testing ✓

- [ ] All tests pass locally: `pytest tests/ -v`
- [ ] Coverage meets threshold (70%): `pytest tests/ --cov --cov-report=term-missing`
- [ ] Linting passes: `flake8 .` and `black --check .`
- [ ] Type checking passes: `mypy app.py routes/ models/ --ignore-missing-imports`
- [ ] No security issues: `bandit -r . --exclude ./tests`

### Dependencies & Versions ✓

- [ ] `requirements.txt` is up to date
- [ ] No vulnerable dependencies: `pip-audit`
- [ ] Python version: 3.9, 3.10, or 3.11
- [ ] PostgreSQL version: 12 or higher
- [ ] All external services configured (email, backups, etc.)

### Environment Configuration ✓

- [ ] `.env` file configured for production
- [ ] Database connection tested
- [ ] Email service tested (send verification email)
- [ ] Backup system tested
- [ ] Static files collected: `flask collect-static` (if applicable)
- [ ] Database migrations ready: `flask db upgrade`

### Security Audit ✓

- [ ] HTTPS enabled on domain
- [ ] Database password is strong (20+ characters, mixed case, numbers, symbols)
- [ ] SECRET_KEY is unique and strong
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] SQL injection tests passed
- [ ] XSS vulnerability tests passed
- [ ] Session security verified

### Infrastructure Readiness ✓

- [ ] Production server prepared (Linux/Ubuntu)
- [ ] Python 3.11 installed on server
- [ ] PostgreSQL installed and configured on server
- [ ] Nginx reverse proxy configured
- [ ] SSL certificate installed
- [ ] Firewall rules configured (allow 80, 443, deny others)
- [ ] SSH keys set up for deployment
- [ ] Backup storage location ready
- [ ] Monitoring tools installed (optional)

### Documentation & Handoff ✓

- [ ] README.md updated with deployment instructions
- [ ] API documentation available (if applicable)
- [ ] Admin credentials reset and communicated securely
- [ ] Runbook created for common operations
- [ ] Incident response plan documented
- [ ] Team trained on deployment process

---

## Deployment Steps

### Option 1: GitHub Actions Deployment (Automated - Recommended)

#### Prerequisites

1. **Repository on GitHub** with main and develop branches
2. **GitHub Secrets configured**:
   - PROD_HOST
   - PROD_USER
   - PROD_PATH
   - PROD_DEPLOY_KEY
   - PROD_URL
   - SLACK_WEBHOOK (optional)

#### Deployment Process

1. **Prepare Release**
   ```bash
   # Switch to main branch
   git checkout main
   git pull origin main
   
   # Create version tag
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. **Trigger Deployment**
   - Go to GitHub Actions → Deploy to Production
   - Click "Run workflow"
   - Enter version: `1.0.0`
   - Select environment: `production`
   - Click "Run workflow"

3. **Monitor Deployment**
   - Watch progress in GitHub Actions
   - Receive notifications (email/Slack)
   - Deployment creates backup automatically
   - Health checks run automatically

4. **Verify Deployment**
   - Check application is running: `https://your-domain.com`
   - Review application logs
   - Run smoke tests

### Option 2: Manual Deployment

#### Prerequisites

1. SSH access to production server
2. Application source code ready
3. Database backups configured

#### Deployment Steps

```bash
# 1. SSH into production server
ssh deploy@your-domain.com

# 2. Navigate to application directory
cd /var/www/travel-agency

# 3. Create database backup
python scripts/run_backup.py

# 4. Pull latest code
git fetch origin
git checkout main
git pull origin main

# 5. Create fresh virtualenv (optional but recommended)
python -m venv venv
source venv/bin/activate

# 6. Install dependencies
pip install -r requirements.txt
pip install gunicorn

# 7. Build static files (if applicable)
flask collect-static

# 8. Run database migrations
flask db upgrade

# 9. Restart application service
sudo systemctl restart travel-agency

# 10. Check logs
sudo journalctl -u travel-agency -f

# 11. Verify with health check
curl https://your-domain.com/health
```

---

## Post-Deployment Verification

### Application Health

```bash
# Check HTTP response
curl -I https://your-domain.com

# Check application status
curl https://your-domain.com/health

# Check database connectivity
flask shell
# >>> from models import db
# >>> db.session.execute("SELECT 1")
```

### Database Health

```bash
# Connect to database
psql -h localhost -U postgres -d travel_agency

# Check tables exist
\dt

# Count records
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM bookings;
SELECT COUNT(*) FROM tour_packages;

# Check recent backups
SELECT * FROM backups ORDER BY created_at DESC LIMIT 5;
```

### Logs & Monitoring

```bash
# View application logs
tail -f /var/log/travel-agency/app.log

# View access logs
tail -f /var/log/nginx/access.log

# Check system resource usage
top
free -h
df -h

# Monitor backup system
python scripts/manage_backups.py stats
```

### Security Verification

```bash
# Test HTTPS
openssl s_client -connect your-domain.com:443

# Test rate limiting
for i in {1..20}; do curl -H "X-Forwarded-For: 127.0.0.1" https://your-domain.com/api/; done

# Check session security headers
curl -I https://your-domain.com | grep -i "secure\|httponly\|samesite"
```

---

## Rollback Procedure

If deployment has issues:

### Automatic Rollback (GitHub Actions)

If health checks fail during deployment, GitHub Actions will:
1. Stop the deployment
2. Restore from backup
3. Restart the previous version
4. Send notification

### Manual Rollback

```bash
# SSH into server
ssh deploy@your-domain.com

# List available backups
python scripts/manage_backups.py list

# Restore specific backup
python scripts/manage_backups.py restore backups/travel_agency_2024-01-15_10-30-45.sql.gz

# Restore application code to previous version
cd /var/www/travel-agency
git checkout HEAD~1
git pull

# Restart application
sudo systemctl restart travel-agency

# Verify
curl https://your-domain.com/health
```

---

## Monitoring & Maintenance

### Daily Tasks

- [ ] Check application health
- [ ] Review error logs
- [ ] Verify backups completed

### Weekly Tasks

- [ ] Review user activity
- [ ] Check database size
- [ ] Test backup restoration

### Monthly Tasks

- [ ] Review security logs
- [ ] Update dependencies (if security patches available)
- [ ] Run performance tests
- [ ] Review and optimize slow queries

---

## Scaling & Performance

### If Application Becomes Slow

1. **Check Database**
   ```bash
   # Identify slow queries
   SELECT query, calls, total_time FROM pg_stat_statements 
   ORDER BY total_time DESC LIMIT 10;
   ```

2. **Add Database Indexes**
   ```sql
   CREATE INDEX idx_bookings_user ON bookings(user_id);
   CREATE INDEX idx_inquiries_email ON inquiries(email);
   ```

3. **Increase Application Servers**
   - Add more Gunicorn workers
   - Configure load balancing

4. **Add Caching**
   - Redis for session storage
   - Memcached for query results

### If Storage Gets Full

```bash
# Check disk usage
du -sh /var/www/travel-agency

# Clean old backups (beyond retention)
python scripts/manage_backups.py cleanup

# Check upload directory size
du -sh /var/www/travel-agency/uploads/

# Archive old uploads
tar -czf old_uploads_backup.tar.gz uploads/
```

---

## Troubleshooting

### 502 Bad Gateway

**Cause:** Application server not running

```bash
# Check status
systemctl status travel-agency

# Restart
sudo systemctl restart travel-agency

# View logs
sudo journalctl -u travel-agency -n 50
```

### Database Connection Refused

**Cause:** PostgreSQL not running

```bash
# Check status
sudo systemctl status postgresql

# Restart
sudo systemctl restart postgresql

# Check connectivity
psql -h localhost -U postgres -c "SELECT 1"
```

### Email Not Sending

**Cause:** Email service configuration

```bash
# Test email configuration
flask shell
>>> from email_service import EmailService
>>> EmailService.test_connection()

# Check logs
tail -f /var/log/mail.log
```

### Backups Not Creating

**Cause:** Backup service not running or insufficient permissions

```bash
# Check backup scheduler status
python scripts/manage_backups.py stats

# Manual backup test
python scripts/run_backup.py

# Check backup directory permissions
ls -la /var/www/travel-agency/backups/
```

---

## Emergency Contacts

Save these numbers/emails:

```
System Administrator: [admin@company.com]
Database Administrator: [dba@company.com]
Security Team: [security@company.com]
Hosting Provider Support: [support@provider.com]
```

---

## Success Criteria

After deployment, verify:

- ✓ Application loads in browser
- ✓ Users can register and login
- ✓ Bookings can be created
- ✓ Admin panel accessible with admin account
- ✓ Emails sending correctly
- ✓ Backups created successfully
- ✓ All tests passing on CI/CD
- ✓ No errors in logs
- ✓ HTTPS working correctly
- ✓ Rate limiting working

---

## Version History

| Version | Date | Deployed By | Status |
|---------|------|-------------|--------|
| 1.0.0 | - | - | Pending |

---

## Additional Resources

- [Flask Deployment Guide](https://flask.palletsprojects.com/deployment/)
- [PostgreSQL Administration](https://www.postgresql.org/docs/current/admin.html)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [SSL/TLS Best Practices](https://wiki.mozilla.org/Security/Server_Side_TLS)

---

**Last Updated:** January 2024
**Status:** Production Ready ✅
