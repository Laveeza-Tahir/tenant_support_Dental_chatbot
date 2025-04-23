cat <<EOL > README.md
# 🦷 Dental Chatbot - Gemini

An intelligent dental FAQ chatbot powered by retrieval-augmented generation (RAG), FastAPI, FAISS, and Gemini Pro (Google Generative AI). This bot classifies user queries and retrieves relevant answers from a dental FAQs dataset using semantic search.

---

## 🚀 Features

- 💬 Natural language query handling with Google Gemini
- 🔎 Vector similarity search using FAISS
- 📂 Modular architecture for retrievers, workflows, and APIs
- 🔧 Configurable via `.env` and `settings.py`
- 🧠 Built-in classification and retrieval logic
- 🧪 API server using FastAPI
- 
---

## ⚙️ Setup Instructions

### 1. Clone the Repository
\`\`\`bash
git clone https://github.com/JM-JamalMustafa/Dental_chatbot.git
cd dental-chatbot-gemini
\`\`\`

### 2. Create a Virtual Environment
\`\`\`bash
python -m venv venv
source venv/bin/activate  # or venv\\Scripts\\activate on Windows
\`\`\`

### 3. Install Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. Configure Environment
Create a `.env` file in the root:
\`\`\`
GEMINI_API_KEY=your_google_gemini_api_key
\`\`\`

---

## 🛠️ Build FAISS Index

If not already built:

\`\`\`bash
python scripts/build_faiss.py
\`\`\`

---

## ▶️ Run the Server

\`\`\`bash
uvicorn app.api.server:app --host 0.0.0.0 --port 8000 --reload
\`\`\`

Then visit: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📡 API Overview

| Method | Endpoint       | Description                  |
|--------|----------------|------------------------------|
| POST   | `/chat`        | Handle user query via Gemini |
| GET    | `/health`      | Check service health         |

> Swagger docs available at `/docs`

---

## 🔍 Key Modules

- **Retrievers**: Semantic search via FAISS or MongoDB.
- **Workflows**: Modular nodes like input, classify, faq retrieval, output.
- **Models**: Sessions, questions, responses defined via Pydantic.

---


## 📜 License

MIT © 2025 - Jamal Mustafa

---

## 🤝 Contributing

Pull requests welcome. Let's improve dental query automation together!

EOL
