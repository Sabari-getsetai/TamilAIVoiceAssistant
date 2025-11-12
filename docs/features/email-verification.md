# Email Verification System

## Overview

The Tamil AI Voice Assistant implements a robust email verification system using One-Time Passwords (OTP) for secure user authentication and organization creation. This system ensures that users have access to the email addresses they register with and provides an additional layer of security.

## Features

### 1. OTP-Based Verification
- **6-digit numeric codes** generated for each verification request
- **10-minute expiration** for security
- **Rate limiting** to prevent abuse (max 3 attempts per 10 minutes)
- **Single-use tokens** that are invalidated after successful verification

### 2. Use Cases

#### Organization Creation
- Users must verify their email before creating an organization
- Ensures organization creators have valid, accessible email addresses
- Prevents spam and fake organization creation

#### Email-Based Invitations
- Invitation links sent via email
- Unique tokens for each invitation
- 7-day expiration for invitation links

## Architecture

### Database Model

```python
class EmailVerification(Base):
    """Email verification OTP records"""
    __tablename__ = "email_verifications"
    
    id: str                          # UUID
    email: str                       # Email address to verify
    otp_code: str                    # 6-digit OTP (hashed)
    purpose: str                     # "organization_creation", "invitation"
    created_at: datetime             # When OTP was generated
    expires_at: datetime             # Expiration time (10 minutes)
    verified_at: Optional[datetime]  # When verified (null if not verified)
    attempts: int = 0                # Number of verification attempts
    ip_address: Optional[str]        # Request IP for security
```

### API Endpoints

#### Send OTP
```http
POST /api/auth/send-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "purpose": "organization_creation"
}

Response:
{
  "message": "OTP sent to email",
  "expires_in": 600,
  "can_resend_at": "2024-01-01T12:10:00Z"
}
```

#### Verify OTP
```http
POST /api/auth/verify-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "otp_code": "123456",
  "purpose": "organization_creation"
}

Response:
{
  "verified": true,
  "verification_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_in": 300
}
```

#### Resend OTP
```http
POST /api/auth/resend-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "purpose": "organization_creation"
}
```

## Email Service Integration

### SMTP Configuration

Required environment variables:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=noreply@tamilai.com
SMTP_FROM_NAME=Tamil AI Voice Assistant
```

### Email Templates

#### OTP Verification Email
```html
Subject: Your verification code for Tamil AI

Hello,

Your verification code is: 123456

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Tamil AI Voice Assistant Team
```

#### Organization Invitation Email
```html
Subject: You've been invited to join {organization_name}

Hello,

{inviter_name} has invited you to join {organization_name} on Tamil AI Voice Assistant.

Role: {role}

Click the link below to accept the invitation:
{invitation_link}

This invitation will expire in 7 days.

Best regards,
Tamil AI Voice Assistant Team
```

## Security Features

### 1. Rate Limiting
- **Per Email**: Maximum 3 OTP requests per 10 minutes
- **Per IP**: Maximum 10 OTP requests per hour
- **Cooldown Period**: 60 seconds between resend requests

### 2. OTP Security
- **Hashed Storage**: OTPs are hashed before storage (bcrypt)
- **Random Generation**: Cryptographically secure random number generation
- **Attempt Tracking**: Maximum 3 verification attempts per OTP
- **Auto-Expiration**: Expired OTPs are automatically invalidated

### 3. Token Security
- **JWT Tokens**: Verification tokens use JWT with short expiration
- **Single Use**: Verification tokens are invalidated after use
- **IP Binding**: Optional IP address validation

## User Flow

### Organization Creation Flow

```
1. User fills organization details
   ↓
2. System sends OTP to user's email
   ↓
3. User receives email with 6-digit code
   ↓
4. User enters OTP in verification modal
   ↓
5. System validates OTP
   ↓
6. If valid: Organization created, user becomes owner
   If invalid: Error message, retry allowed (max 3 attempts)
```

### Invitation Acceptance Flow

```
1. Org admin invites user via email
   ↓
2. System sends invitation email with unique link
   ↓
3. User clicks invitation link
   ↓
4. If not logged in: Redirect to login/register
   If logged in: Show invitation details
   ↓
5. User accepts invitation
   ↓
6. User added to organization with specified role
   ↓
7. If first organization: Set as active_organization_id
```

## Error Handling

### Common Errors

| Error Code | Description | User Action |
|------------|-------------|-------------|
| `OTP_EXPIRED` | OTP has expired (>10 minutes) | Request new OTP |
| `OTP_INVALID` | Incorrect OTP code | Retry (max 3 attempts) |
| `OTP_MAX_ATTEMPTS` | Too many failed attempts | Request new OTP |
| `RATE_LIMIT_EXCEEDED` | Too many OTP requests | Wait for cooldown period |
| `EMAIL_SEND_FAILED` | Failed to send email | Contact support |
| `INVITATION_EXPIRED` | Invitation link expired | Request new invitation |
| `INVITATION_INVALID` | Invalid invitation token | Contact inviter |

## Best Practices

### For Developers

1. **Always validate email format** before sending OTP
2. **Use environment-specific SMTP settings** (dev/staging/prod)
3. **Log OTP requests** for security auditing
4. **Monitor email delivery rates** and failures
5. **Implement proper error handling** for email service failures

### For Users

1. **Check spam folder** if OTP email not received
2. **Wait for cooldown** before requesting new OTP
3. **Use OTP within 10 minutes** of receipt
4. **Don't share OTP codes** with anyone
5. **Contact support** if persistent issues

## Testing

### Development Testing

```python
# Use test mode to bypass email sending
TESTING_MODE=true
TEST_OTP_CODE=123456  # Fixed OTP for testing

# All OTP requests will use TEST_OTP_CODE
# No actual emails will be sent
```

### Email Testing Tools

- **Mailtrap**: For development email testing
- **SendGrid**: For production email delivery
- **Mailgun**: Alternative production option

## Monitoring

### Metrics to Track

1. **OTP Success Rate**: Percentage of successful verifications
2. **Email Delivery Rate**: Percentage of emails successfully delivered
3. **Average Verification Time**: Time from OTP send to verification
4. **Failed Attempts**: Number of failed verification attempts
5. **Rate Limit Hits**: Frequency of rate limiting

### Alerts

- Email delivery failures > 5%
- OTP verification success rate < 90%
- Rate limit hits > 100/hour
- SMTP connection failures

## Future Enhancements

1. **SMS OTP**: Alternative to email OTP
2. **Authenticator Apps**: TOTP support (Google Authenticator, Authy)
3. **Backup Codes**: One-time backup codes for account recovery
4. **Email Templates**: Customizable HTML email templates
5. **Multi-language Support**: Localized email content
6. **Webhook Notifications**: Real-time verification status updates

## Related Documentation

- [Authentication](./authentication.md)
- [Organization Management](./organization-management.md)
- [Member Management](./member-management.md)
- [Email Configuration](../setup/email-configuration.md)
