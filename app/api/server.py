from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.auth import router as auth_router
from app.api.upload import router as upload_router
from app.api.widget import router as widget_router
from fastapi.staticfiles import StaticFiles

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

# Include the auth router
app.include_router(auth_router, prefix="/auth")

# Include the upload router
app.include_router(upload_router, prefix="/files")

# Include the widget router
app.include_router(widget_router, prefix="/widget")

# ✅ Serve static files for widget JS/CSS/images
app.mount("/static", StaticFiles(directory="static"), name="static")