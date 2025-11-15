"""
Audit Service for Enterprise Compliance

This service handles audit log creation, querying, and compliance operations
for GDPR, SOC2, and other regulatory requirements.
"""

import uuid
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from ipaddress import IPv4Address, IPv6Address

from backend.database.models import (
    AuditLog, ActionType, ResourceType, ComplianceTag,
    AuditRetentionPolicy, DEFAULT_RETENTION_POLICIES
)
from backend.database.models import User, Organization
from backend.database.connection import get_db
from backend.infrastructure.logging import get_logger

logger = get_logger(__name__)


class AuditService:
    """
    Service for managing audit logs and compliance operations.

    Provides comprehensive audit logging for all user actions,
    supporting enterprise compliance requirements.
    """

    def __init__(self):
        self.logger = logger

    async def log_action(
        self,
        action_type: Union[ActionType, str],
        user_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        resource_type: Optional[Union[ResourceType, str]] = None,
        resource_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        http_method: Optional[str] = None,
        request_metadata: Optional[Dict[str, Any]] = None,
        response_status: Optional[str] = None,
        description: Optional[str] = None,
        severity: str = "info",
        compliance_tags: Optional[List[str]] = None,
        before_data: Optional[Dict[str, Any]] = None,
        after_data: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log an audit event.

        Args:
            action_type: The type of action being audited
            user_id: ID of the user performing the action
            organization_id: ID of the organization context
            resource_type: Type of resource being acted upon
            resource_id: ID of the specific resource
            ip_address: IP address of the request
            user_agent: User agent string from the request
            session_id: Session identifier
            request_id: Request correlation ID
            endpoint: API endpoint called
            http_method: HTTP method (GET, POST, etc.)
            request_metadata: Additional context data
            response_status: HTTP response status code
            description: Human-readable description
            severity: Severity level (info, warning, critical)
            compliance_tags: Compliance frameworks this applies to
            before_data: State before change (for updates)
            after_data: State after change (for updates)

        Returns:
            The created AuditLog instance
        """
        try:
            # Convert enums to strings if needed
            if isinstance(action_type, ActionType):
                action_type = action_type.value
            if isinstance(resource_type, ResourceType):
                resource_type = resource_type.value

            # Auto-assign compliance tags based on action type
            if compliance_tags is None:
                compliance_tags = self._get_compliance_tags(action_type)

            # Create audit log entry
            audit_log = AuditLog(
                user_id=user_id,
                organization_id=organization_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                request_id=request_id,
                endpoint=endpoint,
                http_method=http_method,
                request_metadata=request_metadata or {},
                response_status=response_status,
                description=description,
                severity=severity,
                compliance_tags=compliance_tags,
                before_data=before_data,
                after_data=after_data
            )

            # Save to database
            async for db in get_db():
                db.add(audit_log)
                await db.commit()
                await db.refresh(audit_log)
                break

            # Log security events at higher level
            if audit_log.is_security_event:
                self.logger.warning(
                    f"Security event logged: {action_type} by user {user_id} "
                    f"from IP {ip_address}"
                )
            else:
                self.logger.info(
                    f"Audit event logged: {action_type} by user {user_id}"
                )

            return audit_log

        except Exception as e:
            self.logger.error(f"Failed to create audit log: {e}")
            raise

    async def log_from_request(
        self,
        request: Request,
        action_type: Union[ActionType, str],
        user_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        resource_type: Optional[Union[ResourceType, str]] = None,
        resource_id: Optional[uuid.UUID] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """
        Log an audit event from a FastAPI Request object.

        Automatically extracts IP address, user agent, endpoint, and method
        from the request object.
        """
        # Extract request information
        client_ip = None
        if request.client:
            client_ip = str(request.client.host)

        user_agent = request.headers.get("user-agent")
        endpoint = str(request.url.path)
        method = request.method
        request_id = request.headers.get("x-request-id")

        # Get additional metadata from headers
        request_metadata = {
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
            "path_params": dict(request.path_params)
        }

        return await self.log_action(
            action_type=action_type,
            user_id=user_id,
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=client_ip,
            user_agent=user_agent,
            endpoint=endpoint,
            http_method=method,
            request_id=request_id,
            request_metadata=request_metadata,
            description=description,
            **kwargs
        )

    async def get_audit_logs(
        self,
        user_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        action_types: Optional[List[str]] = None,
        resource_types: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        severity: Optional[str] = None,
        compliance_tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Query audit logs with filtering options.
        """
        try:
            async for db in get_db():
                query = select(AuditLog).options(
                    selectinload(AuditLog.user),
                    selectinload(AuditLog.organization)
                )

                # Apply filters
                conditions = []

                if user_id:
                    conditions.append(AuditLog.user_id == user_id)

                if organization_id:
                    conditions.append(AuditLog.organization_id == organization_id)

                if action_types:
                    conditions.append(AuditLog.action_type.in_(action_types))

                if resource_types:
                    conditions.append(AuditLog.resource_type.in_(resource_types))

                if start_date:
                    conditions.append(AuditLog.timestamp >= start_date)

                if end_date:
                    conditions.append(AuditLog.timestamp <= end_date)

                if ip_address:
                    conditions.append(AuditLog.ip_address == ip_address)

                if severity:
                    conditions.append(AuditLog.severity == severity)

                if compliance_tags:
                    # Check if any of the specified tags overlap with the log's tags
                    conditions.append(AuditLog.compliance_tags.overlap(compliance_tags))

                if conditions:
                    query = query.where(and_(*conditions))

                # Order by timestamp descending (most recent first)
                query = query.order_by(desc(AuditLog.timestamp))

                # Apply pagination
                query = query.offset(offset).limit(limit)

                result = await db.execute(query)
                return result.scalars().all()

        except Exception as e:
            self.logger.error(f"Failed to query audit logs: {e}")
            raise

    async def get_user_audit_trail(
        self,
        user_id: uuid.UUID,
        days: int = 30
    ) -> List[AuditLog]:
        """
        Get complete audit trail for a specific user.
        Useful for GDPR data subject access requests.
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        return await self.get_audit_logs(
            user_id=user_id,
            start_date=start_date,
            limit=1000  # Higher limit for user trails
        )

    async def get_security_events(
        self,
        organization_id: Optional[uuid.UUID] = None,
        days: int = 7
    ) -> List[AuditLog]:
        """
        Get security-related audit events for monitoring.
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        security_actions = [
            ActionType.LOGIN_FAILED.value,
            ActionType.SUSPICIOUS_LOGIN.value,
            ActionType.RATE_LIMIT_EXCEEDED.value,
            ActionType.UNAUTHORIZED_ACCESS.value
        ]

        return await self.get_audit_logs(
            organization_id=organization_id,
            action_types=security_actions,
            start_date=start_date,
            limit=500
        )

    async def export_compliance_data(
        self,
        compliance_framework: str,
        organization_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Export audit data for compliance reporting.

        Args:
            compliance_framework: GDPR, SOC2, HIPAA, etc.
            organization_id: Limit to specific organization
            start_date: Start of reporting period
            end_date: End of reporting period

        Returns:
            List of audit log dictionaries formatted for compliance
        """
        logs = await self.get_audit_logs(
            organization_id=organization_id,
            compliance_tags=[compliance_framework],
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Large limit for compliance exports
        )

        return [log.to_dict() for log in logs]

    async def cleanup_expired_logs(self) -> int:
        """
        Clean up audit logs based on retention policies.

        Returns:
            Number of logs deleted
        """
        try:
            async for db in get_db():
                # Get all active retention policies
                policies_query = select(AuditRetentionPolicy).where(
                    AuditRetentionPolicy.is_active == "true"
                )
                result = await db.execute(policies_query)
                policies = result.scalars().all()

                if not policies:
                    self.logger.warning("No active retention policies found")
                    return 0

                total_deleted = 0

                for policy in policies:
                    try:
                        retention_days = int(policy.retention_days)
                        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

                        # Build deletion query
                        delete_conditions = [AuditLog.timestamp < cutoff_date]

                        if policy.action_types:
                            delete_conditions.append(
                                AuditLog.action_type.in_(policy.action_types)
                            )

                        if policy.compliance_frameworks:
                            delete_conditions.append(
                                AuditLog.compliance_tags.overlap(policy.compliance_frameworks)
                            )

                        # Count logs to be deleted
                        count_query = select(func.count(AuditLog.id)).where(
                            and_(*delete_conditions)
                        )
                        count_result = await db.execute(count_query)
                        count = count_result.scalar()

                        if count > 0:
                            # Delete expired logs
                            from sqlalchemy import delete
                            delete_query = delete(AuditLog).where(
                                and_(*delete_conditions)
                            )
                            await db.execute(delete_query)

                            total_deleted += count
                            self.logger.info(
                                f"Deleted {count} expired audit logs under policy {policy.name}"
                            )

                    except Exception as e:
                        self.logger.error(
                            f"Failed to cleanup logs for policy {policy.name}: {e}"
                        )
                        continue

                await db.commit()

                if total_deleted > 0:
                    self.logger.info(f"Audit log cleanup completed. Total deleted: {total_deleted}")

                return total_deleted

        except Exception as e:
            self.logger.error(f"Audit log cleanup failed: {e}")
            raise

    def _get_compliance_tags(self, action_type: str) -> List[str]:
        """
        Automatically assign compliance tags based on action type.
        """
        tags = []

        # GDPR applies to most user data operations
        gdpr_actions = {
            ActionType.USER_CREATED.value,
            ActionType.USER_UPDATED.value,
            ActionType.USER_DELETED.value,
            ActionType.DOCUMENT_UPLOADED.value,
            ActionType.DOCUMENT_VIEWED.value,
            ActionType.DOCUMENT_DOWNLOADED.value,
            ActionType.DATA_EXPORT_REQUESTED.value,
            ActionType.DATA_DELETION_REQUESTED.value,
            ActionType.SESSION_STARTED.value,
            ActionType.CONVERSATION_TURN.value
        }

        if action_type in gdpr_actions:
            tags.append(ComplianceTag.GDPR.value)

        # SOC2 applies to security and access control
        soc2_actions = {
            ActionType.LOGIN.value,
            ActionType.LOGOUT.value,
            ActionType.LOGIN_FAILED.value,
            ActionType.PASSWORD_RESET.value,
            ActionType.SUSPICIOUS_LOGIN.value,
            ActionType.RATE_LIMIT_EXCEEDED.value,
            ActionType.UNAUTHORIZED_ACCESS.value,
            ActionType.SYSTEM_CONFIG_CHANGED.value,
            ActionType.API_KEY_CREATED.value,
            ActionType.API_KEY_DELETED.value
        }

        if action_type in soc2_actions:
            tags.append(ComplianceTag.SOC2.value)

        # PCI_DSS applies to payment operations
        pci_actions = {
            ActionType.PAYMENT_PROCESSED.value,
            ActionType.PAYMENT_FAILED.value,
            ActionType.SUBSCRIPTION_CREATED.value,
            ActionType.SUBSCRIPTION_CHANGED.value
        }

        if action_type in pci_actions:
            tags.append(ComplianceTag.PCI_DSS.value)

        return tags


# Global audit service instance
audit_service = AuditService()


# Convenience functions for common audit operations
async def log_user_action(
    action_type: Union[ActionType, str],
    user_id: uuid.UUID,
    organization_id: Optional[uuid.UUID] = None,
    description: Optional[str] = None,
    **kwargs
) -> AuditLog:
    """Log a user action."""
    return await audit_service.log_action(
        action_type=action_type,
        user_id=user_id,
        organization_id=organization_id,
        description=description,
        **kwargs
    )


async def log_security_event(
    action_type: Union[ActionType, str],
    ip_address: str,
    user_id: Optional[uuid.UUID] = None,
    description: Optional[str] = None,
    severity: str = "warning",
    **kwargs
) -> AuditLog:
    """Log a security event."""
    return await audit_service.log_action(
        action_type=action_type,
        user_id=user_id,
        ip_address=ip_address,
        description=description,
        severity=severity,
        compliance_tags=[ComplianceTag.SOC2.value],
        **kwargs
    )


async def log_data_access(
    action_type: Union[ActionType, str],
    user_id: uuid.UUID,
    resource_type: Union[ResourceType, str],
    resource_id: uuid.UUID,
    organization_id: Optional[uuid.UUID] = None,
    description: Optional[str] = None,
    **kwargs
) -> AuditLog:
    """Log data access for GDPR compliance."""
    return await audit_service.log_action(
        action_type=action_type,
        user_id=user_id,
        organization_id=organization_id,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        compliance_tags=[ComplianceTag.GDPR.value],
        **kwargs
    )