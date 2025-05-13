
# Multi-Tenant SaaS Chatbot Platform

A powerful multi-tenant chatbot platform built with retrieval-augmented generation (RAG), FastAPI, MongoDB, and LangChain. Enables businesses to deploy customized AI chatbots with tenant isolation, document management, and conversational capabilities.

---

## Features

### Multi-Tenant Architecture
- **Complete tenant isolation**: Data, chats, and settings isolated per tenant
- **Tenant-specific customization**: Custom branding, prompts and behavior
- **Multi-user support**: Admin and user roles with granular permissions

### Advanced RAG Capabilities
- **Document processing**: Upload PDF, DOCX, and TXT files for knowledge bases
- **Vector databases**: ChromaDB for per-tenant similarity search
- **LangGraph workflows**: Configurable RAG pipelines with state management

### Platform Features
- **Authentication**: JWT-based auth with role-based permissions
- **API-First design**: RESTful APIs for all platform functions
- **Conversation history**: Persistent chat history with metadata
- **Analytics**: Track chatbot performance and usage metrics
- **Legacy support**: Compatible with existing dental chatbot implementation

---

## Architecture Overview

```
┌──────────────────┐     ┌───────────────────┐
│   SaaS ChatBot   │     │    Admin Panel    │
│      Frontend    │     │      Frontend     │
└────────┬─────────┘     └─────────┬─────────┘
         │                         │
         │                         │
         │                         │
         │     ┌─────────────────────────────┐
         └─────►  Multi-Tenant SaaS API      │
               │  - Authentication           │
               │  - Tenant Management        │
               │  - Bot Management           │
               │  - Chat Endpoints           │
               └────────────┬────────────────┘
                            │
                 ┌──────────┴───────────┐
                 │                      │
    ┌────────────▼──────────┐   ┌───────▼──────────────┐
    │  Document Processing  │   │   LangGraph Engine   │
    │  - File Uploads       │   │   - RAG Workflow     │
    │  - Text Extraction    │   │   - LLM Integration  │
    └────────────┬──────────┘   └───────┬──────────────┘
                 │                      │
      ┌──────────▼──────────────────────▼──────────┐
      │                Databases                   │
      │ - MongoDB (tenant data, conversations)     │
      │ - ChromaDB (per-tenant vector databases)   │
      └───────────────────────────────────────────┘
```

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/saas-chatbot-platform.git
cd saas-chatbot-platform
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file in the root:
```
MONGO_URI=mongodb://localhost:27017
GOOGLE_API_KEY=your_google_gemini_api_key
SECRET_KEY=your_jwt_secret_key
```

### 5. Run the Server
```bash
uvicorn app.api.server:app --host 0.0.0.0 --port 8000 --reload
```

Then visit: [http://localhost:8000/docs](http://localhost:8000/docs) for API documentation

---

## API Overview

| Method | Endpoint                            | Description                         |
|--------|-------------------------------------|-------------------------------------|
| POST   | `/api/auth/token`                   | Get authentication token            |
| POST   | `/api/tenants`                      | Create new tenant                   |
| GET    | `/api/tenants/{tenant_id}/bots`     | List tenant bots                    |
| POST   | `/api/tenants/{tenant_id}/files`    | Upload tenant knowledge base files  |
| POST   | `/api/tenants/{tenant_id}/chat`     | Chat with tenant bot                |

> Full API documentation available in Swagger at `/docs`

---

## Key Components

- **Tenant Management**: Complete tenant lifecycle management with isolation
- **Bot Service**: Configure and customize chatbots per tenant
- **Document Service**: Process and vectorize documents for knowledge bases
- **Conversation Service**: Handle chat sessions and message processing
- **LangGraph Service**: Configurable RAG workflows with state management

---

## 📜 License

MIT © 2025

---

## 🤝 Contributing

Pull requests welcome. Let's improve multi-tenant AI experiences together!

