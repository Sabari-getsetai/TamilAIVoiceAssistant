"""
Email service for sending member invitations and notifications.

This module provides email functionality for:
- Member invitation emails with token-based links
- Password reset emails
- Organization notifications
- Billing and subscription updates
"""

import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, List, Any
from jinja2 import Template, FileSystemLoader, Environment

from backend import settings
from backend.database.models import User, Organization, OrganizationMember


class EmailService:
    """Service for sending emails with template support and SMTP configuration."""

    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME

        # Initialize Jinja2 template environment
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'email')
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir) if os.path.exists(template_dir) else None
        )

    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and configure SMTP connection."""
        try:
            # Create SMTP connection
            if self.smtp_use_tls:
                smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)
                smtp.starttls()
            else:
                smtp = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)

            # Authenticate if credentials are provided
            if self.smtp_username and self.smtp_password:
                smtp.login(self.smtp_username, self.smtp_password)

            return smtp
        except Exception as e:
            raise Exception(f"Failed to connect to SMTP server: {str(e)}")

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> tuple[str, str]:
        """Render email template with given context."""
        try:
            if self.jinja_env:
                # Try to load template from file
                template = self.jinja_env.get_template(template_name)
                html_content = template.render(**context)

                # Generate plain text version (simple HTML stripping)
                text_content = self._html_to_text(html_content)
                return html_content, text_content
            else:
                # Fallback to built-in templates
                return self._get_built_in_template(template_name, context)
        except Exception as e:
            # Fallback to built-in template if file template fails
            return self._get_built_in_template(template_name, context)

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (simple implementation)."""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _get_built_in_template(self, template_name: str, context: Dict[str, Any]) -> tuple[str, str]:
        """Get built-in email templates as fallback."""
        if template_name == 'member_invitation.html':
            return self._get_invitation_template(context)
        elif template_name == 'password_reset.html':
            return self._get_password_reset_template(context)
        elif template_name == 'organization_notification.html':
            return self._get_organization_notification_template(context)
        else:
            # Default template
            html = f"""
            <html>
                <body>
                    <h2>{context.get('subject', 'Notification')}</h2>
                    <p>{context.get('message', 'You have received a notification from Tamil AI Voice Assistant.')}</p>
                    <p>Best regards,<br>Tamil AI Voice Assistant Team</p>
                </body>
            </html>
            """
            text = self._html_to_text(html)
            return html, text

    def _get_invitation_template(self, context: Dict[str, Any]) -> tuple[str, str]:
        """Get member invitation email template."""
        html = f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Organization Invitation</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .logo {{ background: #2563eb; color: white; width: 60px; height: 60px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; }}
                    .content {{ background: #f8fafc; padding: 30px; border-radius: 8px; margin: 20px 0; }}
                    .button {{ display: inline-block; background: #2563eb; color: white; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; margin: 20px 0; }}
                    .footer {{ text-align: center; font-size: 14px; color: #6b7280; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">TA</div>
                        <h1>Tamil AI Voice Assistant</h1>
                    </div>

                    <div class="content">
                        <h2>You're invited to join {context.get('organization_name', 'an organization')}</h2>

                        <p>Hello!</p>

                        <p><strong>{context.get('invited_by', 'Someone')}</strong> has invited you to join <strong>{context.get('organization_name', 'their organization')}</strong> on Tamil AI Voice Assistant.</p>

                        <p>You will be added with the role: <strong>{context.get('role', 'Member').title()}</strong></p>

                        <p>Click the button below to accept this invitation:</p>

                        <a href="{context.get('invitation_link', '#')}" class="button">Accept Invitation</a>

                        <p><small>This invitation will expire in 7 days.</small></p>

                        <p>If you're not familiar with Tamil AI Voice Assistant, it's an AI-powered voice assistant that enables natural conversations in Tamil with document intelligence capabilities.</p>
                    </div>

                    <div class="footer">
                        <p>If you didn't expect this invitation, you can safely ignore this email.</p>
                        <p>&copy; 2024 Tamil AI Voice Assistant</p>
                    </div>
                </div>
            </body>
        </html>
        """

        text = f"""
        Tamil AI Voice Assistant - Organization Invitation

        Hello!

        {context.get('invited_by', 'Someone')} has invited you to join {context.get('organization_name', 'their organization')} on Tamil AI Voice Assistant.

        You will be added with the role: {context.get('role', 'Member').title()}

        To accept this invitation, visit: {context.get('invitation_link', '#')}

        This invitation will expire in 7 days.

        If you didn't expect this invitation, you can safely ignore this email.

        Best regards,
        Tamil AI Voice Assistant Team
        """

        return html, text

    def _get_password_reset_template(self, context: Dict[str, Any]) -> tuple[str, str]:
        """Get password reset email template."""
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Password Reset Request</h2>

                    <p>Hello {context.get('user_name', 'there')},</p>

                    <p>We received a request to reset your password for Tamil AI Voice Assistant.</p>

                    <p>Click the link below to reset your password:</p>

                    <p><a href="{context.get('reset_link', '#')}" style="background: #2563eb; color: white; text-decoration: none; padding: 12px 24px; border-radius: 6px; display: inline-block;">Reset Password</a></p>

                    <p><small>This link will expire in 1 hour.</small></p>

                    <p>If you didn't request this password reset, please ignore this email.</p>

                    <p>Best regards,<br>Tamil AI Voice Assistant Team</p>
                </div>
            </body>
        </html>
        """

        text = f"""
        Password Reset Request

        Hello {context.get('user_name', 'there')},

        We received a request to reset your password for Tamil AI Voice Assistant.

        To reset your password, visit: {context.get('reset_link', '#')}

        This link will expire in 1 hour.

        If you didn't request this password reset, please ignore this email.

        Best regards,
        Tamil AI Voice Assistant Team
        """

        return html, text

    def _get_organization_notification_template(self, context: Dict[str, Any]) -> tuple[str, str]:
        """Get organization notification email template."""
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>{context.get('subject', 'Organization Update')}</h2>

                    <p>Hello {context.get('user_name', 'there')},</p>

                    <p>{context.get('message', 'You have received a notification from your organization.')}</p>

                    <p>Organization: <strong>{context.get('organization_name', 'N/A')}</strong></p>

                    <p>Best regards,<br>Tamil AI Voice Assistant Team</p>
                </div>
            </body>
        </html>
        """

        text = f"""
        {context.get('subject', 'Organization Update')}

        Hello {context.get('user_name', 'there')},

        {context.get('message', 'You have received a notification from your organization.')}

        Organization: {context.get('organization_name', 'N/A')}

        Best regards,
        Tamil AI Voice Assistant Team
        """

        return html, text

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """Send email with HTML and text content."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            if reply_to:
                msg['Reply-To'] = reply_to

            # Attach text and HTML parts
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')

            msg.attach(text_part)
            msg.attach(html_part)

            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase(attachment['type'], attachment['subtype'])
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)

            # Send email
            smtp = self._create_smtp_connection()
            smtp.send_message(msg)
            smtp.quit()

            return True

        except Exception as e:
            print(f"Error sending email to {to_email}: {str(e)}")
            return False

    def send_member_invitation(
        self,
        to_email: str,
        invited_by: str,
        organization_name: str,
        role: str,
        invitation_token: str
    ) -> bool:
        """Send member invitation email."""
        # Generate invitation link
        base_url = settings.FRONTEND_URL or "http://localhost:3000"
        invitation_link = f"{base_url}/auth/accept-invitation?token={invitation_token}"

        context = {
            'invited_by': invited_by,
            'organization_name': organization_name,
            'role': role,
            'invitation_link': invitation_link,
            'invitation_token': invitation_token
        }

        html_content, text_content = self._render_template('member_invitation.html', context)

        subject = f"Invitation to join {organization_name} - Tamil AI Voice Assistant"

        return self.send_email(to_email, subject, html_content, text_content)

    def send_password_reset(self, to_email: str, user_name: str, reset_token: str) -> bool:
        """Send password reset email."""
        base_url = settings.FRONTEND_URL or "http://localhost:3000"
        reset_link = f"{base_url}/auth/reset-password?token={reset_token}"

        context = {
            'user_name': user_name,
            'reset_link': reset_link,
            'reset_token': reset_token
        }

        html_content, text_content = self._render_template('password_reset.html', context)

        subject = "Password Reset - Tamil AI Voice Assistant"

        return self.send_email(to_email, subject, html_content, text_content)

    def send_organization_notification(
        self,
        to_email: str,
        user_name: str,
        organization_name: str,
        subject: str,
        message: str
    ) -> bool:
        """Send organization notification email."""
        context = {
            'user_name': user_name,
            'organization_name': organization_name,
            'subject': subject,
            'message': message
        }

        html_content, text_content = self._render_template('organization_notification.html', context)

        return self.send_email(to_email, subject, html_content, text_content)

    def generate_invitation_token(self, organization_id: str, invited_email: str, role: str) -> str:
        """Generate secure invitation token."""
        timestamp = datetime.utcnow().isoformat()
        data = f"{organization_id}:{invited_email}:{role}:{timestamp}:{secrets.token_hex(16)}"
        return secrets.token_urlsafe(64)

    def is_smtp_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return bool(
            self.smtp_host and
            self.smtp_port and
            self.from_email
        )

    def test_connection(self) -> Dict[str, Any]:
        """Test SMTP connection and return status."""
        if not self.is_smtp_configured():
            return {
                'success': False,
                'error': 'SMTP not configured. Check environment variables.',
                'configured': False
            }

        try:
            smtp = self._create_smtp_connection()
            smtp.quit()
            return {
                'success': True,
                'message': 'SMTP connection successful',
                'configured': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'configured': True
            }


# Global email service instance
email_service = EmailService()