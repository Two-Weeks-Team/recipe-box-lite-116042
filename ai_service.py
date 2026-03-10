import os
import json
import re
import httpx
from typing import List, Dict, Any

# -----------------------------------------------------------------------------
# Helper to pull out a JSON block from LLM markdown output
# -----------------------------------------------------------------------------

def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()

# -----------------------------------------------------------------------------
# Core inference call – used by all AI‑powered endpoints
# -----------------------------------------------------------------------------

async def _call_inference(messages: List[Dict[str, str]], max_tokens: int = 512) -> Dict[str, Any]:
    url = "https://inference.do-ai.run/v1/chat/completions"
    api_key = os.getenv("DIGITALOCEAN_INFERENCE_KEY")
    model = os.getenv("DO_INFERENCE_MODEL", "openai-gpt-oss-120b")
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": messages,
        "max_completion_tokens": max_tokens,
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            # Expect OpenAI‑compatible schema
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            raw_json = _extract_json(content)
            return json.loads(raw_json)
    except Exception as e:
        # Fallback – AI unavailable or malformed response
        return {"note": f"AI service unavailable: {str(e)}"}

# -----------------------------------------------------------------------------
# Public API used by route handlers
# -----------------------------------------------------------------------------

async def extract_ocr_text(image_base64: str) -> Dict[str, Any]:
    messages = [
        {
            "role": "system",
            "content": "You are an OCR extractor. Return a JSON object with keys 'extracted_text' (string) and 'confidence' (float between 0 and 1).",
        },
        {
            "role": "user",
            "content": f"Extract the text from the following base64‑encoded image: {image_base64}",
        },
    ]
    return await _call_inference(messages, max_tokens=512)

async def suggest_ingredients(recipe_id: str, dietary_restrictions: List[str]) -> Dict[str, Any]:
    restriction_text = ", ".join(dietary_restrictions) if dietary_restrictions else "none"
    messages = [
        {
            "role": "system",
            "content": "You are a culinary assistant. Suggest up to three ingredient substitutions for a recipe, respecting any dietary restrictions. Return a JSON list under the key 'suggestions', where each item has 'original', 'substitute', and 'reason'.",
        },
        {
            "role": "user",
            "content": f"Recipe ID: {recipe_id}\nDietary restrictions: {restriction_text}\nProvide the suggestions.",
        },
    ]
    return await _call_inference(messages, max_tokens=512)
