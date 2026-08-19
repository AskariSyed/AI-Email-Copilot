# AI Email Copilot

An intelligent, context-aware AI assistant that plugs directly into your Gmail account. It reads your inbox, understands your communication style using Retrieval-Augmented Generation (RAG), and drafts personalized, highly accurate email replies.

## 🚀 Features

- **OAuth2 Gmail Integration**: Securely connect and sync your Gmail inbox using official Google APIs.
- **RAG-Powered AI Replies**: Uses vector embeddings to search your historical sent and received emails. The AI reads past threads and similar emails to match your exact tone and context.
- **AI Style Profile**: Provide permanent global instructions to the AI (e.g., "Keep it short", "Use bullet points") that apply to every draft it writes.
- **Secure HTML Rendering**: Reads rich HTML emails beautifully while isolating malicious scripts in a sandboxed iframe.
- **Infinite Scroll Inbox**: Seamlessly scroll through massive archives of emails directly from your local database.
- **Premium UI/UX**: Built with a stunning, modern glassmorphic interface featuring micro-animations, gradients, and dynamic hover states.

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with `pgvector` for vector similarity search
- **ORM**: SQLAlchemy + Alembic for migrations
- **AI/LLM**: Groq API (Llama/GPT OSS models) for lightning-fast text generation
- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`) running locally for privacy and cost-efficiency
- **Integrations**: Google Auth & Gmail API

### Frontend
- **Framework**: React 18 + Vite
- **Language**: TypeScript
- **Styling**: TailwindCSS v4 (Utility-first CSS)
- **Architecture**: Context-driven component design with a top-navbar layout

## ⚙️ Setup Instructions

### 1. Database Setup
Ensure you have PostgreSQL installed with the `pgvector` extension enabled.
```sql
CREATE EXTENSION vector;
```

### 2. Backend Configuration
Navigate to the `backend/` directory and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:
```env
DATABASE_URL=postgresql://user:password@localhost/email_copilot
GROQ_API_KEY=your_groq_api_key
LLM_MODEL=openai/gpt-oss-120b
```

Run database migrations and start the server:
```bash
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Configuration
Navigate to the `frontend/` directory and install dependencies:
```bash
npm install
```

Start the development server:
```bash
npm run dev
```
The app will be available at `http://localhost:5173`.

## 🔒 Privacy & Security
- The application never trains a public LLM on your emails. Your emails are vectorized locally and stored in your own PostgreSQL database.
- RAG injects only the most relevant snippets of context into the prompt at runtime.
- Emails are stripped of potentially harmful scripts and rendered in a strict `sandbox` iframe to prevent Cross-Site Scripting (XSS).
