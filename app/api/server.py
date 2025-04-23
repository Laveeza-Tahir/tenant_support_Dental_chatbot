from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(title="Dental Chatbot API")

# ✅ Root endpoint
@app.get("/")
def root():
    return {"message": "APIs are working"}

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Include routes under /api
app.include_router(router, prefix="/api")
