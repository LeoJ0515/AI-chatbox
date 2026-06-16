# 🧠 AI Chatbox — Professional AI Assistant

A fully functional, real‑time AI chatbot with a stunning **Matrix‑inspired interface**. Built with **FastAPI**, **Groq** (Llama 3.3 70B), **Supabase** for persistent memory, and a modern frontend featuring typing animations, Markdown rendering, file uploads, and session management.

![Matrix UI Screenshot](https://via.placeholder.com/800x450/0a0f0a/00ff41?text=MATRIX+AI+Interface)

---

## ✨ Features

- 🤖 **Real AI Conversations** – Powered by **Llama 3.3 70B** via Groq (free tier)
- 💾 **Persistent Memory** – Conversations saved in Supabase (per session)
- 📎 **File Upload & Analysis** – Supports PDF, Word (.docx), Excel (.xlsx), CSV, text, code, and more
- ⌨️ **Live Typing Animation** – AI replies type out in real‑time, then morph into beautifully rendered Markdown
- 🎨 **Matrix‑Themed UI** – Green phosphor glow, animated Matrix rain, glass‑morphism panels
- 🌐 **Responsive Design** – Works flawlessly on desktop, tablet, and mobile
- 🧩 **Session Management** – Create, switch, and delete conversations (stored locally)
- 📋 **Code Highlighting & Copy** – Syntax highlighting for code blocks, one‑click copy
- 🖱️ **Drag‑and‑Drop File Upload** – Simply drag files onto the chat area
- 🔒 **Secure** – API keys kept server‑side, `.env` excluded from version control

---

## 🛠️ Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| **Backend** | Python, FastAPI, Uvicorn            |
| **AI Model**| Groq API (Llama 3.3 70B)            |
| **Database**| Supabase (PostgreSQL, session memory)|
| **Frontend**| HTML5, CSS3, JavaScript (vanilla)   |
| **Libraries**| `groq`, `supabase`, `PyPDF2`, `python-docx`, `openpyxl`, `google-genai` (optional for image descriptions) |
| **Markdown**| `marked.js`, `highlight.js` (CDN)   |

---

## 📁 Project Structure
AI-chatbox/
├── main.py # FastAPI backend
├── index.html # Frontend (Matrix UI)
├── .env.example # Environment variables template
├── .gitignore # Ignore secrets & venv
├── requirements.txt # Python dependencies
└── README.md


---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A [Groq API key](https://console.groq.com) (free)
- A [Supabase](https://supabase.com) project (free tier)

### 1. Clone the repository
```bash
git clone https://github.com/LeoJ0515/AI-chatbox.git
cd AI-chatbox
```

### 2. Set up virtual environment
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key
GROQ_API_KEY=gsk_your_groq_api_key
```

### 5. Set up Supabase table
```bash
create table conversations (
  id bigint generated always as identity primary key,
  session_id text unique not null,
  messages jsonb not null default '[]'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index idx_conversations_session_id on conversations(session_id);
```

### 6. Run the backend
```bash
uvicorn main:app --reload
```

### 7. Open the frontend
Simply open index.html in your browser, or serve it via a local server.
It will automatically connect to the backend at http://localhost:8000.


## 📦 Usage
Start a chat – Type a message and press Enter.

Upload files – Click the paperclip icon or drag & drop files onto the input area.

Switch sessions – Use the sidebar to navigate between conversations.

Copy code – Hover over any code block and click CPY.

New session – Click NEW SESSION in the sidebar.
