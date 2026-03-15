def send_email_fast(subject, html_content):
    """Send email without PDF (faster) with better debugging"""
    print(f"\n📧 Preparing to send email...")
    print(f"   Subject: {subject}")
    print(f"   HTML content length: {len(html_content)} characters")
    
    try:
        # Check if all required configs are present
        if not EMAIL_CONFIG["sender_email"]:
            print("❌ SENDER_EMAIL is missing")
            return False
        if not EMAIL_CONFIG["sender_password"]:
            print("❌ SENDER_PASSWORD is missing")
            return False
        if not EMAIL_CONFIG["receiver_email"]:
            print("❌ RECEIVER_EMAIL is missing")
            return False
            
        print(f"   Sender: {EMAIL_CONFIG['sender_email']}")
        print(f"   SMTP Host: {EMAIL_CONFIG['smtp_host']}:{EMAIL_CONFIG['smtp_port']}")
        
        # Parse recipients
        recipients_str = EMAIL_CONFIG["receiver_email"]
        print(f"   Raw recipients: {recipients_str}")
        
        # Handle different delimiters
        for delimiter in [';', '\n', '|', ',']:
            recipients_str = recipients_str.replace(delimiter, ',')
        
        recipients = [e.strip() for e in recipients_str.split(',') if e.strip()]
        recipients = [e for e in recipients if '@' in e]  # Basic email validation
        
        if not recipients:
            print("❌ No valid recipients found")
            print(f"   Parsed recipients: {recipients}")
            return False
        
        print(f"   Valid recipients: {recipients}")
        
        # Initialize SMTP
        print(f"   Connecting to SMTP server...")
        yag = yagmail.SMTP(
            user=EMAIL_CONFIG["sender_email"],
            password=EMAIL_CONFIG["sender_password"],
            host=EMAIL_CONFIG["smtp_host"],
            port=EMAIL_CONFIG["smtp_port"],
            smtp_starttls=True,
            smtp_ssl=False
        )
        
        print(f"   Connected successfully")
        print(f"   Sending email...")
        
        # Send email
        yag.send(
            to=recipients,
            subject=subject,
            contents=html_content
        )
        
        print(f"✅ Email sent successfully to {len(recipients)} recipients")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        import traceback
        traceback.print_exc()
        return False
