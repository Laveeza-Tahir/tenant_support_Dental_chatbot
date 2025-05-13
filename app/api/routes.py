from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import List, Optional, Dict, Any
import re
import logging

from app.models.tenant import TenantCreate, TenantResponse, TenantUpdate
from app.models.bot import BotCreate, BotResponse, BotUpdate
from app.models.conversation import ChatRequest, ChatResponse
from app.models.file import FileResponse
from app.services.tenant_service import TenantService
from app.services.bot_service import BotService
from app.services.conversation_service import ConversationService
from app.vector_store.document_service import DocumentService

# Legacy import for backward compatibility
from app.core.workflows.main_workflow import DentalWorkflow

# Create router
router = APIRouter()

# -------------------------------------------------------------------
# Tenant Management routes
# -------------------------------------------------------------------

@router.post("/tenants", response_model=TenantResponse)
async def create_tenant(tenant: TenantCreate):
    try:
        # Remove admin_email and admin_password from the tenant creation logic
        tenant_data = {
            "name": tenant.name,
            "description": tenant.description,
            "contact_email": tenant.contact_email
        }
        return await TenantService.create_tenant(tenant_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str):
    tenant = await TenantService.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, tenant_data: TenantUpdate):
    tenant = await TenantService.update_tenant(tenant_id, tenant_data)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.get("/tenants", response_model=List[TenantResponse])
async def list_tenants(skip: int = 0, limit: int = 100):
    return await TenantService.list_tenants(skip, limit)

# -------------------------------------------------------------------
# Bot Management routes
# -------------------------------------------------------------------

@router.post("/tenants/{tenant_id}/bots", response_model=BotResponse)
async def create_bot(tenant_id: str, bot_data: BotCreate):
    try:
        bot_data.tenant_id = tenant_id
        return await BotService.create_bot(bot_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tenants/{tenant_id}/bots/{bot_id}", response_model=BotResponse)
async def get_bot(tenant_id: str, bot_id: str):
    bot = await BotService.get_bot(tenant_id, bot_id)
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot

@router.put("/tenants/{tenant_id}/bots/{bot_id}", response_model=BotResponse)
async def update_bot(tenant_id: str, bot_id: str, bot_data: BotUpdate):
    bot = await BotService.update_bot(tenant_id, bot_id, bot_data)
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot

@router.get("/tenants/{tenant_id}/bots", response_model=List[BotResponse])
async def list_bots(tenant_id: str, skip: int = 0, limit: int = 100):
    return await BotService.list_bots(tenant_id, skip, limit)

# -------------------------------------------------------------------
# Document/Knowledge Base routes
# -------------------------------------------------------------------

@router.post("/tenants/{tenant_id}/bots/{bot_id}/files", response_model=FileResponse)  # Modified route
async def upload_file(tenant_id: str, bot_id: str, file: UploadFile = File(...), description: Optional[str] = Form(None)):  # Added bot_id
    try:
        return await DocumentService.save_uploaded_file(
            tenant_id=tenant_id,
            bot_id=bot_id,  # Pass bot_id
            file=file.file,
            filename=file.filename,
            description=description
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tenants/{tenant_id}/files", response_model=List[FileResponse])
async def list_files(tenant_id: str, skip: int = 0, limit: int = 100):
    return await DocumentService.get_files(tenant_id, skip, limit)

# -------------------------------------------------------------------
# Chat routes
# -------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Chat endpoint accepting only conversation_id, bot_id, tenant_id, and message."""
    wf = DentalWorkflow()
    result = await wf.run(req.conversation_id, req.message)
    cleaned_response = re.sub(r"\[Source(?:\:.*?)?\]", "", result['response']).strip()
    return ChatResponse(
        conversation_id=req.conversation_id,
        response=cleaned_response,
        sources=result['sources']
    )

@router.post("/tenants/{tenant_id}/chat", response_model=ChatResponse)
async def tenant_chat(tenant_id: str, chat_request: ChatRequest):
    chat_request.tenant_id = tenant_id

    # Fetch the knowledge base for the tenant and bot
    knowledge_base = await DocumentService.get_knowledge_base(tenant_id, chat_request.bot_id)

    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found for the specified tenant and bot."
        )

    try:
        # Pass the knowledge base to the conversation service
        return await ConversationService.process_chat_message(chat_request, knowledge_base)
    except Exception as e:
        logging.error(f"Error processing chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing chat message"
        )

# @router.post("/tenants/{tenant_id}/bots/{bot_id}/faqs", response_model=Dict[str, Any])
# async def upload_faqs(tenant_id: str, bot_id: str, file: UploadFile = File(...)):
#     try:
#         result = await DocumentService.process_and_store_faqs(
#             tenant_id=tenant_id,
#             bot_id=bot_id,
#             file=file.file,
#             filename=file.filename
#         )
#         return {"message": "FAQs uploaded successfully", "details": result}
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# -------------------------------------------------------------------
# Clinic Management routes
# -------------------------------------------------------------------

@router.put("/tenants/{tenant_id}/clinic/timings", response_model=TenantResponse)
async def update_clinic_timings(tenant_id: str, timings: Dict[str, str]):
    """Update clinic timings for a tenant."""
    tenant = await TenantService.update_tenant(tenant_id, {"clinic_timings": timings})
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.put("/tenants/{tenant_id}/clinic/calendar", response_model=TenantResponse)
async def update_clinic_calendar(tenant_id: str, calendar: List[Dict[str, Any]]):
    """Update clinic calendar for a tenant."""
    tenant = await TenantService.update_tenant(tenant_id, {"calendar": calendar})
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

# -------------------------------------------------------------------
# Appointment Scheduling routes
# -------------------------------------------------------------------

@router.post("/tenants/{tenant_id}/appointments", response_model=Dict[str, Any])
async def create_appointment(tenant_id: str, appointment: Dict[str, Any]):
    """Create an appointment for a tenant."""
    # Validate and add the appointment to the tenant's calendar
    tenant = await TenantService.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if "calendar" not in tenant:
        tenant["calendar"] = []

    tenant["calendar"].append(appointment)
    await TenantService.update_tenant(tenant_id, {"calendar": tenant["calendar"]})
    return {"message": "Appointment created successfully", "appointment": appointment}