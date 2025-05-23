import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from app.api.auth import get_current_user
from pathlib import Path
from PyPDF2 import PdfReader
from docx import Document
from app.core.chroma_manager import create_or_update_collection

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def extract_text_from_file(file_path: str, file_type: str) -> str:
    if file_type == "pdf":
        reader = PdfReader(file_path)
        extracted_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text.append(text)
        if not extracted_text:
            raise ValueError("No text could be extracted from the PDF. It might be an image-based PDF.")
        return "\n".join(extracted_text)
    elif file_type == "docx":
        doc = Document(file_path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    elif file_type == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError("Unsupported file type")

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    user_dir = Path(UPLOAD_DIR) / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = user_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        file_type = file.filename.split(".")[-1].lower()
        extracted_text = extract_text_from_file(str(file_path), file_type)
        
        # Update Chroma DB with the new document
        user_id = str(current_user.id)
        create_or_update_collection(user_id, extracted_text)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}",
        )

    return {"message": "File uploaded successfully and embeddings updated."}
