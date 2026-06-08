# Email Verification Implementation Guide

## Overview

The Travel Agency application now includes a complete email verification system that requires users to verify their email address before they can log in and book tours. This feature improves data quality and prevents spam registrations.

## Architecture

### Components

1. **EmailVerificationToken Model** (`models/email_verification.py`)
   - Stores verification tokens in the database
   - Tracks token creation, expiration, and usage
   - Includes methods for token generation and validation

2. **EmailVerificationService** (`email_verification_service.py`)
   - Manages token creation and verification workflows
   - Sends verification emails
   - Handles token resending
   - Cleans up expired tokens

3. **User Model Updates** (`models/user.py`)
   - Added `email_verified` (Boolean) - marks if email is verified
   - Added `email_verified_at` (DateTime) - when email was verified

4. **Auth Routes** (`routes/auth.py`)
   - Modified registration to require email verification
   - Added `/auth/verify-email/<token>` route
   - Added `/auth/resend-verification` route
   - Added `/auth/pending-verification` page
   - Modified login to check email verification

## User Flow

### Registration with Email Verification

```
1. User fills out registration form
   ↓
2. System creates user account (email_verified = False)
   ↓
3. System generates verification token (24-hour expiration)
   ↓
4. System sends verification email with unique link
   ↓
5. User redirected to pending verification page
   ↓
6. User clicks link in email
   ↓
7. System verifies token and marks user.email_verified = True
   ↓
8. User can now log in
```

### Login with Email Verification Check

```
1. User enters credentials
   ↓
2. System validates credentials
   ↓
3. System checks if email_verified == True
   ↓
4. If not verified → Redirect to pending verification page
   ↓
5. If verified → Allow login
```

### Resending Verification Email

```
1. User clicks "Resend Verification Email" link
   ↓
2. System checks if user exists and email not yet verified
   ↓
3. System invalidates previous tokens
   ↓
4. System creates new verification token
   ↓
5. System sends verification email
   ↓
6. User receives new email with fresh token (24-hour expiration)
```

## Database Schema

### email_verification_tokens Table

```sql
CREATE TABLE email_verification_tokens (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL (indexed),
    token VARCHAR(128) NOT NULL UNIQUE (indexed),
    email VARCHAR(150) NOT NULL,
    created_at DATETIME NOT NULL (indexed),
    expires_at DATETIME NOT NULL (indexed),
    verified_at DATETIME NULL,
    is_used BOOLEAN NOT NULL DEFAULT FALSE (indexed),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### users Table (New Columns)

```sql
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE (indexed);
ALTER TABLE users ADD COLUMN email_verified_at DATETIME NULL;
```

## API Reference

### EmailVerificationService

#### create_verification_token(user_id, email, expires_in_hours=24)

Creates a new verification token for a user.

**Parameters:**
- `user_id` (int) - User ID to create token for
- `email` (str) - Email address to verify
- `expires_in_hours` (int) - Token expiration time (default: 24 hours)

**Returns:**
- `token` (str) - The verification token

**Raises:**
- `ValueError` - If user not found

**Example:**
```python
from email_verification_service import EmailVerificationService

token = EmailVerificationService.create_verification_token(
    user_id=1,
    email='user@example.com',
    expires_in_hours=24
)
```

#### send_verification_email(user_email, user_name, token, is_resend=False)

Sends verification email to user.

**Parameters:**
- `user_email` (str) - Email address to send to
- `user_name` (str) - User's name for greeting
- `token` (str) - Verification token
- `is_resend` (bool) - Whether this is a resend

**Returns:**
- `bool` - True if email sent successfully

**Example:**
```python
success = EmailVerificationService.send_verification_email(
    user_email='user@example.com',
    user_name='John Doe',
    token=token,
    is_resend=False
)
```

#### verify_email(token)

Verifies email with token.

**Parameters:**
- `token` (str) - Verification token from email

**Returns:**
- Tuple of `(success: bool, message: str, user: User or None)`

**Example:**
```python
success, message, user = EmailVerificationService.verify_email(token)
if success:
    print(f"Email verified for {user.email}")
else:
    print(f"Verification failed: {message}")
```

#### resend_verification_email(email)

Resends verification email to user.

**Parameters:**
- `email` (str) - User's email address

**Returns:**
- Tuple of `(success: bool, message: str)`

**Example:**
```python
success, message = EmailVerificationService.resend_verification_email('user@example.com')
```

#### cleanup_expired_tokens()

Cleans up expired verification tokens from database.

**Returns:**
- `int` - Number of tokens deleted

**Example:**
```python
deleted_count = EmailVerificationService.cleanup_expired_tokens()
print(f"Deleted {deleted_count} expired tokens")
```

## Routes

### POST /auth/register

**Changes:**
- User registration now requires email verification
- User account created with `email_verified = False`
- Verification email sent automatically
- Redirects to `/auth/pending-verification`

### GET /auth/verify-email/<token>

**Purpose:** Verify user email with token from email link

**Parameters:**
- `token` (str) - Verification token

**Response:**
- Success: Redirects to login with success message
- Failure: Redirects to pending verification with error message

### GET /auth/pending-verification

**Purpose:** Show page for user to verify their email

**Parameters:**
- `email` (str, optional) - Email address being verified

**Response:**
- HTML page showing pending verification status

### GET/POST /auth/resend-verification

**Purpose:** Resend verification email to user

**Methods:**
- GET: Show form to enter email
- POST: Send verification email

**Parameters:**
- `email` (str) - Email address to resend to

**Response:**
- Redirects to pending verification page with status message

## Templates

### auth/pending_verification.html

Shows user that verification email has been sent. Includes:
- Email address being verified
- Instructions to check email
- Link to resend verification email
- Link to login after verification

### auth/resend_verification.html

Form for resending verification email. Includes:
- Email input field
- Submit button
- Links to login and register

## Email Content

### Verification Email (Initial)

**Subject:** "Verify Your Email Address"

**Body includes:**
- Greeting with user name
- Explanation of registration
- Verification button/link
- Link expiration notice (24 hours)
- Note about spam folder

### Verification Email (Resend)

**Subject:** "Re-verify Your Email"

**Body includes:**
- Greeting with user name
- Explanation of resend
- Verification button/link
- Link expiration notice (24 hours)

## Database Migration

Run the migration to add email verification tables:

```bash
# Using Alembic
flask db upgrade

# Or manually
python scripts/create_database.py
```

### Migration: d1a8f8c3b2a1_add_email_verification

**Changes:**
- Adds `email_verified` and `email_verified_at` columns to `users` table
- Creates `email_verification_tokens` table with proper indexes and foreign keys

**Rollback:**
```bash
flask db downgrade
```

## Testing

### Running Tests

```bash
# Run all email verification tests
pytest tests/test_email_verification.py -v

# Run specific test class
pytest tests/test_email_verification.py::TestEmailVerificationToken -v

# Run with coverage
pytest tests/test_email_verification.py --cov=models --cov=email_verification_service
```

### Test Coverage

The test suite includes:

1. **Model Tests** (`TestEmailVerificationToken`)
   - Token generation
   - Token expiration
   - Token validation
   - Token verification
   - Already-used token handling

2. **Service Tests** (`TestEmailVerificationService`)
   - Token creation
   - Email verification
   - Resend verification
   - Token cleanup

3. **Route Tests** (`TestEmailVerificationRoutes`)
   - Registration with email verification
   - Login requires verified email
   - Email verification route
   - Pending verification page
   - Resend verification route

## Configuration

### Email Service Configuration

Update your Flask configuration in `app.py`:

```python
# Mail configuration
MAIL_SERVER = 'smtp.gmail.com'  # or your email provider
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@travelagency.com')
```

### Environment Variables

```bash
# .env file
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # Not your regular password!
MAIL_DEFAULT_SENDER=noreply@travelagency.com
```

### Token Expiration

Default token expiration is 24 hours. To change:

```python
# In registration route
token = EmailVerificationService.create_verification_token(
    user.id,
    user.email,
    expires_in_hours=48  # 48 hours instead of default 24
)
```

## Security Considerations

1. **Token Security:**
   - Tokens are cryptographically secure (using `secrets.token_urlsafe`)
   - Tokens are unique and indexed in database
   - Tokens expire after 24 hours
   - Tokens cannot be reused after verification

2. **Email Security:**
   - Email addresses are case-insensitive (converted to lowercase)
   - Verification links use HTTPS only in production
   - Email contains no sensitive information

3. **Database Security:**
   - Tokens are indexed for fast lookup
   - Foreign key constraints on user_id
   - Automatic cleanup of expired tokens recommended

4. **Rate Limiting:**
   - Resend verification: 3 per minute (prevents brute force)
   - Registration: 10 per minute (prevents spam)

## Logging

All email verification events are logged via `StructuredLogger`:

```python
# Log successful verification
StructuredLogger.log_auth_event('verification_token_created', email, True)

# Log failed verification
StructuredLogger.log_error('email_verification', 'Failed to verify email', {}, 'ERROR')

# Log email sent
StructuredLogger.log_auth_event('verification_email_sent', email, True)
```

## Maintenance Tasks

### Cleanup Expired Tokens

Schedule this to run periodically (daily recommended):

```bash
# Via command line
python -c "from email_verification_service import EmailVerificationService; EmailVerificationService.cleanup_expired_tokens()"

# Or in a Flask CLI command
flask verify cleanup-tokens
```

### Monitor Verification Rates

Track statistics in logs:
- Registrations per day
- Verification success rate
- Resend request rate
- Token expiration rate

## Troubleshooting

### Verification Email Not Received

1. Check spam/junk folder
2. Verify email configuration in `.env`
3. Check application logs for email sending errors
4. Test email service: `python -m pytest tests/test_email_verification.py`

### Token Expired

- Tokens expire after 24 hours
- User can request new token via "Resend Verification Email" link
- Only 3 resend requests allowed per minute

### User Cannot Log In

Possible causes:
1. Email not verified - redirect to pending verification
2. Invalid password - show error message
3. Account doesn't exist - show error message

Check logs for specific error details.

## Future Enhancements

1. **Configurable Expiration:**
   - Allow different expiration times per registration wave
   - Different expiration for resend tokens

2. **Email Verification on Login:**
   - Re-verify email after certain time period
   - Verify new email change before updating profile

3. **Multi-factor Authentication:**
   - Add phone verification option
   - Add OTP (one-time password) verification

4. **Analytics:**
   - Track verification completion rates
   - Monitor email bounce rates
   - A/B test email content

## Summary

The email verification system is fully integrated and production-ready. It:

- ✅ Requires email verification on registration
- ✅ Prevents login for unverified emails
- ✅ Allows resending verification emails
- ✅ Automatically cleans up expired tokens
- ✅ Includes comprehensive logging
- ✅ Is fully tested (15+ test cases)
- ✅ Supports rate limiting
- ✅ Follows security best practices

Users now must verify their email address before booking tours, improving data quality and preventing spam registrations.
