# Email Notifications System

## Overview
Your Travel Worthy PH website now has comprehensive email notifications that automatically alert users and admins about important events.

## Features Added

### 1. **User Registration Welcome Email**
- **Trigger**: When a new user registers
- **Recipient**: New user
- **Content**: Welcome message with features overview
- **File**: `routes/auth.py` → `register()` function

### 2. **Booking Confirmation Email**
- **Trigger**: When a user creates a booking
- **Recipient**: Customer
- **Content**: Booking details, travel date, number of travelers, total price
- **Status**: Pending confirmation
- **File**: `routes/bookings.py` (already implemented)

### 3. **Admin New Booking Alert**
- **Trigger**: When a new booking is submitted
- **Recipient**: Admin
- **Content**: Complete booking details for review
- **File**: `routes/bookings.py` (already implemented)

### 4. **Booking Status Update Emails**
- **Trigger**: When admin updates booking status
- **Recipient**: Customer
- **Types**:
  - **Approved**: Booking accepted, travel confirmed
  - **Rejected**: Booking declined with optional reason
  - **Cancelled**: Booking cancelled
- **File**: `routes/admin.py` → `update_booking_status()` function

### 5. **Trip Inquiry Received Alert**
- **Trigger**: When customer submits a custom trip inquiry
- **Recipient**: Admin
- **Content**: Customer details, destination, dates, number of travelers
- **File**: `routes/bookings.py` (already implemented)

### 6. **Inquiry Response Email**
- **Trigger**: When admin replies to a customer inquiry
- **Recipient**: Customer
- **Content**: Admin's response to their trip inquiry
- **File**: `routes/admin.py` → `reply_to_inquiry()` function (NEW)

### 7. **Contact Form Auto-Reply**
- **Trigger**: When someone fills contact form
- **Recipient**: Contact form submitter
- **Content**: Acknowledgment that message was received
- **File**: `routes/main.py` (already implemented)

### 8. **Contact Form Admin Alert**
- **Trigger**: When someone submits contact form
- **Recipient**: Admin
- **Content**: Contact message details for follow-up
- **File**: `routes/main.py` (already implemented)

---

## Configuration Required

### Email Settings (in `.env` or config)
Make sure these environment variables are set:

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### For Gmail:
1. Enable "2-Factor Authentication"
2. Generate an "App Password" (16-character password)
3. Use that password in `MAIL_PASSWORD`

### For Other Providers:
- **SendGrid**: Use sendgrid SMTP settings
- **Mailgun**: Use mailgun SMTP settings
- **AWS SES**: Use SES SMTP credentials

---

## Database Migration

After these changes, run database migration to add new fields:

```bash
flask db migrate -m "Add inquiry response fields"
flask db upgrade
```

**New fields added to `Inquiry` model:**
- `admin_response` (Text) - Stores admin's response message
- `responded_at` (DateTime) - Timestamp of admin response

---

## How to Use in Admin Panel

### Replying to Inquiry
1. Go to Admin → Inquiries
2. Find the inquiry you want to respond to
3. Click "Reply" button
4. Type your response message
5. Submit
6. Email automatically sent to customer with your response

### Updating Booking Status
1. Go to Admin → Bookings
2. Select a booking
3. Change status to: CONFIRMED, REJECTED, or CANCELLED
4. Save
5. Email automatically sent to customer with status update

---

## Email Service Functions

All email functions are in `email_service.py`:

```python
# User Emails
send_user_registration_welcome(user)
send_booking_confirmation(user, booking, package)
send_booking_approved(user, booking, package)
send_booking_rejected(user, booking, package, reason="")
send_booking_cancellation(user, booking, package)
send_inquiry_reply(inquiry, admin_response)

# Admin Emails
send_admin_new_booking(admin_email, user, booking, package)
send_admin_new_inquiry(admin_email, inquiry)

# Contact Form
send_contact_autoreply(name, to_email, subject)
send_contact_admin_alert(admin_email, name, email, subject, message)
```

---

## Testing Email Delivery

### Quick Test:
```python
# In Flask shell
from email_service import send_user_registration_welcome
from models.user import User

user = User.query.first()
send_user_registration_welcome(user)
```

### Gmail Sandbox Testing:
1. Add test email addresses to your Gmail contacts
2. Send emails only to those addresses during testing
3. Check spam/promotions folder if email not received

---

## Troubleshooting

### "No module named email_service"
- Check `PYTHONPATH` includes project root
- Restart Flask development server

### "MAIL_USERNAME not configured"
- Emails silently fail if mail not configured
- Check `.env` file for proper MAIL_ variables
- Restart server after changing .env

### Gmail Authentication Failed
- Use 16-character "App Password", not regular password
- Check if "Less secure app access" needs enabling
- Verify MAIL_PORT is 587 for TLS

### Email Not Received
- Check spam/promotions folder
- Verify recipient email is correct
- Check server logs: `tail -f logs/*.log`
- Test with `send_test_email.py` script

---

## Enhancement Ideas

1. **HTML Email Templates** - Currently plain text, could add HTML formatting
2. **Email Scheduling** - Send booking reminders 7/3/1 days before travel
3. **Multi-language Emails** - Translate emails based on user language
4. **Email Unsubscribe** - Add unsubscribe links to newsletters
5. **SMS Notifications** - Add Twilio integration for SMS alerts
6. **Email Analytics** - Track open rates, click rates
7. **Bulk Email** - Newsletter/promo campaigns to customer list

---

## Files Modified

- ✅ `email_service.py` - Added new email functions
- ✅ `routes/auth.py` - Added welcome email to registration
- ✅ `routes/admin.py` - Added email to booking status updates & inquiry replies
- ✅ `models/inquiry.py` - Added response fields to Inquiry model

