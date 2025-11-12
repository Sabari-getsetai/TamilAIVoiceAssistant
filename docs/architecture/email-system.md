# Email System Architecture

This document describes the email system architecture for the Tamil AI Voice Assistant platform, including email verification, member invitations, and notification systems.

## Overview

The email system provides:
- **Email Verification**: OTP-based email verification for user registration
- **Member Invitations**: Email-based organization member invitations
- **Notifications**: System notifications and alerts
- **Templates**: Customizable email templates with i18n support
- **Delivery**: Reliable email delivery with multiple provider support

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Registration │  │ Invitations  │  │ Notifications│      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Email Service Layer                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                Email Manager                         │   │
│  │  - Template rendering                               │   │
│  │  - Provider selection                               │   │
│  │  - Queue management                                 │   │
│  │  - Retry logic                                      │   │
│  │  - Rate limiting                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Provider Abstraction                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Gmail     │  │   SendGrid   │  │   AWS SES    │      │
│  │   Provider   │  │   Provider   │  │   Provider   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Storage & Queue                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Redis     │  │   MinIO      │      │
│  │ (Metadata)   │  │  (Queue)     │  │(Attachments) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Email Models

```python
class EmailVerification(Base):
    __tablename__ = "email_verifications"
    
    id: UUID
    user_id: UUID
    email: str
    otp_code: str  # 6-digit code
    expires_at: datetime
    verified_at: Optional[datetime]
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime

class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"
    
    id: UUID
    organization_id: UUID
    email: str
    role: OrganizationRole
    invited_by: UUID
    invitation_token: str
    expires_at: datetime
    accepted_at: Optional[datetime]
    created_at: datetime

class EmailLog(Base):
    __tablename__ = "email_logs"
    
    id: UUID
    recipient: str
    subject: str
    template: str
    provider: str
    status: EmailStatus  # pending, sent, failed, bounced
    error_message: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime
```

### 2. Email Service Interface

```python
from abc import ABC, abstractmethod

class EmailProvider(ABC):
    @abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Attachment]] = None
    ) -> EmailResult:
        pass

class EmailResult:
    success: bool
    message_id: Optional[str]
    error: Optional[str]
    provider: str
```

### 3. Email Manager

```python
class EmailManager:
    def __init__(self):
        self.providers = {
            'gmail': GmailProvider(),
            'sendgrid': SendGridProvider(),
            'ses': SESProvider()
        }
        self.template_engine = TemplateEngine()
        self.queue = EmailQueue()
    
    async def send_verification_email(
        self, 
        user: User, 
        otp_code: str
    ) -> bool:
        template_data = {
            'user_name': user.full_name,
            'otp_code': otp_code,
            'expires_minutes': 10,
            'support_email': settings.SUPPORT_EMAIL
        }
        
        return await self._send_templated_email(
            to=user.email,
            template='email_verification',
            data=template_data,
            priority='high'
        )
    
    async def send_invitation_email(
        self,
        invitation: OrganizationInvitation,
        organization: Organization,
        inviter: User
    ) -> bool:
        template_data = {
            'organization_name': organization.name,
            'inviter_name': inviter.full_name,
            'role': invitation.role.value,
            'invitation_url': f"{settings.FRONTEND_URL}/invite/{invitation.invitation_token}",
            'expires_days': 7
        }
        
        return await self._send_templated_email(
            to=invitation.email,
            template='organization_invitation',
            data=template_data,
            priority='normal'
        )
```

## Email Verification System

### 1. OTP Generation & Storage

```python
class EmailVerificationService:
    async def initiate_verification(self, user: User) -> EmailVerification:
        # Generate 6-digit OTP
        otp_code = self._generate_otp()
        
        # Store in database
        verification = EmailVerification(
            user_id=user.id,
            email=user.email,
            otp_code=otp_code,
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        
        db.add(verification)
        await db.commit()
        
        # Send email
        await email_manager.send_verification_email(user, otp_code)
        
        return verification
    
    def _generate_otp(self) -> str:
        """Generate cryptographically secure 6-digit OTP"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    async def verify_otp(self, user_id: UUID, otp_code: str) -> bool:
        verification = await self._get_active_verification(user_id)
        
        if not verification:
            return False
        
        # Check attempts
        if verification.attempts >= verification.max_attempts:
            return False
        
        # Increment attempts
        verification.attempts += 1
        
        # Check OTP
        if verification.otp_code == otp_code:
            verification.verified_at = datetime.utcnow()
            user = await db.get(User, user_id)
            user.is_email_verified = True
            await db.commit()
            return True
        
        await db.commit()
        return False
```

### 2. Verification Flow

```
User Registration
    ↓
Generate OTP (6 digits)
    ↓
Store in database (10 min expiry)
    ↓
Send verification email
    ↓
User enters OTP
    ↓
Validate OTP (max 3 attempts)
    ↓
Mark email as verified
    ↓
Allow organization creation
```

## Member Invitation System

### 1. Invitation Generation

```python
class InvitationService:
    async def create_invitation(
        self,
        organization_id: UUID,
        email: str,
        role: OrganizationRole,
        invited_by: UUID
    ) -> OrganizationInvitation:
        # Check if user already exists
        existing_user = await self._get_user_by_email(email)
        
        # Generate secure token
        invitation_token = self._generate_invitation_token()
        
        # Create invitation
        invitation = OrganizationInvitation(
            organization_id=organization_id,
            email=email,
            role=role,
            invited_by=invited_by,
            invitation_token=invitation_token,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        db.add(invitation)
        await db.commit()
        
        # Send invitation email
        organization = await db.get(Organization, organization_id)
        inviter = await db.get(User, invited_by)
        
        await email_manager.send_invitation_email(
            invitation, organization, inviter
        )
        
        return invitation
    
    def _generate_invitation_token(self) -> str:
        """Generate secure invitation token"""
        return secrets.token_urlsafe(32)
```

### 2. Invitation Acceptance

```python
async def accept_invitation(
    self,
    invitation_token: str,
    user_id: Optional[UUID] = None
) -> OrganizationMember:
    invitation = await self._get_invitation_by_token(invitation_token)
    
    if not invitation or invitation.expires_at < datetime.utcnow():
        raise HTTPException(400, "Invalid or expired invitation")
    
    if invitation.accepted_at:
        raise HTTPException(400, "Invitation already accepted")
    
    # If user_id not provided, user needs to register first
    if not user_id:
        user = await self._get_user_by_email(invitation.email)
        if not user:
            # Redirect to registration with invitation token
            return {"redirect": f"/register?invitation={invitation_token}"}
        user_id = user.id
    
    # Add user to organization
    member = OrganizationMember(
        organization_id=invitation.organization_id,
        user_id=user_id,
        role=invitation.role,
        joined_at=datetime.utcnow()
    )
    
    # Mark invitation as accepted
    invitation.accepted_at = datetime.utcnow()
    
    db.add(member)
    await db.commit()
    
    # Send welcome email
    await self._send_welcome_email(member)
    
    return member
```

## Email Templates

### 1. Template Structure

```
templates/
├── email/
│   ├── base.html                 # Base template
│   ├── email_verification.html   # OTP verification
│   ├── organization_invitation.html  # Member invitation
│   ├── welcome.html              # Welcome message
│   ├── password_reset.html       # Password reset
│   └── notification.html         # General notifications
└── i18n/
    ├── en.json                   # English translations
    ├── ta.json                   # Tamil translations
    └── hi.json                   # Hindi translations
```

### 2. Template Engine

```python
class TemplateEngine:
    def __init__(self):
        self.jinja_env = Environment(
            loader=FileSystemLoader('templates/email'),
            autoescape=True
        )
    
    async def render_template(
        self,
        template_name: str,
        data: Dict[str, Any],
        language: str = 'en'
    ) -> Tuple[str, str]:
        # Load translations
        translations = await self._load_translations(language)
        
        # Merge data with translations
        template_data = {
            **data,
            'translations': translations,
            'language': language
        }
        
        # Render HTML template
        html_template = self.jinja_env.get_template(f'{template_name}.html')
        html_content = html_template.render(**template_data)
        
        # Generate text version
        text_content = self._html_to_text(html_content)
        
        return html_content, text_content
```

### 3. Email Verification Template

```html
<!-- templates/email/email_verification.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ translations.verify_email_title }}</title>
</head>
<body>
    <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
        <h1>{{ translations.verify_email_heading }}</h1>
        
        <p>{{ translations.hello }} {{ user_name }},</p>
        
        <p>{{ translations.verify_email_message }}</p>
        
        <div style="background: #f5f5f5; padding: 20px; text-align: center; margin: 20px 0;">
            <h2 style="font-size: 32px; letter-spacing: 5px; margin: 0;">
                {{ otp_code }}
            </h2>
        </div>
        
        <p>{{ translations.otp_expires_message.format(minutes=expires_minutes) }}</p>
        
        <p>{{ translations.no_action_needed }}</p>
        
        <hr>
        <p style="color: #666; font-size: 12px;">
            {{ translations.support_message }} 
            <a href="mailto:{{ support_email }}">{{ support_email }}</a>
        </p>
    </div>
</body>
</html>
```

## Email Providers

### 1. Gmail Provider

```python
class GmailProvider(EmailProvider):
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
    
    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Attachment]] = None
    ) -> EmailResult:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = to
            
            # Add text and HTML parts
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return EmailResult(
                success=True,
                message_id=msg['Message-ID'],
                provider='gmail'
            )
            
        except Exception as e:
            logger.error(f"Failed to send email via Gmail: {str(e)}")
            return EmailResult(
                success=False,
                error=str(e),
                provider='gmail'
            )
```

### 2. SendGrid Provider

```python
class SendGridProvider(EmailProvider):
    def __init__(self):
        self.api_key = settings.SENDGRID_API_KEY
        self.client = SendGridAPIClient(self.api_key)
    
    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Attachment]] = None
    ) -> EmailResult:
        try:
            message = Mail(
                from_email=settings.SMTP_FROM_EMAIL,
                to_emails=to,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    self._add_attachment(message, attachment)
            
            response = self.client.send(message)
            
            return EmailResult(
                success=True,
                message_id=response.headers.get('X-Message-Id'),
                provider='sendgrid'
            )
            
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {str(e)}")
            return EmailResult(
                success=False,
                error=str(e),
                provider='sendgrid'
            )
```

### 3. AWS SES Provider

```python
class SESProvider(EmailProvider):
    def __init__(self):
        self.client = boto3.client(
            'ses',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
    
    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Attachment]] = None
    ) -> EmailResult:
        try:
            response = self.client.send_email(
                Source=settings.SMTP_FROM_EMAIL,
                Destination={'ToAddresses': [to]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {
                        'Html': {'Data': html_content},
                        'Text': {'Data': text_content or ''}
                    }
                }
            )
            
            return EmailResult(
                success=True,
                message_id=response['MessageId'],
                provider='ses'
            )
            
        except Exception as e:
            logger.error(f"Failed to send email via SES: {str(e)}")
            return EmailResult(
                success=False,
                error=str(e),
                provider='ses'
            )
```

## Email Queue System

### 1. Queue Implementation

```python
class EmailQueue:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL)
        self.queue_name = 'email_queue'
    
    async def enqueue(
        self,
        email_data: Dict[str, Any],
        priority: str = 'normal'
    ) -> str:
        """Add email to queue with priority"""
        email_id = str(uuid4())
        
        queue_item = {
            'id': email_id,
            'data': email_data,
            'priority': priority,
            'attempts': 0,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Add to appropriate queue based on priority
        queue_key = f"{self.queue_name}:{priority}"
        await self.redis.lpush(queue_key, json.dumps(queue_item))
        
        return email_id
    
    async def dequeue(self, priority: str = 'normal') -> Optional[Dict]:
        """Get next email from queue"""
        queue_key = f"{self.queue_name}:{priority}"
        item = await self.redis.rpop(queue_key)
        
        if item:
            return json.loads(item)
        return None
    
    async def requeue(self, email_item: Dict, delay_seconds: int = 60):
        """Requeue failed email with delay"""
        email_item['attempts'] += 1
        email_item['retry_at'] = (
            datetime.utcnow() + timedelta(seconds=delay_seconds)
        ).isoformat()
        
        await self.redis.zadd(
            f"{self.queue_name}:retry",
            {json.dumps(email_item): time.time() + delay_seconds}
        )
```

### 2. Queue Worker

```python
class EmailWorker:
    def __init__(self):
        self.queue = EmailQueue()
        self.email_manager = EmailManager()
        self.max_attempts = 3
    
    async def process_queue(self):
        """Process emails from queue"""
        while True:
            try:
                # Process high priority first
                for priority in ['high', 'normal', 'low']:
                    email_item = await self.queue.dequeue(priority)
                    
                    if email_item:
                        await self._process_email(email_item)
                
                # Check retry queue
                await self._process_retries()
                
                # Sleep briefly
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Queue worker error: {str(e)}")
                await asyncio.sleep(5)
    
    async def _process_email(self, email_item: Dict):
        """Process single email"""
        try:
            result = await self.email_manager.send_email(**email_item['data'])
            
            if result.success:
                await self._log_success(email_item, result)
            else:
                await self._handle_failure(email_item, result)
                
        except Exception as e:
            logger.error(f"Failed to process email: {str(e)}")
            await self._handle_failure(email_item, str(e))
    
    async def _handle_failure(self, email_item: Dict, error: str):
        """Handle failed email"""
        if email_item['attempts'] < self.max_attempts:
            # Requeue with exponential backoff
            delay = 60 * (2 ** email_item['attempts'])
            await self.queue.requeue(email_item, delay)
        else:
            # Max attempts reached, log failure
            await self._log_failure(email_item, error)
```

## Rate Limiting

```python
class EmailRateLimiter:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL)
    
    async def check_rate_limit(
        self,
        email: str,
        limit_type: str = 'verification'
    ) -> bool:
        """Check if email can be sent based on rate limits"""
        key = f"email_rate:{limit_type}:{email}"
        
        # Get current count
        count = await self.redis.get(key)
        
        if count and int(count) >= self._get_limit(limit_type):
            return False
        
        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self._get_window(limit_type))
        await pipe.execute()
        
        return True
    
    def _get_limit(self, limit_type: str) -> int:
        limits = {
            'verification': 3,  # 3 per hour
            'invitation': 10,   # 10 per hour
            'notification': 50  # 50 per hour
        }
        return limits.get(limit_type, 10)
    
    def _get_window(self, limit_type: str) -> int:
        """Get time window in seconds"""
        return 3600  # 1 hour
```

## Security Considerations

### 1. Token Security

- **OTP Codes**: Cryptographically secure random generation
- **Invitation Tokens**: URL-safe tokens with sufficient entropy
- **Expiration**: All tokens have expiration times
- **One-time Use**: Tokens invalidated after use

### 2. Email Validation

```python
def validate_email(email: str) -> bool:
    """Validate email format and domain"""
    # Basic format validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False
    
    # Check disposable email domains
    domain = email.split('@')[1]
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return False
    
    return True
```

### 3. Content Security

- HTML sanitization to prevent XSS
- SPF/DKIM/DMARC configuration
- Unsubscribe links in all emails
- Bounce handling

## Monitoring & Analytics

### 1. Email Metrics

```python
class EmailMetrics:
    async def track_email_sent(
        self,
        template: str,
        provider: str,
        success: bool
    ):
        """Track email sending metrics"""
        await self.redis.hincrby(
            f"email_metrics:{date.today()}",
            f"{template}:{provider}:{'success' if success else 'failure'}",
            1
        )
    
    async def get_daily_stats(self, date: date) -> Dict:
        """Get email statistics for a date"""
        stats = await self.redis.hgetall(f"email_metrics:{date}")
        return self._parse_stats(stats)
```

### 2. Logging

```python
logger.info(
    "Email sent",
    extra={
        "recipient": email,
        "template": template_name,
        "provider": provider,
        "message_id": message_id,
        "duration_ms": duration
    }
)
```

## Testing

### 1. Email Testing in Development

```python
class MockEmailProvider(EmailProvider):
    """Mock provider for testing"""
    async def send_email(self, **kwargs) -> EmailResult:
        logger.info(f"Mock email sent to {kwargs['to']}")
        logger.info(f"Subject: {kwargs['subject']}")
        logger.info(f"Content: {kwargs['html_content'][:100]}...")
        
        return EmailResult(
            success=True,
            message_id=f"mock-{uuid4()}",
            provider='mock'
        )
```

### 2. Integration Tests

```python
async def test_email_verification_flow():
    # Create user
    user = await create_test_user()
    
    # Initiate verification
    verification = await email_service.initiate_verification(user)
    
    # Verify OTP
    assert await email_service.verify_otp(user.id, verification.otp_code)
    
    # Check user is verified
    user = await db.get(User, user.id)
    assert user.is_email_verified
```

## References

- [Email Verification Feature](../features/email-verification.md)
- [Email Configuration Guide](../setup/email-configuration.md)
- [Organization Management](../features/organization-management.md)
- [Member Management](../features/member-management.md)
