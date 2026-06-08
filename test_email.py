#!/usr/bin/env python
"""Test email configuration and send test email"""

from flask import current_app
from app import create_app
from flask_mail import Message
from app import mail

app = create_app()

with app.app_context():
    # Check configuration
    server = current_app.config.get('MAIL_SERVER')
    username = current_app.config.get('MAIL_USERNAME')
    
    print("=" * 50)
    print("EMAIL CONFIGURATION TEST")
    print("=" * 50)
    
    if server and username:
        print("✅ Email Configuration Found:")
        print(f"   Server: {server}")
        print(f"   Username: {username}")
        print(f"   Port: {current_app.config.get('MAIL_PORT')}")
        print(f"   Use TLS: {current_app.config.get('MAIL_USE_TLS')}")
        
        # Try to send test email
        print("\n📧 Sending test email...")
        try:
            msg = Message(
                subject='Test Email from Travel Worthy PH',
                recipients=[username],
                body='''Hello!

This is a test email from your Travel Worthy PH website.

If you received this email, your email notifications system is working correctly! ✅

Best regards,
Travel Worthy PH Team'''
            )
            mail.send(msg)
            print(f"✅ Test email sent to {username}!")
            print("\n📬 Check your inbox (and spam folder) within 1 minute.")
        except Exception as e:
            print(f"❌ Error sending email: {e}")
    else:
        print("❌ Email not configured!")
        print("   Check your .env file for MAIL_SERVER and MAIL_USERNAME")

print("=" * 50)
