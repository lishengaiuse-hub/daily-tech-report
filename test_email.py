#!/usr/bin/env python3
"""
Simple Email Test Script - FIXED VERSION
"""

import os
import yagmail
import smtplib
import re

print("=" * 50)
print("EMAIL TEST SCRIPT - FIXED VERSION")
print("=" * 50)

# Get credentials from environment
sender = os.getenv("SENDER_EMAIL")
password = os.getenv("SENDER_PASSWORD")
recipients_raw = os.getenv("RECEIVER_EMAIL")

print(f"\n📧 Configuration:")
print(f"   Sender: {sender}")
print(f"   Password length: {len(password) if password else 0} characters")
print(f"   Recipients raw: '{recipients_raw}'")

if not sender or not password or not recipients_raw:
    print("\n❌ Missing required environment variables!")
    exit(1)

# FIXED: Clean up the recipients string
print("\n🔄 Cleaning recipients string...")
# Remove asterisks, replace line breaks with commas
clean_recipients = recipients_raw.replace('*', '').replace('\n', ',').replace('\r', ',').replace(';', ',')
print(f"   After cleaning: '{clean_recipients}'")

# Split by comma and clean each email
recipients = []
for email in clean_recipients.split(','):
    email = email.strip()
    if email and '@' in email:
        recipients.append(email)

print(f"   Parsed recipients: {recipients}")

if not recipients:
    print("\n❌ No valid email recipients found!")
    exit(1)

print("\n🔄 Testing SMTP connection...")

# Test 1: Basic SMTP connection
try:
    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
    server.starttls()
    server.ehlo()
    print("✅ Step 1: Basic SMTP connection successful")
    server.quit()
except Exception as e:
    print(f"❌ Step 1: SMTP connection failed: {e}")
    exit(1)

# Test 2: Login
try:
    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
    server.starttls()
    server.login(sender, password)
    print("✅ Step 2: Login successful")
    server.quit()
except Exception as e:
    print(f"❌ Step 2: Login failed: {e}")
    print("\n🔑 Common issues:")
    print("   - Password is NOT your Gmail password, it's an App Password")
    print("   - 2-Factor Authentication must be enabled")
    print("   - App Password must be 16 characters with spaces")
    exit(1)

# Test 3: Send test email
try:
    print("\n🔄 Sending test email...")
    yag = yagmail.SMTP(sender, password)
    
    for recipient in recipients:
        print(f"   → Sending to: {recipient}")
    
    yag.send(
        to=recipients,
        subject="✅ TEST EMAIL - GitHub Actions Working!",
        contents=f"""
        <h1>✅ Test Successful!</h1>
        <p>This is a test email from GitHub Actions.</p>
        <p><strong>Time:</strong> {__import__('datetime').datetime.now()}</p>
        <p><strong>Recipients:</strong> {', '.join(recipients)}</p>
        <p>If you receive this, email is working correctly!</p>
        """
    )
    print("✅ Step 3: Test email sent successfully!")
    
except Exception as e:
    print(f"❌ Step 3: Failed to send email: {e}")
    exit(1)

print("\n🎉 ALL TESTS PASSED! Check your inbox in a few minutes.")
