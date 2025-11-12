# Email Configuration Guide - Tamil AI Voice Assistant

## Overview

This guide provides comprehensive instructions for configuring email services in the Tamil AI Voice Assistant platform. Email functionality is essential for organization invitations, OTP verification, and system notifications.

## Email Service Requirements

### Supported Email Providers

1. **Gmail SMTP** (Development & Small Scale)
2. **SendGrid** (Recommended for Production)
3. **AWS SES** (Enterprise Scale)
4. **Mailgun** (Alternative Production Option)
5. **Custom SMTP Server** (Self-hosted)

### Email Features

- **Organization Invitations**: Email-based member invitations with secure links
- **OTP Verification**: 6-digit verification codes for organization creation
- **System Notifications**: Account activity and security alerts
- **Password Reset**: Secure password recovery emails
- **Welcome Emails**: Onboarding emails for new users and members

## Configuration Methods

### Method 1: Gmail SMTP (Development)

#### Prerequisites
- Gmail account
- App-specific password (2FA must be enabled)

#### Setup Steps

1. **Enable 2-Factor Authentication**
   - Go to Google Account settings
   - Security → 2-Step Verification
   - Enable 2FA

2. **Generate App Password**
   - Go to Security → App passwords
   - Select "Mail" and "Other (Custom name)"
   - Name it "Tamil AI Assistant"
   - Copy the 16-character password

3. **Configure Environment Variables**
```bash
# .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false

EMAIL_FROM_NAME=Tamil AI Voice Assistant
EMAIL_FROM_ADDRESS=your-email@gmail.com
```

#### Limitations
- **Daily Limit**: 500 emails per day
- **Rate Limiting**: 100 emails per hour
- **Not Recommended**: For production use

### Method 2: SendGrid (Production Recommended)

#### Prerequisites
- SendGrid account (free tier available)
- Verified sender identity

#### Setup Steps

1. **Create SendGrid Account**
   - Sign up at https://sendgrid.com
   - Verify your email address
   - Complete account setup

2. **Create API Key**
   - Go to Settings → API Keys
   - Click "Create API Key"
   - Name: "Tamil AI Assistant Production"
   - Permissions: "Full Access" or "Mail Send"
   - Copy the API key (shown only once)

3. **Verify Sender Identity**
   - Go to Settings → Sender Authentication
   - Choose "Single Sender Verification" or "Domain Authentication"
   - For single sender: Verify your email
   - For domain: Add DNS records to your domain

4. **Configure Environment Variables**
```bash
# .env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=true
SMTP_USE_SSL=false

EMAIL_FROM_NAME=Tamil AI Voice Assistant
EMAIL_FROM_ADDRESS=noreply@yourdomain.com
```

#### Advantages
- **Free Tier**: 100 emails/day forever
- **Scalable**: Up to 100k emails/month on paid plans
- **Reliable**: 99.9% uptime SLA
- **Analytics**: Email tracking and analytics
- **Templates**: Email template management

### Method 3: AWS SES (Enterprise Scale)

#### Prerequisites
- AWS account
- Verified email or domain
- IAM credentials with SES permissions

#### Setup Steps

1. **Verify Email/Domain in SES**
   - Go to AWS SES Console
   - Verify email addresses or domain
   - Complete verification process

2. **Create SMTP Credentials**
   - Go to SMTP Settings in SES
   - Click "Create My SMTP Credentials"
   - Download credentials

3. **Request Production Access**
   - By default, SES is in sandbox mode
   - Request production access to send to any email
   - Provide use case details

4. **Configure Environment Variables**
```bash
# .env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false

EMAIL_FROM_NAME=Tamil AI Voice Assistant
EMAIL_FROM_ADDRESS=noreply@yourdomain.com
```

#### Advantages
- **Cost-Effective**: $0.10 per 1,000 emails
- **High Volume**: Unlimited sending capacity
- **Reliability**: AWS infrastructure
- **Integration**: Works with other AWS services

### Method 4: Mailgun (Alternative)

#### Setup Steps

1. **Create Mailgun Account**
   - Sign up at https://www.mailgun.com
   - Verify your account

2. **Add and Verify Domain**
   - Add your domain
   - Configure DNS records
   - Wait for verification

3. **Get SMTP Credentials**
   - Go to Sending → Domain Settings
   - Find SMTP credentials section
   - Copy credentials

4. **Configure Environment Variables**
```bash
# .env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=postmaster@yourdomain.com
SMTP_PASSWORD=your-mailgun-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false

EMAIL_FROM_NAME=Tamil AI Voice Assistant
EMAIL_FROM_ADDRESS=noreply@yourdomain.com
```

## Email Templates

### Template Structure

Email templates are stored in `backend/templates/email/` directory:

```
backend/templates/email/
├── base.html                    # Base template
├── organization_invitation.html # Member invitation
├── otp_verification.html        # OTP verification
├── email_verification.html      # Email verification
├── password_reset.html          # Password reset
├── welcome.html                 # Welcome email
└── notification.html            # General notifications
```

### Base Template

```html
<!-- backend/templates/email/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #FF9933 0%, #E6851A 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }
        .content {
            background: #ffffff;
            padding: 30px;
            border: 1px solid #e0e0e0;
        }
        .button {
            display: inline-block;
            padding: 12px 24px;
            background: #FF9933;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }
        .footer {
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #757575;
            border-radius: 0 0 10px 10px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Tamil AI Voice Assistant</h1>
    </div>
    <div class="content">
        {% block content %}{% endblock %}
    </div>
    <div class="footer">
        <p>&copy; 2024 Tamil AI Voice Assistant. All rights reserved.</p>
        <p>This email was sent to {{ recipient_email }}</p>
    </div>
</body>
</html>
```

### OTP Verification Template

```html
<!-- backend/templates/email/otp_verification.html -->
{% extends "base.html" %}

{% block content %}
<h2>Verify Your Email Address</h2>

<p>Hello,</p>

<p>You're creating a new organization on Tamil AI Voice Assistant. To verify your email address, please use the following verification code:</p>

<div style="background: #f5f5f5; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px;">
    <h1 style="font-size: 36px; letter-spacing: 8px; margin: 0; color: #FF9933;">
        {{ otp_code }}
    </h1>
</div>

<p><strong>This code will expire in {{ expiration_minutes }} minutes.</strong></p>

<p>If you didn't request this code, please ignore this email.</p>

<p>Best regards,<br>
Tamil AI Voice Assistant Team</p>
{% endblock %}
```

### Organization Invitation Template

```html
<!-- backend/templates/email/organization_invitation.html -->
{% extends "base.html" %}

{% block content %}
<h2>You're Invited to Join {{ organization_name }}</h2>

<p>Hello,</p>

<p>{{ invited_by_name }} has invited you to join <strong>{{ organization_name }}</strong> as a {{ role }} on the Tamil AI Voice Assistant platform.</p>

{% if custom_message %}
<div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #FF9933; margin: 20px 0;">
    <p><strong>Personal message from {{ invited_by_name }}:</strong></p>
    <p>{{ custom_message }}</p>
</div>
{% endif %}

<div style="text-align: center; margin: 30px 0;">
    <a href="{{ invitation_url }}" class="button">
        Accept Invitation
    </a>
</div>

<p><strong>What you'll get access to:</strong></p>
<ul>
    <li>AI-powered chat and voice assistant in Tamil</li>
    <li>Document upload and knowledge base features</li>
    <li>Collaborative workspace with your team</li>
    <li>Analytics and usage insights</li>
</ul>

<p><small>This invitation will expire in {{ expiration_days }} days. If you don't have an account yet, you can create one when accepting the invitation.</small></p>

<hr style="margin: 30px 0; border: none; border-top: 1px solid #e0e0e0;">

<p><small>If you're having trouble with the button above, copy and paste this link into your browser:</small></p>
<p><small>{{ invitation_url }}</small></p>
{% endblock %}
```

## Email Service Implementation

### Python Email Service

```python
# backend/services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from backend.settings import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.from_name = settings.EMAIL_FROM_NAME
        self.from_address = settings.EMAIL_FROM_ADDRESS
        
        # Setup Jinja2 template environment
        self.template_env = Environment(
            loader=FileSystemLoader(settings.EMAIL_TEMPLATE_DIR)
        )
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict
    ) -> bool:
        """Send an email using the specified template"""
        try:
            # Render template
            template = self.template_env.get_template(template_name)
            html_content = template.render(
                recipient_email=to_email,
                subject=subject,
                **context
            )
            
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_address}>"
            message['To'] = to_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_otp_email(self, to_email: str, otp_code: str, expiration_minutes: int = 10):
        """Send OTP verification email"""
        return self.send_email(
            to_email=to_email,
            subject="Verify Your Email - Tamil AI Voice Assistant",
            template_name="otp_verification.html",
            context={
                "otp_code": otp_code,
                "expiration_minutes": expiration_minutes
            }
        )
    
    def send_invitation_email(
        self,
        to_email: str,
        organization_name: str,
        invited_by_name: str,
        role: str,
        invitation_url: str,
        custom_message: str = None,
        expiration_days: int = 7
    ):
        """Send organization invitation email"""
        return self.send_email(
            to_email=to_email,
            subject=f"Invitation to join {organization_name}",
            template_name="organization_invitation.html",
            context={
                "organization_name": organization_name,
                "invited_by_name": invited_by_name,
                "role": role,
                "invitation_url": invitation_url,
                "custom_message": custom_message,
                "expiration_days": expiration_days
            }
        )

# Create singleton instance
email_service = EmailService()
```

## Testing Email Configuration

### Test Script

```python
# scripts/test_email.py
import asyncio
from backend.services.email_service import email_service

async def test_email_configuration():
    """Test email configuration"""
    print("Testing email configuration...")
    
    # Test OTP email
    print("\n1. Testing OTP email...")
    success = email_service.send_otp_email(
        to_email="test@example.com",
        otp_code="123456",
        expiration_minutes=10
    )
    print(f"OTP email: {'✓ Success' if success else '✗ Failed'}")
    
    # Test invitation email
    print("\n2. Testing invitation email...")
    success = email_service.send_invitation_email(
        to_email="test@example.com",
        organization_name="Test Organization",
        invited_by_name="John Doe",
        role="member",
        invitation_url="https://app.tamilai.com/invite/abc123",
        custom_message="Welcome to our team!",
        expiration_days=7
    )
    print(f"Invitation email: {'✓ Success' if success else '✗ Failed'}")

if __name__ == "__main__":
    asyncio.run(test_email_configuration())
```

### Run Test

```bash
# Test email configuration
python scripts/test_email.py

# Or run with specific email
python scripts/test_email.py --email your-email@example.com
```

### Development Email Testing

For development, you can use **MailHog** to capture emails locally:

```bash
# Install and run MailHog
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Configure environment for MailHog
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USERNAME=""
SMTP_PASSWORD=""
SMTP_USE_TLS=false
EMAIL_BACKEND=smtp

# View emails at http://localhost:8025
```

## Environment Configuration

### Complete Email Environment Variables

```bash
# Email Service Configuration
ENABLE_EMAIL_VERIFICATION=true
EMAIL_BACKEND=smtp  # smtp, console, or file

# SMTP Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_TIMEOUT=30

# Email Content Settings
EMAIL_FROM_NAME=Tamil AI Voice Assistant
EMAIL_FROM_ADDRESS=noreply@yourdomain.com
EMAIL_TEMPLATE_DIR=backend/templates/email

# OTP Settings
OTP_EXPIRATION_MINUTES=10
OTP_LENGTH=6
OTP_MAX_ATTEMPTS=3
OTP_RESEND_COOLDOWN_MINUTES=2

# Email Rate Limiting
EMAIL_RATE_LIMIT_PER_HOUR=100
EMAIL_RATE_LIMIT_PER_DAY=1000

# Email Queue Settings (for high volume)
EMAIL_QUEUE_ENABLED=false
EMAIL_QUEUE_BACKEND=redis
EMAIL_QUEUE_MAX_RETRIES=3
```

## Security Considerations

### Email Security Best Practices

1. **Use App Passwords**: Never use your main account password
2. **Enable TLS**: Always use encrypted connections
3. **Validate Recipients**: Verify email addresses before sending
4. **Rate Limiting**: Implement sending limits to prevent abuse
5. **Template Validation**: Sanitize template variables
6. **Logging**: Log email activities for monitoring

### Email Content Security

```python
# backend/services/email_service.py (security additions)
import html
import re
from urllib.parse import quote

class EmailService:
    def _sanitize_content(self, content: str) -> str:
        """Sanitize email content to prevent injection"""
        # HTML escape
        content = html.escape(content)
        
        # Remove potentially dangerous patterns
        dangerous_patterns = [
            r'<script.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror='
        ]
        
        for pattern in dangerous_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        return content
    
    def _validate_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
```

## Monitoring and Analytics

### Email Delivery Monitoring

```python
# backend/services/email_monitoring.py
from datetime import datetime, timedelta
from backend.database.models import EmailLog
from backend.database.connection import get_db

class EmailMonitoring:
    @staticmethod
    def log_email_sent(
        to_email: str,
        subject: str,
        template_name: str,
        success: bool,
        error_message: str = None
    ):
        """Log email sending attempt"""
        db = next(get_db())
        
        email_log = EmailLog(
            to_email=to_email,
            subject=subject,
            template_name=template_name,
            success=success,
            error_message=error_message,
            sent_at=datetime.utcnow()
        )
        
        db.add(email_log)
        db.commit()
    
    @staticmethod
    def get_email_stats(days: int = 7):
        """Get email statistics for the last N days"""
        db = next(get_db())
        
        since = datetime.utcnow() - timedelta(days=days)
        
        stats = db.query(EmailLog).filter(
            EmailLog.sent_at >= since
        ).all()
        
        total_sent = len(stats)
        successful = len([s for s in stats if s.success])
        failed = total_sent - successful
        
        return {
            "total_sent": total_sent,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_sent * 100) if total_sent > 0 else 0
        }
```

### Email Database Model

```python
# backend/database/models.py (addition)
from sqlalchemy import Column, String, Boolean, DateTime, Text

class EmailLog(Base):
    __tablename__ = "email_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    to_email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    template_name = Column(String, nullable=False)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<EmailLog(to={self.to_email}, success={self.success})>"
```

## Troubleshooting

### Common Issues

#### 1. Authentication Failed
```
smtplib.SMTPAuthenticationError: (535, '5.7.8 Username and Password not accepted')
```

**Solutions:**
- Verify SMTP credentials
- Enable "Less secure app access" (Gmail)
- Use app-specific password (Gmail with 2FA)
- Check if account is locked

#### 2. Connection Timeout
```
socket.timeout: timed out
```

**Solutions:**
- Check SMTP host and port
- Verify firewall settings
- Try different ports (587, 465, 25)
- Check network connectivity

#### 3. TLS/SSL Errors
```
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Solutions:**
- Verify TLS/SSL settings
- Update certificates
- Try different encryption methods
- Check server requirements

#### 4. Rate Limiting
```
smtplib.SMTPRecipientsRefused: {'email@example.com': (550, 'Rate limit exceeded')}
```

**Solutions:**
- Implement email queuing
- Add delays between sends
- Use different SMTP provider
- Upgrade service plan

### Debugging Email Issues

```python
# scripts/debug_email.py
import logging
from backend.services.email_service import email_service

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def debug_email_configuration():
    """Debug email configuration step by step"""
    
    print("=== Email Configuration Debug ===\n")
    
    # Check environment variables
    print("1. Environment Variables:")
    print(f"   SMTP_HOST: {email_service.smtp_host}")
    print(f"   SMTP_PORT: {email_service.smtp_port}")
    print(f"   SMTP_USERNAME: {email_service.smtp_username}")
    print(f"   SMTP_USE_TLS: {email_service.smtp_use_tls}")
    print(f"   FROM_ADDRESS: {email_service.from_address}")
    
    # Test SMTP connection
    print("\n2. Testing SMTP Connection:")
    try:
        import smtplib
        server = smtplib.SMTP(email_service.smtp_host, email_service.smtp_port)
        if email_service.smtp_use_tls:
            server.starttls()
        server.login(email_service.smtp_username, email_service.smtp_password)
        server.quit()
        print("   ✓ SMTP connection successful")
    except Exception as e:
        print(f"   ✗ SMTP connection failed: {e}")
    
    # Test template loading
    print("\n3. Testing Template Loading:")
    try:
        template = email_service.template_env.get_template("otp_verification.html")
        print("   ✓ Template loading successful")
    except Exception as e:
        print(f"   ✗ Template loading failed: {e}")
    
    # Test email sending
    print("\n4. Testing Email Sending:")
    try:
        success = email_service.send_otp_email(
            to_email="test@example.com",
            otp_code="123456"
        )
        print(f"   {'✓' if success else '✗'} Email sending {'successful' if success else 'failed'}")
    except Exception as e:
        print(f"   ✗ Email sending failed: {e}")

if __name__ == "__main__":
    debug_email_configuration()
```

## Production Deployment

### Email Service Scaling

For high-volume production deployments:

1. **Use Professional Email Service**
   - SendGrid, AWS SES, or Mailgun
   - Dedicated IP addresses
   - Domain authentication

2. **Implement Email Queuing**
   - Redis or RabbitMQ for queue management
   - Background workers for email processing
   - Retry mechanisms for failed sends

3. **Monitor Email Delivery**
   - Track delivery rates
   - Monitor bounce rates
   - Set up alerts for failures

4. **Implement Email Templates Management**
   - Version control for templates
   - A/B testing capabilities
   - Dynamic content personalization

### Email Queue Implementation

```python
# backend/services/email_queue.py
import redis
import json
from celery import Celery

# Setup Celery for email queue
celery_app = Celery('email_queue')
celery_app.config_from_object('backend.celery_config')

@celery_app.task(bind=True, max_retries=3)
def send_email_task(self, email_data):
    """Background task to send emails"""
    try:
        email_service.send_email(**email_data)
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

def queue_email(to_email: str, subject: str, template_name: str, context: dict):
    """Queue an email for background sending"""
    email_data = {
        'to_email': to_email,
        'subject': subject,
        'template_name': template_name,
        'context': context
    }
    
    send_email_task.delay(email_data)
```

## Related Documentation

- [Environment Configuration](environment-configuration.md)
- [Organization Management](../features/organization-management.md)
- [Email Verification](../features/email-verification.md)
- [Member Management](../features/member-management.md)
- [Security Best Practices](../security/email-security.md)

## Support

For email configuration issues:

1. Check the troubleshooting section above
2. Run the debug script to identify issues
3. Review email service provider documentation
4. Check firewall and network settings
5. Verify DNS configuration for custom domains

Remember to test email configuration in a development environment before deploying to production.
