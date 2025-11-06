import os
import requests

# Optional: override via env, else use Llama-3.1-70B
DEFAULT_MODEL = "mistralai/mistral-7b-instruct:free"

def build_prompt(context: str, question: str) -> str:
    return f"""You are a careful policy assistant. Answer using ONLY the excerpts below.
- Quote exact terms when needed.
- Always cite page numbers like (p. 7).
- If the answer is not present, say: "Not specified in this policy excerpt."
- Add: "This is informational, not legal advice."

Question: {question}

Policy excerpts:
{context}

Answer:"""

def generate_answer(prompt: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY missing. Add it to your environment or .env file."
        )

    # Using requests directly so we can set timeouts and show readable errors
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=40)  # hard timeout
        r.raise_for_status()
        data = r.json()
        # defensive parsing
        choice = (data.get("choices") or [{}])[0]
        msg = (choice.get("message") or {}).get("content", "")
        if not msg:
            raise RuntimeError(f"Empty response from model: {data}")
        return msg.strip()

    except requests.Timeout:
        raise RuntimeError("OpenRouter request timed out (40s). Check network or try a smaller model.")

    except requests.HTTPError as e:
        # Surface OpenRouter error body if present
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise RuntimeError(f"OpenRouter HTTP {r.status_code}: {detail}") from e

    except Exception as e:
        raise RuntimeError(f"OpenRouter call failed: {e}")
