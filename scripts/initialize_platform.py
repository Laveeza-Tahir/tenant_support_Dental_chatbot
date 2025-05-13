import asyncio
import sys
import logging
import json
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import init_db, tenants_collection, users_collection, bots_collection
from app.models.tenant import TenantCreate
from app.services.tenant_service import TenantService
from app.services.bot_service import BotService
from app.models.bot import BotCreate, BotType, BotEngine
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

async def setup_demo_tenant():
    """Set up a demo tenant with sample data"""
    # Check if demo tenant already exists
    demo_tenant = await tenants_collection.find_one({"name": "Demo Dental Clinic"})
    if demo_tenant:
        logging.info("Demo tenant already exists. Skipping...")
        return demo_tenant["id"]
        
    # Create demo tenant
    tenant_data = TenantCreate(
        name="Demo Dental Clinic",
        description="A demo dental clinic tenant for testing",
        contact_email="admin@demotenant.com",
        admin_email="admin@demotenant.com",
        admin_password="Password123!"  # In production, use a secure password
    )
    
    logging.info("Creating demo tenant...")
    try:
        tenant = await TenantService.create_tenant(tenant_data)
        logging.info(f"Demo tenant created with ID: {tenant.id}")
        
        # Create a demo bot
        bot_data = BotCreate(
            name="Dental Assistant",
            description="A helpful dental assistant chatbot",
            tenant_id=tenant.id,
            bot_type=BotType.FAQ,
            engine=BotEngine.GOOGLE_GEMINI,
            custom_instructions=(
                "You are a friendly dental assistant chatbot. "
                "Answer questions about dental procedures, oral health, "
                "and provide helpful advice. Be informative but not overly technical."
            ),
            settings={
                "welcome_message": "👋 Hello! I'm your virtual dental assistant. How can I help you today?",
                "primary_color": "#4F81BD",
                "bot_avatar": "🦷"
            }
        )
        
        logging.info("Creating demo bot...")
        bot = await BotService.create_bot(bot_data)
        logging.info(f"Demo bot created with ID: {bot.id}")
        
        return tenant.id
        
    except Exception as e:
        logging.error(f"Error creating demo tenant: {str(e)}")
        return None

async def import_dental_faq():
    """Import the dental FAQ data to the demo tenant"""
    # Get demo tenant ID
    demo_tenant = await tenants_collection.find_one({"name": "Demo Dental Clinic"})
    if not demo_tenant:
        logging.error("Demo tenant not found. Run setup_demo_tenant first.")
        return
        
    tenant_id = demo_tenant["id"]
    
    # Check if we have any bots for this tenant
    bot = await bots_collection.find_one({"tenant_id": tenant_id})
    if not bot:
        logging.error("No bots found for demo tenant.")
        return
        
    # Get the dental FAQ data
    try:
        with open("data/dental_faqs.json", "r") as f:
            faqs = json.load(f)
            
        # In a real application, you'd use DocumentService to process these properly
        # For this demo, we'll just log the info
        logging.info(f"Loaded {len(faqs)} dental FAQs")
        logging.info("In a production setup, these would be added to the tenant's knowledge base")
        
    except Exception as e:
        logging.error(f"Error loading dental FAQs: {str(e)}")

async def main():
    """Main initialization function"""
    logging.info("Initializing SaaS Chatbot Platform...")
    
    try:
        # Initialize database
        await init_db()
        logging.info("Database initialized")
        
        # Set up demo tenant
        tenant_id = await setup_demo_tenant()
        if tenant_id:
            # Import dental FAQ data
            await import_dental_faq()
            
        logging.info("Initialization completed successfully")
        
    except Exception as e:
        logging.error(f"Initialization failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
