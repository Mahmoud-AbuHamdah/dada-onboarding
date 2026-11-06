import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # reads GEMINI_API_KEY from the .env file

MODELS = ["gemini-3.1-flash-lite", "gemini-3.8-flash"]  # fast model first
TIMEOUT_MS = 30000  # 30 seconds per model
FLOOR = 0.75          # below this: refuse without calling the AI
FALLBACK_MIN = 0.84   # if the AI is unavailable, only show a fact this confident
TOP_K = 5             # how many facts to give the AI

REFUSAL = (
    "لا تتوفر لدي هذه المعلومة في المصادر المتاحة. يُرجى التأكد من قسم الموارد البشرية.\n\n"
    "I don't have this information in my sources. Please check with HR."
)

SYSTEM_PROMPT = """You are the learning assistant of "Dada Group Academy", helping new employees during their first 90 days.

RULES:
1. Answer ONLY with information stated in the FACTS. Add nothing else: no phone numbers, emails, names, numbers, dates or policies that are not in the FACTS.
2. If the FACTS fully answer the question, set status to "answered".
3. If the question asks for a specific detail (a number, a name, a date, a contact) that the FACTS do not give, but the FACTS contain closely related useful information, set status to "partial": give the related information, then clearly say that the specific detail is not in your sources. Example: asked "How many annual leave days do I get?" with a fact about how to request leave, explain how to request leave and say the number of days is not available.
4. If the FACTS do not answer the question, set status to "refused" and say politely that this information is not in your sources and the employee should check with HR. Never guess.
5. Put the IDs of the facts you actually used in used_ids. Use only IDs that appear in the FACTS.
6. Reply in the same language as the QUESTION (Arabic or English).
7. You do not make employment decisions and you do not replace HR procedures. If a fact applies only to certain roles, say so, and never assume it applies to this employee.
8. Keep the answer short: 1 to 3 sentences, or a short list.

Return JSON only, in this format:
{"status": "answered" or "partial" or "refused", "answer": "...", "used_ids": ["K01"]}
"""


def get_client():
    """Create the Gemini client, or return None if there is no API key."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    return genai.Client(
        api_key=key,
        http_options=types.HttpOptions(timeout=TIMEOUT_MS),
    )

def gather_facts(question, retriever, kb):
    """Find the facts most related to the question."""
    all_results = retriever.search(question, top_k=len(kb))  # every fact, ranked
    facts = all_results[:TOP_K]

    # If the question is about values, give the AI all five value facts,
    # because the answer is spread over five rows (K05-K09).
    value_ids = set(kb.loc[kb["topic"] == "Values", "id"])
    if any(f["id"] in value_ids for f in facts[:2]):
        facts += [r for r in all_results if r["id"] in value_ids and r not in facts]
    return facts


def fallback(facts, error=None):
    """Used when the AI can't be reached: show only a very confident fact."""
    best = facts[0]
    if best["score"] >= FALLBACK_MIN:
        return {"status": "answered", "answer": best["text"], "used_ids": [best["id"]],
                "facts": facts, "mode": "fallback", "error": error}
    return {"status": "refused", "answer": REFUSAL, "used_ids": [],
            "facts": facts, "mode": "fallback", "error": error}


def answer_question(question, role, retriever, kb, client):
    """The full pipeline: find facts, ask the AI, check its reply."""
    facts = gather_facts(question, retriever, kb)

    # 1. Completely unrelated question: refuse without calling the AI
    if facts[0]["score"] < FLOOR:
        return {"status": "refused", "answer": REFUSAL, "used_ids": [],
                "facts": facts, "mode": "rule"}

    # 2. No API key: use the fallback
    if client is None:
        return fallback(facts, error="No API key found")

        # 3. Ask the AI: try each model in order until one works
    facts_text = "\n".join(f"[{f['id']}] {f['text']}" for f in facts)
    prompt = f"Employee training track: {role}\n\nFACTS:\n{facts_text}\n\nQUESTION:\n{question}"

    out = None
    errors = []
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            out = json.loads(response.text)
            out["model"] = model
            break                      # success: stop trying other models
        except Exception as e:         # overloaded, timeout, rate limit, bad JSON...
            errors.append(f"{model}: {e}")

    if out is None:                    # every model failed
        return fallback(facts, error=" | ".join(errors))

    # 4. Check the AI's reply: keep only IDs we actually gave it
    allowed = {f["id"] for f in facts}
    out["used_ids"] = [i for i in out.get("used_ids", []) if i in allowed]

    # An answer with no valid source is not trusted
    if out.get("status") != "refused" and not out["used_ids"]:
        out["status"], out["answer"] = "refused", REFUSAL

    out["facts"] = facts
    out["mode"] = "ai"
    out["errors"] = errors      # failures of earlier models, if any
    return out