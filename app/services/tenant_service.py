from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import logging

from app.models.tenant import TenantBase, TenantCreate, TenantUpdate, TenantInDB, TenantResponse
from app.models.user import UserCreate
from app.db.database import tenants_collection, DatabaseService
from app.services.auth_service import AuthService

class TenantService:
    """Service for managing tenant operations"""

    @staticmethod
    async def create_tenant(tenant_data: TenantCreate) -> TenantResponse:
        """Create a new tenant"""
        global tenants_collection
        if tenants_collection is None:
            logging.warning("tenants_collection is None. Reinitializing database.")
            await DatabaseService.initialize()
            tenants_collection = await DatabaseService.get_collection("tenants")
            if tenants_collection is None:
                raise ValueError("Failed to initialize tenants_collection after reinitialization.")

        # Ensure tenant_data is an instance of TenantCreate
        if isinstance(tenant_data, dict):
            tenant_data = TenantCreate.parse_obj(tenant_data)

        # Check if tenant already exists
        existing_tenant = await tenants_collection.find_one({"name": tenant_data.name})
        if existing_tenant:
            raise ValueError(f"Tenant with name '{tenant_data.name}' already exists")

        # Generate ID for tenant
        tenant_id = str(uuid.uuid4())
        
        # Create tenant record
        tenant = TenantInDB(
            id=tenant_id,
            name=tenant_data.name,
            description=tenant_data.description,
            contact_email=tenant_data.contact_email,
            admin_user_id=None,  # No admin user created
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True,
            settings={
                "bot_name": f"{tenant_data.name} Assistant",
                "welcome_message": f"Welcome to {tenant_data.name}! How can I help you today?",
                "primary_color": "#3B82F6",
                "allowed_file_types": ["pdf", "docx", "txt"],
                "max_files": 50,
                "max_file_size_mb": 5,
                "calendar_integration": False
            }
        )
        
        # Insert into database
        await tenants_collection.insert_one(tenant.dict())
        
        # Initialize tenant-specific database collections
        tenant_db = DatabaseService.get_tenant_db(tenant_id)
        await tenant_db.conversations.create_index([("bot_id", 1), ("updated_at", -1)])
        await tenant_db.knowledge_base.create_index("name", unique=True)
        
        # Create initial collections
        return TenantResponse(**tenant.dict())
        
    @staticmethod
    async def get_tenant(tenant_id: str) -> Optional[TenantResponse]:
        """Get a tenant by ID"""
        global tenants_collection
        if tenants_collection is None:
            logging.warning("tenants_collection is None. Reinitializing database.")
            await DatabaseService.initialize()
            tenants_collection = await DatabaseService.get_collection("tenants")
            if tenants_collection is None:
                raise ValueError("Failed to initialize tenants_collection after reinitialization.")

        # Proceed with fetching the tenant document
        tenant_doc = await tenants_collection.find_one({"id": tenant_id})
        if not tenant_doc:
            return None
        return TenantResponse(**tenant_doc)
        
    @staticmethod
    async def update_tenant(tenant_id: str, tenant_data: TenantUpdate) -> Optional[TenantResponse]:
        """Update a tenant"""
        # Check if tenant exists
        tenant_doc = await tenants_collection.find_one({"id": tenant_id})
        if not tenant_doc:
            return None
            
        # Create update data
        update_data = {k: v for k, v in tenant_data.dict(exclude_unset=True).items() if v is not None}
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update tenant
            await tenants_collection.update_one(
                {"id": tenant_id},
                {"$set": update_data}
            )
        
        # Get updated tenant
        updated_tenant = await tenants_collection.find_one({"id": tenant_id})
        return TenantResponse(**updated_tenant)
        
    @staticmethod
    async def list_tenants(skip: int = 0, limit: int = 100) -> List[TenantResponse]:
        """List all tenants"""
        global tenants_collection
        if tenants_collection is None:
            logging.warning("tenants_collection is None. Reinitializing database.")
            await DatabaseService.initialize()
            tenants_collection = await DatabaseService.get_collection("tenants")
            if tenants_collection is None:
                raise ValueError("Failed to initialize tenants_collection after reinitialization.")

        cursor = tenants_collection.find() \
                                  .sort("created_at", -1) \
                                  .skip(skip) \
                                  .limit(limit)
        tenants = await cursor.to_list(length=limit)
        return [TenantResponse(**tenant) for tenant in tenants]
        
    @staticmethod
    async def delete_tenant(tenant_id: str) -> bool:
        """Delete a tenant - DANGEROUS operation"""
        # Get tenant to verify it exists
        tenant = await tenants_collection.find_one({"id": tenant_id})
        if not tenant:
            return False
            
        # Delete from database
        result = await tenants_collection.delete_one({"id": tenant_id})
        
        # Delete the tenant database (should be done with caution)
        await DatabaseService.client.drop_database(
            DatabaseService.get_tenant_db_name(tenant_id)
        )
        
        return result.deleted_count > 0
