from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import sys
import requests
import json
import re

# Add backend directory to sys.path to import query_service
BASE_DIR = os.path.dirname(__file__)
sys.path.append(BASE_DIR)

# Gemini Config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

from query_service import get_thread_response

# Point templates to the ../frontend/templates directory
frontend_dir = os.path.abspath(os.path.join(BASE_DIR, "../frontend/templates"))
templates = Jinja2Templates(directory=frontend_dir)

app = FastAPI(title="Query Assistant")


def _get_gemini_instructions() -> str:
    return (
        "You are a helpful AI support assistant.\n\n"
        "You will be given:\n"
        "- A user's question\n"
        "- A possibly related past support answer (which may contain personal names, links, or escalation suggestions)\n\n"
        "Your job is to assess how well the past answer fits the new question.\n\n"
        "There are three possible situations:\n\n"
        "1. ✅ **Strong Match**: The past answer clearly addresses the user's current question.\n"
        "   - Rewrite it cleanly and professionally.\n"
        "   - Include helpful links if relevant.\n"
        "   - **Omit** personal names and escalation text (e.g. 'reach out 1:1').\n\n"
        "2. 🟡 **Somewhat Related**: The answer is not exact, but it might still be helpful.\n"
        "   - Say something like: \"This may not be exactly what you're looking for, but it might help.\"\n"
        "   - Include useful info, if any.\n\n"
        "3. ❌ **Irrelevant**: The past answer is unrelated.\n"
        "   - Respond as if you're the first person assisting.\n"
        "   - Politely ask for clarification if needed.\n\n"
        "Important:\n"
        "- Do NOT say things like 'based on past thread' or 'this is a rephrased answer'.\n"
        "- Just reply naturally.\n"
        "- If you're unsure, prefer being transparent and helpful.\n\n"
        "🔍 Also include a short explanation of your decision:\n"
        "- Why do you believe the past answer is a strong/partial/no match?\n"
        "- Which sentence or link from the past support answer was useful?\n"
        "- If nothing was useful, state that clearly.\n\n"
        "Finally, return your reply as valid JSON with this format:\n"
        "{\n"
        "  \"response\": \"...\",\n"
        "  \"confidence_score\": 0.73,\n"
        "  \"reasoning\": \"Explains why the answer was relevant or not, and what part of it was used.\"\n"
        "}\n\n"
        "The confidence_score must be:\n"
        "- Close to 1.0 for strong matches\n"
        "- Moderate (0.4–0.6) for partial relevance\n"
        "- Low (< 0.4) if the answer is mostly irrelevant"
    )


def _build_gemini_prompt(user_query: str, thread_answer: str, follow_ups: list[str] = []) -> dict:
    parts = [
        {"text": "You're an AI support assistant helping users with technical issues."},
        {"text": _get_gemini_instructions()},
        {"text": "---"},
        {"text": f"📝 User's Question:\n{user_query.strip()}"},
        {"text": f"📄 Possible Answer from past support:\n{thread_answer.strip()}"}
    ]

    if follow_ups:
        followup_text = "\n📚 Other Notes from the Thread:\n" + "\n".join(f"- {msg.strip()}" for msg in follow_ups)
        parts.append({"text": followup_text})

    parts.append({
        "text": "💬 Now write your final reply to the user. Include a confidence_score and reasoning as explained."
    })

    return {"contents": [{"parts": parts}]}


def _call_gemini(prompt_body):
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(GEMINI_URL, headers=headers, json=prompt_body)
        response.raise_for_status()
        content = response.json()["candidates"][0]["content"]["parts"]
        raw_text = content[0]["text"]
        print("\n📥 Raw Gemini text:\n", raw_text[:1000], "\n")
        return raw_text
    except Exception as e:
        print(f"\n❌ Gemini error: {e}")
        if 'response' in locals():
            print("📨 Gemini full response body:")
            print(response.text[:2000])
        return None


def _extract_json_from_markdown(text: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)


def _is_query_too_vague(query: str) -> bool:
    tokens = re.findall(r'\w+', query.lower())
    stopwords = {"the", "is", "in", "on", "of", "to", "a", "and", "what", "how", "why", "when", "need", "some", "information"}
    keywords = [word for word in tokens if word not in stopwords]
    return len(keywords) < 3


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "query": None,
        "result": None,
        "assistant_response": None,
        "confidence_score": None,
        "reasoning": None
    })


@app.post("/", response_class=HTMLResponse)
async def handle_query(request: Request, query: str = Form(...)):
    if _is_query_too_vague(query):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "query": query,
            "result": None,
            "assistant_response": (
                "Your question seems a bit unclear. Could you please provide more details so I can help better?"
            ),
            "confidence_score": 0.0,
            "reasoning": "The question was too vague and did not contain enough specific keywords."
        })

    result = get_thread_response(query)
    gemini_prompt = _build_gemini_prompt(query, result["answer"], result["follow_ups"])
    raw_response = _call_gemini(gemini_prompt)

    assistant_response = "I'm unable to provide a suitable response right now. Please check the matched response below."
    confidence_score = 0.0
    reasoning = ""

    if raw_response:
        try:
            cleaned = _extract_json_from_markdown(raw_response)
            print("🔍 Cleaned Gemini JSON attempt:\n", cleaned)
            parsed = json.loads(cleaned)
            assistant_response = parsed.get("response", assistant_response)
            confidence_score = parsed.get("confidence_score", 0.0)
            reasoning = parsed.get("reasoning", "")
        except json.JSONDecodeError as e:
            print("❌ Failed to parse Gemini JSON response")
            print("🔎 Raw response snippet:\n", raw_response[:500])
            print("⚠️ JSON decode error:", e)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "query": query,
        "result": result,
        "assistant_response": assistant_response,
        "confidence_score": confidence_score,
        "reasoning": reasoning,
        "faiss_score": result.get("faiss_score", 0.0)
    })


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
