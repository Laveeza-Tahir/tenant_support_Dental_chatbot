from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from datetime import datetime
from typing import Optional

from app.api.routes import router
from app.db.database import init_db, DatabaseService
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create FastAPI instance
app = FastAPI(
    title="Multi-Tenant SaaS Chatbot API",
    description="A platform for managing chatbots across multiple tenants with customizable knowledge bases.",
    version="1.0.0",
)

# ✅ Root endpoint
@app.get("/")
def root():
    return {
        "message": "APIs are working",
        "version": "1.0.0",
        "status": "operational"
    }

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Get client IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_host = forwarded.split(",")[0].strip()
    else:
        client_host = request.client.host if request.client else "unknown"
    
    # Log request
    logging.info(f"Request: {request.method} {request.url.path} from {client_host}")
    
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logging.info(f"Response: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
    
    # Add processing time header
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    
    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the error
    logging.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Return error response
    return JSONResponse(
        status_code=500,
        content={
            "message": "An internal server error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logging.info("Server starting...")
    await init_db()
    logging.info("Database initialized")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logging.info("Server shutting down...")
    await DatabaseService.close()
    logging.info("Database connection closed")

# Include routes under /api
app.include_router(router, prefix="/api")
