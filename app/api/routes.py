from fastapi import APIRouter
from pydantic import BaseModel
from app.core.workflows.main_workflow import DentalWorkflow
import re
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
    result = await wf.run(req.session_id, req.message)

    # Remove all occurrences of [Source: ...]
    cleaned_response = re.sub(r"\[Source(?:\:.*?)?\]", "", result['response']).strip()


    return ChatResponse(response=cleaned_response, sources=result['sources'])