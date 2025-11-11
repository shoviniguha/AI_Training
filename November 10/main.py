# backend/main.py
import os
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend_tools")

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://api.openrouter.ai/api/v1/chat/completions"

# If you need to run behind a proxy, set HTTPS_PROXY/HTTP_PROXY env vars
proxies = None
proxy_env = os.getenv("HTTP_PROXY") or os.getenv("http_proxy") or os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
if proxy_env:
    logger.info("Proxy detected via env; httpx will use environment proxy settings.")

# create httpx client (uses env proxies automatically)
client = httpx.AsyncClient(timeout=60.0)

app = FastAPI(title="Tools + OpenRouter LLM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Request / Response models
# -------------------------
class ToolRequest(BaseModel):
    tool: str = Field(..., description="Tool name: math, reverse, date, llm")
    # math specifics
    op: Optional[str] = Field(None, description="for math: add, sub, mul, div")
    a: Optional[float] = None
    b: Optional[float] = None
    # string reverse
    text: Optional[str] = None
    # llm / general query
    query: Optional[str] = None
    model: Optional[str] = None  # openrouter model id (optional)
    history: Optional[list[dict]] = None

class ToolResponse(BaseModel):
    status: str
    tool: str
    result: str

# -------------------------
# Local tool implementations
# -------------------------
def do_math(op: str, a: float, b: float) -> str:
    op = op.lower()
    if op == "add":
        return str(a + b)
    if op == "sub" or op == "subtract":
        return str(a - b)
    if op == "mul" or op == "multiply":
        return str(a * b)
    if op == "div" or op == "divide":
        if b == 0:
            raise ValueError("Division by zero")
        return str(a / b)
    raise ValueError(f"Unknown math op '{op}'")

def do_reverse(s: str) -> str:
    return s[::-1]

def do_date() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

# -------------------------
# Helper: call OpenRouter
# -------------------------
async def call_openrouter(prompt: str, model: str | None = None, history: list[dict] | None = None) -> str:
    # Mock mode: quick local dev fallback
    if os.getenv("NO_NETWORK") == "1":
        logger.info("NO_NETWORK=1 set -> returning mock LLM response")
        return "(mock) OpenRouter offline — this is a canned reply."

    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not configured")

    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model or "mistralai/mistral-small-3",
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.2,
    }

    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    try:
        resp = await client.post(OPENROUTER_URL, json=payload, headers=headers)
    except httpx.RequestError as ex:
        logger.exception("OpenRouter request failed")
        raise HTTPException(status_code=502, detail=f"Upstream request error: {ex}") from ex

    if resp.status_code != 200:
        logger.error("OpenRouter responded with non-200: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    data = resp.json()
    try:
        answer = data["choices"][0]["message"]["content"]
    except Exception:
        logger.error("Unexpected OpenRouter response: %s", data)
        raise HTTPException(status_code=502, detail="Unexpected upstream response shape")
    return answer

# -------------------------
# Main endpoint: dispatch
# -------------------------
@app.post("/call_tool", response_model=ToolResponse)
async def call_tool(req: ToolRequest):
    tool = req.tool.lower().strip()
    logger.info("call_tool request: %s", tool)

    try:
        if tool == "math" or tool == "calculator":
            if req.op is None or req.a is None or req.b is None:
                raise HTTPException(status_code=400, detail="math requires 'op', 'a' and 'b'")
            res = do_math(req.op, req.a, req.b)
            return ToolResponse(status="ok", tool="math", result=res)

        if tool == "reverse" or tool == "reverse_string":
            if req.text is None:
                raise HTTPException(status_code=400, detail="reverse requires 'text'")
            res = do_reverse(req.text)
            return ToolResponse(status="ok", tool="reverse", result=res)

        if tool == "date" or tool == "today":
            res = do_date()
            return ToolResponse(status="ok", tool="date", result=res)

        if tool == "llm" or tool == "openrouter":
            if not req.query:
                raise HTTPException(status_code=400, detail="llm requires 'query'")
            answer = await call_openrouter(req.query, model=req.model, history=req.history)
            return ToolResponse(status="ok", tool="llm", result=answer)

        raise HTTPException(status_code=400, detail=f"Unknown tool '{req.tool}'")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as ex:
        logger.exception("Internal error in tool execution")
        raise HTTPException(status_code=500, detail=str(ex))

@app.get("/health")
def health():
    return {"status": "ok"}
