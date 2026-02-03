import os
import json
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv

# φορτώνει το .env από το app/ (ίδιο directory με db.py)
env_path = Path(__file__).resolve().parents[1] / ".env"  # .../app/.env
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing. Check app/.env")

def _extract_json(text: str) -> dict:
    # πιάνει JSON ακόμα κι αν το Gemini το βάλει μέσα σε ```json ... ```
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON object found in Gemini response text")
    return json.loads(m.group(0))

def generate_questions_json(prompt: str) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=60) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    text = data["candidates"][0]["content"]["parts"][0].get("text", "")
    return _extract_json(text)
