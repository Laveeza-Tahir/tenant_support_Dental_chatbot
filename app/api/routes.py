from fastapi import APIRouter
from pydantic import BaseModel
from app.core.workflows.main_workflow import DentalWorkflow

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: list[str]

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    wf = DentalWorkflow()
    return await wf.run(req.session_id, req.message)
