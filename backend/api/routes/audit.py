"""
Audit API Routes for Enterprise Compliance

Provides REST API endpoints for audit log viewing, compliance reporting,
and data export functionality.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import csv
import io
import json

from backend.services.audit_service import audit_service
from backend.database.models import ActionType, ResourceType, ComplianceTag
from backend.services.auth import get_current_admin_user_dep as get_current_admin_user
from backend.database.models import User
from backend.infrastructure.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


# Pydantic models for API responses
class AuditLogResponse(BaseModel):
    """Response model for audit log entries."""
    id: str
    user_id: Optional[str]
    organization_id: Optional[str]
    action_type: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    endpoint: Optional[str]
    http_method: Optional[str]
    timestamp: datetime
    description: Optional[str]
    severity: str
    compliance_tags: List[str]
    request_metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class AuditQueryParams(BaseModel):
    """Query parameters for audit log filtering."""
    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    action_types: Optional[List[str]] = None
    resource_types: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    severity: Optional[str] = None
    compliance_tags: Optional[List[str]] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class ComplianceExportRequest(BaseModel):
    """Request model for compliance data export."""
    compliance_framework: str = Field(..., description="GDPR, SOC2, HIPAA, etc.")
    organization_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = Field(default="json", description="json, csv, or xlsx")
    include_sensitive_data: bool = Field(default=False, description="Include potentially sensitive fields")


class AuditStatsResponse(BaseModel):
    """Response model for audit statistics."""
    total_events: int
    events_by_action: Dict[str, int]
    events_by_severity: Dict[str, int]
    security_events_count: int
    top_users: List[Dict[str, Any]]
    top_ip_addresses: List[Dict[str, Any]]
    date_range: Dict[str, datetime]


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    action_types: Optional[str] = Query(None, description="Comma-separated action types"),
    resource_types: Optional[str] = Query(None, description="Comma-separated resource types"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    compliance_tags: Optional[str] = Query(None, description="Comma-separated compliance tags"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get audit logs with optional filtering.

    Requires admin role for access.
    """
    try:
        # Parse comma-separated values
        action_types_list = action_types.split(",") if action_types else None
        resource_types_list = resource_types.split(",") if resource_types else None
        compliance_tags_list = compliance_tags.split(",") if compliance_tags else None

        # Query audit logs
        logs = await audit_service.get_audit_logs(
            user_id=user_id,
            organization_id=organization_id,
            action_types=action_types_list,
            resource_types=resource_types_list,
            start_date=start_date,
            end_date=end_date,
            ip_address=ip_address,
            severity=severity,
            compliance_tags=compliance_tags_list,
            limit=limit,
            offset=offset
        )

        # Convert to response format
        return [
            AuditLogResponse(
                id=str(log.id),
                user_id=str(log.user_id) if log.user_id else None,
                organization_id=str(log.organization_id) if log.organization_id else None,
                action_type=log.action_type,
                resource_type=log.resource_type,
                resource_id=str(log.resource_id) if log.resource_id else None,
                ip_address=str(log.ip_address) if log.ip_address else None,
                user_agent=log.user_agent,
                endpoint=log.endpoint,
                http_method=log.http_method,
                timestamp=log.timestamp,
                description=log.description,
                severity=log.severity,
                compliance_tags=log.compliance_tags or [],
                request_metadata=log.request_metadata or {}
            )
            for log in logs
        ]

    except Exception as e:
        logger.error(f"Failed to retrieve audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: UUID,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get a specific audit log entry by ID.

    Requires admin role for access.
    """
    try:
        logs = await audit_service.get_audit_logs(limit=1)

        # Find the specific log (this is a simplified implementation)
        # In production, you'd want a more efficient get_by_id method
        for log in logs:
            if log.id == log_id:
                return AuditLogResponse(
                    id=str(log.id),
                    user_id=str(log.user_id) if log.user_id else None,
                    organization_id=str(log.organization_id) if log.organization_id else None,
                    action_type=log.action_type,
                    resource_type=log.resource_type,
                    resource_id=str(log.resource_id) if log.resource_id else None,
                    ip_address=str(log.ip_address) if log.ip_address else None,
                    user_agent=log.user_agent,
                    endpoint=log.endpoint,
                    http_method=log.http_method,
                    timestamp=log.timestamp,
                    description=log.description,
                    severity=log.severity,
                    compliance_tags=log.compliance_tags or [],
                    request_metadata=log.request_metadata or {}
                )

        raise HTTPException(status_code=404, detail="Audit log not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve audit log {log_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get audit statistics and analytics.

    Provides insights into system usage, security events, and compliance metrics.
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get all logs for the period
        logs = await audit_service.get_audit_logs(
            organization_id=organization_id,
            start_date=start_date,
            limit=10000  # Large limit for stats
        )

        # Calculate statistics
        total_events = len(logs)

        # Events by action type
        events_by_action = {}
        for log in logs:
            action = log.action_type
            events_by_action[action] = events_by_action.get(action, 0) + 1

        # Events by severity
        events_by_severity = {}
        for log in logs:
            severity = log.severity
            events_by_severity[severity] = events_by_severity.get(severity, 0) + 1

        # Security events count
        security_events_count = sum(1 for log in logs if log.is_security_event)

        # Top users (by event count)
        user_counts = {}
        for log in logs:
            if log.user_id:
                user_id = str(log.user_id)
                user_counts[user_id] = user_counts.get(user_id, 0) + 1

        top_users = [
            {"user_id": user_id, "event_count": count}
            for user_id, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        # Top IP addresses
        ip_counts = {}
        for log in logs:
            if log.ip_address:
                ip = str(log.ip_address)
                ip_counts[ip] = ip_counts.get(ip, 0) + 1

        top_ip_addresses = [
            {"ip_address": ip, "event_count": count}
            for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        # Date range
        date_range = {
            "start_date": start_date,
            "end_date": datetime.utcnow()
        }

        return AuditStatsResponse(
            total_events=total_events,
            events_by_action=events_by_action,
            events_by_severity=events_by_severity,
            security_events_count=security_events_count,
            top_users=top_users,
            top_ip_addresses=top_ip_addresses,
            date_range=date_range
        )

    except Exception as e:
        logger.error(f"Failed to calculate audit stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security-events")
async def get_security_events(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    days: int = Query(7, ge=1, le=90, description="Number of days to retrieve"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get recent security-related audit events.

    Useful for security monitoring and incident response.
    """
    try:
        security_events = await audit_service.get_security_events(
            organization_id=organization_id,
            days=days
        )

        return [
            {
                "id": str(event.id),
                "action_type": event.action_type,
                "user_id": str(event.user_id) if event.user_id else None,
                "ip_address": str(event.ip_address) if event.ip_address else None,
                "user_agent": event.user_agent,
                "timestamp": event.timestamp,
                "description": event.description,
                "severity": event.severity,
                "request_metadata": event.request_metadata or {}
            }
            for event in security_events
        ]

    except Exception as e:
        logger.error(f"Failed to retrieve security events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/trail")
async def get_user_audit_trail(
    user_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get complete audit trail for a specific user.

    Useful for GDPR data subject access requests and user activity analysis.
    """
    try:
        audit_trail = await audit_service.get_user_audit_trail(
            user_id=user_id,
            days=days
        )

        return [
            {
                "id": str(log.id),
                "action_type": log.action_type,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "ip_address": str(log.ip_address) if log.ip_address else None,
                "timestamp": log.timestamp,
                "description": log.description,
                "endpoint": log.endpoint,
                "http_method": log.http_method
            }
            for log in audit_trail
        ]

    except Exception as e:
        logger.error(f"Failed to retrieve user audit trail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/compliance")
async def export_compliance_data(
    export_request: ComplianceExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Export audit data for compliance reporting.

    Supports GDPR, SOC2, HIPAA, and other compliance frameworks.
    """
    try:
        # Validate compliance framework
        valid_frameworks = [tag.value for tag in ComplianceTag]
        if export_request.compliance_framework not in valid_frameworks:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid compliance framework. Valid options: {', '.join(valid_frameworks)}"
            )

        # Export compliance data
        compliance_data = await audit_service.export_compliance_data(
            compliance_framework=export_request.compliance_framework,
            organization_id=export_request.organization_id,
            start_date=export_request.start_date,
            end_date=export_request.end_date
        )

        # Handle different export formats
        if export_request.format == "csv":
            return _export_as_csv(compliance_data, export_request.compliance_framework)
        elif export_request.format == "xlsx":
            # For Excel export, you'd need to install openpyxl and implement this
            raise HTTPException(status_code=501, detail="Excel export not yet implemented")
        else:
            # Default JSON export
            return JSONResponse(
                content={
                    "compliance_framework": export_request.compliance_framework,
                    "export_date": datetime.utcnow().isoformat(),
                    "record_count": len(compliance_data),
                    "data": compliance_data
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export compliance data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_expired_logs(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Clean up expired audit logs based on retention policies.

    This operation runs in the background to avoid blocking the request.
    """
    try:
        # Run cleanup in background
        background_tasks.add_task(_run_audit_cleanup)

        return {
            "message": "Audit log cleanup started in background",
            "status": "accepted"
        }

    except Exception as e:
        logger.error(f"Failed to start audit cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/action-types")
async def get_action_types():
    """
    Get list of all available action types for filtering.
    """
    return [{"value": action.value, "name": action.name} for action in ActionType]


@router.get("/resource-types")
async def get_resource_types():
    """
    Get list of all available resource types for filtering.
    """
    return [{"value": resource.value, "name": resource.name} for resource in ResourceType]


@router.get("/compliance-tags")
async def get_compliance_tags():
    """
    Get list of all available compliance tags for filtering.
    """
    return [{"value": tag.value, "name": tag.name} for tag in ComplianceTag]


# Helper functions
def _export_as_csv(data: List[Dict[str, Any]], compliance_framework: str) -> StreamingResponse:
    """
    Export audit data as CSV format.
    """
    output = io.StringIO()

    if not data:
        # Empty CSV with headers
        writer = csv.writer(output)
        writer.writerow(["No data available for the specified criteria"])
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_export_{compliance_framework}.csv"}
        )

    # Write CSV with all fields from first record as headers
    fieldnames = list(data[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in data:
        # Convert complex fields to JSON strings
        csv_row = {}
        for key, value in row.items():
            if isinstance(value, (dict, list)):
                csv_row[key] = json.dumps(value)
            elif value is None:
                csv_row[key] = ""
            else:
                csv_row[key] = str(value)
        writer.writerow(csv_row)

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_export_{compliance_framework}.csv"}
    )


async def _run_audit_cleanup():
    """
    Background task to run audit log cleanup.
    """
    try:
        deleted_count = await audit_service.cleanup_expired_logs()
        logger.info(f"Audit cleanup completed. Deleted {deleted_count} expired logs.")
    except Exception as e:
        logger.error(f"Audit cleanup failed: {e}")