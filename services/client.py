# services/client.py

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta
import secrets
import string

from models.client import Client, ClientType, ClientStatus, ClientPriority
from models.user import User
from schemas.client.core import (
    ClientCreate, ClientUpdate, ClientFilter, ClientStats, 
    ClientBulkAction, ClientBulkResult
)
from core.exceptions import NotFoundError, ValidationError


class ClientService:
    """Service layer for client management with multi-tenant support."""
    
    @staticmethod
    def generate_client_slug(first_name: str, last_name: str, organization_id: int) -> str:
        """Generate a unique slug for the client."""
        base_slug = f"{first_name.lower()}-{last_name.lower()}".replace(" ", "-")
        # Remove special characters
        base_slug = "".join(c for c in base_slug if c.isalnum() or c == "-")
        
        # Add random suffix to ensure uniqueness
        suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
        return f"{base_slug}-{suffix}"
    
    @staticmethod
    def create_client(
        db: Session, 
        client_data: ClientCreate, 
        organization_id: int, 
        created_by_id: int
    ) -> Client:
        """Create a new client with organization isolation."""
        
        # Check if client with same email exists in organization
        if client_data.email:
            existing_client = db.query(Client).filter(
                and_(
                    Client.email == client_data.email,
                    Client.organization_id == organization_id,
                    Client.is_deleted == False
                )
            ).first()
            
            if existing_client:
                raise ValidationError(f"Client with email {client_data.email} already exists")
        
        # Generate unique slug
        slug = ClientService.generate_client_slug(
            client_data.first_name, 
            client_data.last_name, 
            organization_id
        )
        
        # Create client
        client = Client(
            slug=slug,
            first_name=client_data.first_name,
            last_name=client_data.last_name,
            email=client_data.email,
            phone=client_data.phone,
            date_of_birth=client_data.date_of_birth,
            company_name=client_data.company_name,
            job_title=client_data.job_title,
            client_type=client_data.client_type,
            status=client_data.status,
            priority=client_data.priority,
            preferred_language=client_data.preferred_language,
            notes=client_data.notes,
            external_id=client_data.external_id,
            source=client_data.source,
            referral_source=client_data.referral_source,
            organization_id=organization_id,
            created_by_id=created_by_id,
            assigned_to_id=client_data.assigned_to_id,
            tags=client_data.tags or []
        )
        
        # Set address if provided
        if client_data.address:
            client.address_line1 = client_data.address.line1
            client.address_line2 = client_data.address.line2
            client.city = client_data.address.city
            client.state_province = client_data.address.state_province
            client.postal_code = client_data.address.postal_code
            client.country = client_data.address.country
        
        # Update computed fields
        client.update_full_name()
        
        db.add(client)
        db.commit()
        db.refresh(client)
        
        return client
    
    @staticmethod
    def get_client(db: Session, client_id: int, organization_id: int) -> Optional[Client]:
        """Get a client by ID with organization isolation."""
        return db.query(Client).filter(
            and_(
                Client.id == client_id,
                Client.organization_id == organization_id,
                Client.is_deleted == False
            )
        ).first()
    
    @staticmethod
    def get_client_by_slug(db: Session, slug: str, organization_id: int) -> Optional[Client]:
        """Get a client by slug with organization isolation."""
        return db.query(Client).filter(
            and_(
                Client.slug == slug,
                Client.organization_id == organization_id,
                Client.is_deleted == False
            )
        ).first()
    
    @staticmethod
    def update_client(
        db: Session, 
        client_id: int, 
        client_update: ClientUpdate, 
        organization_id: int,
        updated_by_id: int
    ) -> Optional[Client]:
        """Update a client with organization isolation."""
        client = ClientService.get_client(db, client_id, organization_id)
        if not client:
            raise NotFoundError("Client not found")
        
        # Check email uniqueness if updating email
        if client_update.email and client_update.email != client.email:
            existing_client = db.query(Client).filter(
                and_(
                    Client.email == client_update.email,
                    Client.organization_id == organization_id,
                    Client.id != client_id,
                    Client.is_deleted == False
                )
            ).first()
            
            if existing_client:
                raise ValidationError(f"Client with email {client_update.email} already exists")
        
        # Update fields
        update_data = client_update.dict(exclude_unset=True)
        
        # Handle address separately
        if 'address' in update_data:
            address = update_data.pop('address')
            if address:
                client.address_line1 = address.get('line1')
                client.address_line2 = address.get('line2')
                client.city = address.get('city')
                client.state_province = address.get('state_province')
                client.postal_code = address.get('postal_code')
                client.country = address.get('country')
        
        # Update other fields
        for field, value in update_data.items():
            setattr(client, field, value)
        
        # Update computed fields if name changed
        if 'first_name' in update_data or 'last_name' in update_data:
            client.update_full_name()
        
        db.commit()
        db.refresh(client)
        
        return client
    
    @staticmethod
    def delete_client(db: Session, client_id: int, organization_id: int) -> bool:
        """Soft delete a client with organization isolation."""
        client = ClientService.get_client(db, client_id, organization_id)
        if not client:
            raise NotFoundError("Client not found")
        
        # Check if client has any cases
        if client.cases:
            raise ValidationError("Cannot delete client with associated cases")
        
        client.soft_delete()
        db.commit()
        
        return True
    
    @staticmethod
    def list_clients(
        db: Session, 
        organization_id: int, 
        filters: Optional[ClientFilter] = None,
        skip: int = 0, 
        limit: int = 100,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> Tuple[List[Client], int]:
        """List clients with filtering, pagination, and organization isolation."""
        
        query = db.query(Client).filter(
            and_(
                Client.organization_id == organization_id,
                Client.is_deleted == False
            )
        )
        
        # Apply filters
        if filters:
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Client.first_name.ilike(search_term),
                        Client.last_name.ilike(search_term),
                        Client.full_name.ilike(search_term),
                        Client.email.ilike(search_term),
                        Client.company_name.ilike(search_term)
                    )
                )
            
            if filters.client_type:
                query = query.filter(Client.client_type == filters.client_type)
            
            if filters.status:
                query = query.filter(Client.status == filters.status)
            
            if filters.priority:
                query = query.filter(Client.priority == filters.priority)
            
            if filters.assigned_to_id:
                query = query.filter(Client.assigned_to_id == filters.assigned_to_id)
            
            if filters.tags:
                for tag in filters.tags:
                    query = query.filter(Client.tags.contains([tag]))
            
            if filters.created_after:
                query = query.filter(Client.created_at >= filters.created_after)
            
            if filters.created_before:
                query = query.filter(Client.created_at <= filters.created_before)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply ordering
        if order_direction.lower() == "desc":
            query = query.order_by(desc(getattr(Client, order_by, Client.created_at)))
        else:
            query = query.order_by(asc(getattr(Client, order_by, Client.created_at)))
        
        # Apply pagination
        clients = query.offset(skip).limit(limit).all()
        
        return clients, total
    
    @staticmethod
    def get_client_stats(db: Session, organization_id: int) -> ClientStats:
        """Get client statistics for an organization."""
        
        base_query = db.query(Client).filter(
            and_(
                Client.organization_id == organization_id,
                Client.is_deleted == False
            )
        )
        
        total_clients = base_query.count()
        active_clients = base_query.filter(Client.status == ClientStatus.ACTIVE).count()
        prospects = base_query.filter(Client.status == ClientStatus.PROSPECT).count()
        
        # Count by type
        by_type = {}
        for client_type in ClientType:
            count = base_query.filter(Client.client_type == client_type).count()
            by_type[client_type.value] = count
        
        # Count by status
        by_status = {}
        for status in ClientStatus:
            count = base_query.filter(Client.status == status).count()
            by_status[status.value] = count
        
        # Count by priority
        by_priority = {}
        for priority in ClientPriority:
            count = base_query.filter(Client.priority == priority).count()
            by_priority[priority.value] = count
        
        # Recent clients (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_clients = base_query.filter(Client.created_at >= thirty_days_ago).count()
        
        return ClientStats(
            total_clients=total_clients,
            active_clients=active_clients,
            prospects=prospects,
            by_type=by_type,
            by_status=by_status,
            by_priority=by_priority,
            recent_clients=recent_clients
        )
    
    @staticmethod
    def bulk_update_clients(
        db: Session, 
        bulk_action: ClientBulkAction, 
        organization_id: int,
        updated_by_id: int
    ) -> ClientBulkResult:
        """Perform bulk operations on clients."""
        
        result = ClientBulkResult()
        
        for client_id in bulk_action.client_ids:
            try:
                client = ClientService.get_client(db, client_id, organization_id)
                if not client:
                    result.error_count += 1
                    result.errors.append({
                        "client_id": client_id,
                        "error": "Client not found"
                    })
                    continue
                
                # Perform action
                if bulk_action.action == "update_status":
                    new_status = bulk_action.parameters.get("status")
                    if new_status and new_status in [s.value for s in ClientStatus]:
                        client.status = ClientStatus(new_status)
                        result.success_count += 1
                        result.updated_clients.append(client_id)
                    else:
                        result.error_count += 1
                        result.errors.append({
                            "client_id": client_id,
                            "error": "Invalid status"
                        })
                
                elif bulk_action.action == "update_priority":
                    new_priority = bulk_action.parameters.get("priority")
                    if new_priority and new_priority in [p.value for p in ClientPriority]:
                        client.priority = ClientPriority(new_priority)
                        result.success_count += 1
                        result.updated_clients.append(client_id)
                    else:
                        result.error_count += 1
                        result.errors.append({
                            "client_id": client_id,
                            "error": "Invalid priority"
                        })
                
                elif bulk_action.action == "assign_to":
                    assigned_to_id = bulk_action.parameters.get("assigned_to_id")
                    if assigned_to_id:
                        # Verify user exists and belongs to organization
                        user = db.query(User).filter(
                            and_(
                                User.id == assigned_to_id,
                                User.organization_id == organization_id,
                                User.is_active == True
                            )
                        ).first()
                        
                        if user:
                            client.assigned_to_id = assigned_to_id
                            result.success_count += 1
                            result.updated_clients.append(client_id)
                        else:
                            result.error_count += 1
                            result.errors.append({
                                "client_id": client_id,
                                "error": "Invalid assigned user"
                            })
                    else:
                        client.assigned_to_id = None
                        result.success_count += 1
                        result.updated_clients.append(client_id)
                
                elif bulk_action.action == "add_tags":
                    tags_to_add = bulk_action.parameters.get("tags", [])
                    for tag in tags_to_add:
                        client.add_tag(tag)
                    result.success_count += 1
                    result.updated_clients.append(client_id)
                
                elif bulk_action.action == "remove_tags":
                    tags_to_remove = bulk_action.parameters.get("tags", [])
                    for tag in tags_to_remove:
                        client.remove_tag(tag)
                    result.success_count += 1
                    result.updated_clients.append(client_id)
                
                else:
                    result.error_count += 1
                    result.errors.append({
                        "client_id": client_id,
                        "error": f"Unknown action: {bulk_action.action}"
                    })
                
            except Exception as e:
                result.error_count += 1
                result.errors.append({
                    "client_id": client_id,
                    "error": str(e)
                })
        
        if result.success_count > 0:
            db.commit()
        
        return result
    
    @staticmethod
    def get_cases_for_client(db: Session, client_id: int, organization_id: int) -> List:
        """Get all cases for a specific client."""
        from models.case import Case  # Import here to avoid circular imports
        
        client = ClientService.get_client(db, client_id, organization_id)
        if not client:
            raise NotFoundError("Client not found")
        
        return db.query(Case).filter(
            and_(
                Case.client_id == client_id,
                Case.organization_id == organization_id,
                Case.is_deleted == False
            )
        ).order_by(desc(Case.created_at)).all()
    
    @staticmethod
    def search_clients(
        db: Session, 
        organization_id: int, 
        search_term: str, 
        limit: int = 10
    ) -> List[Client]:
        """Quick search for clients (for typeahead/autocomplete)."""
        
        search_pattern = f"%{search_term}%"
        
        return db.query(Client).filter(
            and_(
                Client.organization_id == organization_id,
                Client.is_deleted == False,
                or_(
                    Client.first_name.ilike(search_pattern),
                    Client.last_name.ilike(search_pattern),
                    Client.full_name.ilike(search_pattern),
                    Client.email.ilike(search_pattern),
                    Client.company_name.ilike(search_pattern)
                )
            )
        ).order_by(Client.full_name).limit(limit).all()
