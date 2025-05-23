from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, validator
from app.api.auth import get_current_user
from typing import Optional
import os
import json
import re

router = APIRouter()

WIDGET_CONFIG_DIR = "widget_configs"
os.makedirs(WIDGET_CONFIG_DIR, exist_ok=True)

class WidgetSettings(BaseModel):
    theme: Optional[str] = "light"
    primary_color: Optional[str] = "#060dcf"  # Updated to match widget theme
    secondary_color: Optional[str] = "#e3e7ee"  # Updated to match message bubbles
    chatbot_name: Optional[str] = "DentalBot"
    welcome_message: Optional[str] = "Welcome to DentalBot! How can I assist you today?"
    bot_avatar: Optional[str] = "/static/img/botAvatar.png"
    user_avatar: Optional[str] = "/static/img/userAvatar.jpg"
    widget_width: Optional[str] = "350px"
    widget_height: Optional[str] = "500px"
    position: Optional[str] = "right"  # right or left
    show_timestamp: Optional[bool] = True
    enable_voice: Optional[bool] = False
    enable_attachments: Optional[bool] = False

    @validator('theme')
    def validate_theme(cls, v):
        if v not in ['light', 'dark']:
            raise ValueError('Theme must be either "light" or "dark"')
        return v

    @validator('primary_color', 'secondary_color')
    def validate_color(cls, v):
        if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', v):
            raise ValueError('Color must be a valid hex color code (e.g., #FF0000)')
        return v

    @validator('position')
    def validate_position(cls, v):
        if v not in ['right', 'left']:
            raise ValueError('Position must be either "right" or "left"')
        return v

    @validator('widget_width', 'widget_height')
    def validate_dimensions(cls, v):
        if not re.match(r'^\d+(%|px|em|rem|vh|vw)$', v):
            raise ValueError('Dimensions must be a valid CSS size (e.g., 350px, 50%, 20em)')
        return v

@router.post("/widget/settings")
async def save_widget_settings(
    settings: WidgetSettings,
    current_user: str = Depends(get_current_user)
):
    user_config_path = os.path.join(WIDGET_CONFIG_DIR, f"{current_user.email}.json")
    with open(user_config_path, "w") as f:
        json.dump(settings.dict(), f)
    return {"message": "Widget settings saved successfully."}

@router.get("/widget/settings")
async def get_widget_settings(
    current_user: str = Depends(get_current_user)
):
    user_config_path = os.path.join(WIDGET_CONFIG_DIR, f"{current_user.email}.json")
    if not os.path.exists(user_config_path):
        raise HTTPException(status_code=404, detail="Widget settings not found.")
    with open(user_config_path, "r") as f:
        settings = json.load(f)
    return settings

@router.get("/widget/code")
async def generate_widget_code(
    request: Request,
    current_user: str = Depends(get_current_user)
):
    user_config_path = os.path.join(WIDGET_CONFIG_DIR, f"{current_user.email}.json")
    if not os.path.exists(user_config_path):
        raise HTTPException(status_code=404, detail="Widget settings not found.")
    with open(user_config_path, "r") as f:
        settings = json.load(f)    # Include API endpoint configuration
    api_config = {
        **settings,
        "apiEndpoint": "/api/chat",  # Chat endpoint
        "baseUrl": "{{request.base_url}}",  # Dynamic base URL from request
        "userId": current_user.email,
        "authenticated": True
    }

    # Generate the widget code with both CSS and JS
    widget_code = f"""
    <!-- Dental Chatbot Widget -->
    <link rel="stylesheet" href="{api_config['baseUrl']}/static/css/widget.css">
    <script>
        (function() {{
            const chatbotSettings = {json.dumps(api_config)};
            const script = document.createElement('script');
            script.src = '{api_config['baseUrl']}/static/js/chat-widget.js';
            script.onload = function() {{
                window.initializeChatWidget(chatbotSettings);
            }};
            document.head.appendChild(script);
        }})();
    </script>
    """
    return {"widget_code": widget_code}
