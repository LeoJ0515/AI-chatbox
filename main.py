import os
import json
import base64
import io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Dict, Optional

# New imports for document parsing
import PyPDF2
from docx import Document
from openpyxl import load_workbook

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY]):
    raise RuntimeError("Missing required environment variables in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

GROQ_MODEL = "llama-3.3-70b-versatile"
SYSTEM_PROMPT = (
    "You are a helpful, professional AI assistant. "
    "Answer questions accurately and in detail. "
    "If you receive file content, use it to answer the user's query."
)
MAX_HISTORY_CHARS = 50000

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FileAttachment(BaseModel):
    name: str
    type: str
    data: str  # base64

class ChatRequest(BaseModel):
    session_id: str
    message: str
    files: Optional[List[FileAttachment]] = []

class ChatResponse(BaseModel):
    reply: str

def load_messages(session_id: str) -> List[Dict[str, str]]:
    res = supabase.table("conversations") \
                  .select("messages") \
                  .eq("session_id", session_id) \
                  .execute()
    return res.data[0]["messages"] if res.data else []

def save_messages(session_id: str, messages: List[Dict[str, str]]):
    supabase.table("conversations") \
            .upsert({
                "session_id": session_id,
                "messages": messages,
                "updated_at": "now()"
            }, on_conflict="session_id") \
            .execute()

def trim_history(messages: List[Dict]) -> List[Dict]:
    total = sum(len(json.dumps(m)) for m in messages)
    while total > MAX_HISTORY_CHARS and len(messages) > 2:
        removed = messages.pop(0)
        if messages and messages[0]["role"] == "assistant":
            removed = messages.pop(0)
        total = sum(len(json.dumps(m)) for m in messages)
    return messages

def call_groq(messages: List[Dict]) -> str:
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=api_messages,
        temperature=0.7,
        max_tokens=4096,
    )
    return response.choices[0].message.content

def extract_file_content(file: FileAttachment) -> str:
    """
    Decode and extract text from supported file types.
    Returns the file content or a note if unsupported.
    """
    # Get file extension (lowercase)
    ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
    # Get bytes from base64
    try:
        file_bytes = base64.b64decode(file.data)
    except Exception:
        return f"[Error decoding file {file.name}]"

    # --- Text-based files (original) ---
    text_extensions = {'txt', 'csv', 'md', 'json', 'xml', 'yaml', 'yml', 'py', 'js',
                       'ts', 'html', 'css', 'sh', 'bat', 'log', 'ini', 'cfg', 'toml'}
    text_mime_prefixes = ["text/", "application/json", "application/javascript",
                          "application/xml", "application/x-python", "application/x-sh"]
    is_text = any(file.type.startswith(p) for p in text_mime_prefixes) or ext in text_extensions

    if is_text:
        try:
            text = file_bytes.decode('utf-8', errors='replace')
            return f"--- Content of {file.name} ---\n{text}\n--- End of file ---"
        except Exception as e:
            return f"[Error reading text file {file.name}: {str(e)}]"

    # --- PDF ---
    if ext == 'pdf' or file.type == 'application/pdf':
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            if not text.strip():
                return f"[PDF {file.name} contains no extractable text (maybe scanned image)]"
            return f"--- Content of {file.name} (PDF) ---\n{text}\n--- End of file ---"
        except Exception as e:
            return f"[Error reading PDF {file.name}: {str(e)}]"

    # --- Word (.docx) ---
    if ext == 'docx' or file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        try:
            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
            if not text.strip():
                text = "[Document appears empty]"
            return f"--- Content of {file.name} (Word) ---\n{text}\n--- End of file ---"
        except Exception as e:
            return f"[Error reading Word file {file.name}: {str(e)}]"

    # --- Excel (.xlsx) ---
    if ext == 'xlsx' or file.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        try:
            wb = load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
            text = ""
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                text += f"Sheet: {sheet_name}\n"
                for row in ws.iter_rows(values_only=True):
                    row_text = "\t".join([str(cell) if cell is not None else "" for cell in row])
                    text += row_text + "\n"
                text += "\n"
            wb.close()
            return f"--- Content of {file.name} (Excel) ---\n{text}\n--- End of file ---"
        except Exception as e:
            return f"[Error reading Excel file {file.name}: {str(e)}]"

    # --- Fallback for images and unsupported types ---
    if file.type.startswith("image/"):
        return f"[Image attached: {file.name}]"
    return f"[File attached: {file.name} (unsupported type)]"

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id.strip()
    user_message = req.message.strip()

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    # 1. Extract content from all files
    file_contents = []
    if req.files:
        for f in req.files:
            content = extract_file_content(f)
            if content:
                file_contents.append(content)

    # 2. Build effective message
    effective_message = user_message
    if file_contents:
        file_text_block = "\n\n".join(file_contents)
        effective_message = f"{user_message}\n\n[Attached file content]\n{file_text_block}"

    if not effective_message:
        raise HTTPException(status_code=400, detail="Empty message")

    # 3. Process with AI
    messages = load_messages(session_id)
    messages.append({"role": "user", "content": effective_message})
    messages = trim_history(messages)

    try:
        assistant_reply = call_groq(messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    messages.append({"role": "assistant", "content": assistant_reply})
    save_messages(session_id, messages)

    return ChatResponse(reply=assistant_reply)

@app.delete("/chat/{session_id}")
async def clear_history(session_id: str):
    supabase.table("conversations").delete().eq("session_id", session_id).execute()
    return {"message": "History cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)