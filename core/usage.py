"""
Core usage tracking utilities and helpers.
Provides functions to start and finalize usage events with cost calculation.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.usage_event import UsageEvent
from core.database import SessionLocal


def get_usage_rate_cents() -> int:
    """Get the usage rate in cents from environment variables."""
    return int(os.getenv('USAGE_RATE_CENTS', '10'))  # Default 10 cents


def start_event(
    route: str,
    action: str,
    request_id: str,
    user_id: str,
    tenant_id: str,
    units: float = 1.0,
    metadata: Optional[str] = None,
    db: Optional[Session] = None
) -> Optional[UsageEvent]:
    """
    Start a usage event with idempotency via request_id.
    
    Args:
        route: API route/endpoint
        action: Action being performed
        request_id: Unique request identifier for idempotency
        user_id: User making the request
        tenant_id: Tenant/organization identifier
        units: Number of units consumed (default 1.0)
        metadata: Optional metadata as JSON string
        db: Database session (will create one if not provided)
    
    Returns:
        UsageEvent instance or None if already exists (idempotent)
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    
    try:
        # Check if event already exists (idempotency)
        existing_event = UsageEvent.get_by_request_id(db, request_id)
        if existing_event:
            return existing_event
        
        # Create new usage event
        usage_event = UsageEvent(
            request_id=request_id,
            tenant_id=tenant_id,
            user_id=user_id,
            route=route,
            action=action,
            units=units,
            ts=datetime.utcnow(),
            metadata=metadata
        )
        
        # Calculate initial cost
        rate_cents = get_usage_rate_cents()
        usage_event.cost_cents = usage_event.calculate_cost(rate_cents)
        
        db.add(usage_event)
        db.commit()
        db.refresh(usage_event)
        
        return usage_event
        
    except IntegrityError:
        # Handle race condition where another request created the same event
        db.rollback()
        existing_event = UsageEvent.get_by_request_id(db, request_id)
        return existing_event
        
    except Exception as e:
        db.rollback()
        # Log error but don't fail the main request
        print(f"Error creating usage event: {e}")
        return None
        
    finally:
        if close_db:
            db.close()


def finalize_event(
    event_id: UUID,
    units: Optional[float] = None,
    cost_cents: Optional[int] = None,
    metadata: Optional[str] = None,
    db: Optional[Session] = None
) -> Optional[UsageEvent]:
    """
    Finalize a usage event by updating units and cost.
    
    Args:
        event_id: Usage event ID to update
        units: Updated number of units consumed
        cost_cents: Explicit cost in cents (overrides calculated cost)
        metadata: Additional metadata to append
        db: Database session (will create one if not provided)
    
    Returns:
        Updated UsageEvent instance or None if not found
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    
    try:
        # Get the usage event
        usage_event = db.query(UsageEvent).filter(UsageEvent.id == event_id).first()
        if not usage_event:
            return None
        
        # Update units if provided
        if units is not None:
            usage_event.units = units
        
        # Update cost if provided, otherwise recalculate
        if cost_cents is not None:
            usage_event.cost_cents = cost_cents
        else:
            rate_cents = get_usage_rate_cents()
            usage_event.cost_cents = usage_event.calculate_cost(rate_cents)
        
        # Update metadata if provided
        if metadata is not None:
            usage_event.metadata = metadata
        
        db.commit()
        db.refresh(usage_event)
        
        return usage_event
        
    except Exception as e:
        db.rollback()
        # Log error but don't fail the main request
        print(f"Error finalizing usage event: {e}")
        return None
        
    finally:
        if close_db:
            db.close()


def get_usage_event_by_request_id(
    request_id: str,
    db: Optional[Session] = None
) -> Optional[UsageEvent]:
    """
    Get usage event by request ID.
    
    Args:
        request_id: Request identifier
        db: Database session (will create one if not provided)
    
    Returns:
        UsageEvent instance or None if not found
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    
    try:
        return UsageEvent.get_by_request_id(db, request_id)
    finally:
        if close_db:
            db.close()


def calculate_usage_cost(units: float, custom_rate_cents: Optional[int] = None) -> int:
    """
    Calculate usage cost for given units.
    
    Args:
        units: Number of units
        custom_rate_cents: Custom rate in cents (uses env default if not provided)
    
    Returns:
        Cost in cents
    """
    rate_cents = custom_rate_cents or get_usage_rate_cents()
    return int(units * rate_cents)


def get_tenant_usage_summary(
    tenant_id: str,
    start_date: datetime,
    end_date: datetime,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Get usage summary for a tenant within a date range.
    
    Args:
        tenant_id: Tenant identifier
        start_date: Start date (UTC)
        end_date: End date (UTC)
        db: Database session (will create one if not provided)
    
    Returns:
        Usage summary dictionary
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    
    try:
        return UsageEvent.get_usage_summary(db, tenant_id, start_date, end_date)
    finally:
        if close_db:
            db.close()


def is_billable_route(route: str) -> bool:
    """
    Check if a route is billable based on environment configuration.
    
    Args:
        route: API route path
    
    Returns:
        True if route is billable, False otherwise
    """
    billable_routes = os.getenv('BILLABLE_ROUTES', '').split(',')
    billable_routes = [r.strip() for r in billable_routes if r.strip()]
    
    if not billable_routes:
        return False
    
    # Check if route matches any billable pattern
    for pattern in billable_routes:
        if route.startswith(pattern):
            return True
    
    return False


def generate_usage_report(
    tenant_id: str,
    start_date: datetime,
    end_date: datetime,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive usage report for a tenant.
    
    Args:
        tenant_id: Tenant identifier
        start_date: Start date (UTC)
        end_date: End date (UTC)
        db: Database session (will create one if not provided)
    
    Returns:
        Comprehensive usage report
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    
    try:
        # Get basic summary
        summary = UsageEvent.get_usage_summary(db, tenant_id, start_date, end_date)
        
        # Get route breakdown
        from sqlalchemy import func
        route_breakdown = db.query(
            UsageEvent.route,
            func.count(UsageEvent.id).label('count'),
            func.sum(UsageEvent.units).label('total_units'),
            func.sum(UsageEvent.cost_cents).label('total_cost_cents')
        ).filter(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.ts >= start_date,
            UsageEvent.ts <= end_date
        ).group_by(UsageEvent.route).all()
        
        # Format route breakdown
        routes = []
        for route_data in route_breakdown:
            routes.append({
                'route': route_data.route,
                'event_count': route_data.count,
                'total_units': float(route_data.total_units or 0),
                'total_cost_cents': int(route_data.total_cost_cents or 0)
            })
        
        return {
            **summary,
            'route_breakdown': routes,
            'current_rate_cents': get_usage_rate_cents()
        }
        
    finally:
        if close_db:
            db.close()