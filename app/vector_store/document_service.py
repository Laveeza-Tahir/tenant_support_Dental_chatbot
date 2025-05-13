import os
import uuid
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional, BinaryIO, Tuple
from datetime import datetime

# Text extraction libraries
import fitz  # PyMuPDF for PDF
import docx2txt  # For DOCX

from app.models.file import FileCreate, FileInDB, FileStatus, FileType
from app.db.database import DatabaseService
from app.vector_store.vector_db_service import VectorDBService

# Ensure chroma_db is defined
chroma_db = VectorDBService

class DocumentService:
    """Service for handling document uploads and processing"""
    
    UPLOADS_DIR = "data/uploads"
    
    @classmethod
    def get_tenant_upload_dir(cls, tenant_id: str) -> str:
        """Get upload directory for a tenant"""
        tenant_dir = os.path.join(cls.UPLOADS_DIR, tenant_id)
        os.makedirs(tenant_dir, exist_ok=True)
        return tenant_dir
    
    @classmethod
    async def save_uploaded_file(
        cls, 
        tenant_id: str, 
        bot_id: str,  # Added bot_id
        file: BinaryIO, 
        filename: str,
        description: Optional[str] = None
    ) -> FileInDB:
        """Save an uploaded file and create database entry"""
        # Generate a unique ID for the file
        file_id = str(uuid.uuid4())
        
        # Determine file type
        file_extension = filename.split('.')[-1].lower()
        if file_extension == 'pdf':
            file_type = FileType.PDF
        elif file_extension in ['doc', 'docx']:
            file_type = FileType.DOCX
        elif file_extension == 'txt':
            file_type = FileType.TXT
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
            
        # Create filesystem path
        tenant_dir = cls.get_tenant_upload_dir(tenant_id)
        file_path = os.path.join(tenant_dir, f"{file_id}.{file_extension}")
        
        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(file.read())
        
        # Get files collection via DatabaseService
        files_collection = await DatabaseService.get_collection("files")
        if files_collection is None:
            raise ValueError("Failed to initialize files_collection after reinitialization.")
        
        # Create database entry
        file_data = FileInDB(
            id=file_id,
            filename=filename,
            file_type=file_type,
            tenant_id=tenant_id,
            bot_id=bot_id,  # Added bot_id
            description=description,
            status=FileStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ).dict()
        
        # Insert into database
        await files_collection.insert_one(file_data)
        
        # Start processing in background
        asyncio.create_task(cls.process_file(file_id, tenant_id, bot_id, file_path, file_type))  # Added bot_id
        
        return FileInDB(**file_data)
    
    @classmethod
    async def process_file(
        cls, 
        file_id: str, 
        tenant_id: str, 
        bot_id: str,  # Added bot_id
        file_path: str, 
        file_type: FileType
    ):
        """Process a file and add to vector store"""
        files_collection = await DatabaseService.get_collection("files")
        if files_collection is None:
            raise ValueError("Failed to get files_collection in process_file.")
        try:
            logging.info(f"Starting file processing for file_id: {file_id}, tenant_id: {tenant_id}")

            # Update status to processing
            await files_collection.update_one(
                {"id": file_id},
                {"$set": {"status": FileStatus.PROCESSING, "updated_at": datetime.utcnow()}}
            )
            
            # Extract text based on file type
            text, metadata = await cls.extract_text(file_path, file_type)
            
            if not text:
                raise ValueError("No text extracted from file")
                
            # Log extracted text and metadata
            if text:
                logging.debug(f"Extracted text (truncated): {text[:500]}...")
            else:
                logging.warning("No text extracted from the file.")
            logging.debug(f"Metadata: {metadata}")
                
            # Create vector DB service for this tenant and bot
            vector_db = VectorDBService(tenant_id, bot_id)
            
            # Add metadata about the file
            metadata["file_id"] = file_id
            metadata["tenant_id"] = tenant_id
            metadata["bot_id"] = bot_id  # Added bot_id
            metadata["processed_at"] = datetime.utcnow().isoformat()
            
            # Add to vector store
            result = await vector_db.add_texts(
                texts=[text],
                metadatas=[metadata],
                collection_name="default"
            )
            
            # Log vector store result
            logging.info(f"Vector store result for file_id {file_id}: {result}")
            
            # Update file status
            await files_collection.update_one(
                {"id": file_id},
                {
                    "$set": {
                        "status": FileStatus.INDEXED,
                        "indexed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "embedding_count": result["added_count"],
                        "token_count": len(text.split())  # Simple token counting
                    }
                }
            )
            
            logging.info(f"File {file_id} processed successfully with {result['added_count']} embeddings")
            
        except Exception as e:
            logging.error(f"Error processing file {file_id}: {e}")
            # Update file status to failed
            await files_collection.update_one(
                {"id": file_id},
                {
                    "$set": {
                        "status": FileStatus.FAILED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
    
    @classmethod
    async def extract_text(cls, file_path: str, file_type: FileType) -> Tuple[str, Dict[str, Any]]:
        """Extract text from a file based on its type"""
        text = ""
        metadata = {"source": file_path}
        
        if file_type == FileType.PDF:
            # Extract text from PDF
            try:
                pdf = fitz.open(file_path)
                metadata["page_count"] = len(pdf)
                metadata["title"] = pdf.metadata.get("title", "")
                metadata["author"] = pdf.metadata.get("author", "")
                
                text_parts = []
                for i, page in enumerate(pdf):
                    text_parts.append(page.get_text())
                    
                text = "\n\n".join(text_parts)
            except Exception as e:
                logging.error(f"Error extracting text from PDF: {e}")
                raise
                
        elif file_type == FileType.DOCX:
            # Extract text from DOCX
            try:
                text = docx2txt.process(file_path)
                metadata["word_count"] = len(text.split())
            except Exception as e:
                logging.error(f"Error extracting text from DOCX: {e}")
                raise
                
        elif file_type == FileType.TXT:
            # Read text file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                metadata["word_count"] = len(text.split())
            except Exception as e:
                logging.error(f"Error reading text file: {e}")
                raise
        
        return text, metadata
    
    @classmethod
    async def delete_file(cls, tenant_id: str, file_id: str) -> Dict[str, Any]:
        """Delete a file and its embeddings"""
        files_collection = await DatabaseService.get_collection("files")
        if files_collection is None:
            raise ValueError("Failed to get files_collection in delete_file.")

        # Get file info
        file_doc = await files_collection.find_one({"id": file_id, "tenant_id": tenant_id})
        if not file_doc:
            raise ValueError(f"File {file_id} not found for tenant {tenant_id}")
        
        # Delete file from disk if it exists
        file_extension = file_doc.get("file_type", "").lower()
        tenant_dir = cls.get_tenant_upload_dir(tenant_id)
        file_path = os.path.join(tenant_dir, f"{file_id}.{file_extension}")
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete embeddings from vector store
        vector_db = VectorDBService(tenant_id, file_doc.get("bot_id"))
        deleted_count = await vector_db.delete_by_filter({"file_id": file_id})
        
        # Delete file record from database
        await files_collection.delete_one({"id": file_id, "tenant_id": tenant_id})
        
        return {
            "id": file_id,
            "deleted_embeddings": deleted_count,
            "file_removed": os.path.exists(file_path)
        }
    
    @classmethod
    async def get_files(cls, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all files for a tenant"""
        files_collection = await DatabaseService.get_collection("files")
        if files_collection is None:
            raise ValueError("Failed to get files_collection in get_files.")

        cursor = files_collection.find({"tenant_id": tenant_id}) \
                               .sort("created_at", -1) \
                               .skip(skip) \
                               .limit(limit)
        return await cursor.to_list(length=limit)
    
    @staticmethod
    async def process_and_store_faqs(tenant_id: str, file: Any, filename: str) -> Dict[str, Any]:
        """Process and store FAQs in ChromaDB for a specific tenant."""
        # Read the file content
        content = file.read().decode("utf-8")

        # Parse the FAQs (assuming JSON format for simplicity)
        try:
            faqs = json.loads(content)
        except json.JSONDecodeError:
            raise ValueError("Invalid FAQ file format. Expected JSON.")

        # Store in ChromaDB with tenant isolation
        namespace = f"{tenant_id}_faqs"
        for faq in faqs:
            question = faq.get("question")
            answer = faq.get("answer")
            if not question or not answer:
                raise ValueError("Each FAQ must have a 'question' and an 'answer'.")

            # Add to ChromaDB (pseudo-code, replace with actual ChromaDB logic)
            chroma_db.add(namespace=namespace, question=question, answer=answer)

        return {"namespace": namespace, "faq_count": len(faqs)}

    @classmethod
    async def get_knowledge_base(cls, tenant_id: str, bot_id: str) -> List[Dict[str, Any]]:
        """Retrieve the knowledge base for a specific tenant and bot."""
        files_collection = await DatabaseService.get_collection("files")
        if files_collection is None:
            raise ValueError("Failed to initialize files_collection in get_knowledge_base.")

        try:
            # Query the files collection for documents associated with the tenant and bot
            documents = await files_collection.find({
                "tenant_id": tenant_id,
                "bot_id": bot_id,
                "status": FileStatus.INDEXED  # Use INDEXED instead of PROCESSED
            }).to_list(length=None)

            # Extract relevant data from the documents
            knowledge_base = [
                {
                    "id": doc["id"],
                    "filename": doc["filename"],
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {})
                }
                for doc in documents
            ]

            return knowledge_base
        except Exception as e:
            logging.error(f"Error retrieving knowledge base: {e}")
            return []
