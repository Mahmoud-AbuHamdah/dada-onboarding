import json
import os
import re
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
    "لا تتوفر لدي هذه المعلومة في المصادر المتاحة.\n\n"
    "I don't have this information in my sources."
)
ARABIC = re.compile(r"[\u0600-\u06FF]")


def answer_language(text):
    """Arabic if the text contains Arabic letters, otherwise English."""
    return "Arabic" if ARABIC.search(text) else "English"

SYSTEM_PROMPT = """You are the learning assistant of "Dada Group Academy", helping new employees during their first 90 days.

RULES:
1. Answer ONLY with information stated in the FACTS. Add nothing else: no phone numbers, emails, names, numbers, dates or policies that are not in the FACTS.
2. If the FACTS fully answer the question, set status to "answered".
3. If the question asks for a specific detail (a number, a name, a date, a contact) that the FACTS do not give, but the FACTS contain closely related useful information, set status to "partial": give the related information, then clearly say that the specific detail is not in your sources. Example: asked "How many annual leave days do I get?" with a fact about how to request leave, explain how to request leave and say the number of days is not available.
4. If the FACTS do not answer the question, set status to "refused" and say politely that this information is not in your sources. Suggest checking with HR only if the question is about work at Dada Group (for example policies, pay, contacts or procedures); for unrelated questions (for example the weather), just say it is outside what you can help with. Never guess.
5. Put the IDs of the facts you actually used in used_ids. Use only IDs that appear in the FACTS.
6. Write the answer in the ANSWER LANGUAGE given, even though the FACTS are in Arabic. Translate the facts faithfully if needed.
7. You do not make employment decisions and you do not replace HR procedures. If a fact applies only to certain roles, say so, and never assume it applies to this employee.
8. Keep every condition, exception or role limitation that a fact states (for example who a rule applies to, or when something happens). When the answer comes from one fact, include all of that fact, not only the first part.
9. Keep the answer short: 1 to 3 sentences, or a short list.

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


def fallback(facts, error=None, value_ids=()):
    """Used when the AI can't be reached: show only very confident facts."""
    # A values question: the search already gathered all five value facts
    values = [f for f in facts if f["id"] in value_ids]
    if value_ids and facts[0]["id"] in value_ids and len(values) == len(value_ids):
        return {"status": "answered", "answer": "\n".join(f["text"] for f in values),
                "used_ids": [f["id"] for f in values],
                "facts": facts, "mode": "fallback", "error": error}

    best = facts[0]
    if best["score"] >= FALLBACK_MIN:
        return {"status": "answered", "answer": best["text"], "used_ids": [best["id"]],
                "facts": facts, "mode": "fallback", "error": error}
    return {"status": "refused", "answer": REFUSAL, "used_ids": [],
            "facts": facts, "mode": "fallback", "error": error}

# =====================================================================
# qa.py - Step 13 changes
#
# In your qa.py, find the line that starts with:   def call_gemini(
# Delete from that line down to the END of the file, then paste
# everything below this box in its place.
#
# Do NOT touch anything above def call_gemini( : your SYSTEM_PROMPT,
# get_client, gather_facts and fallback stay exactly as they are.
# =====================================================================


def call_gemini(client, system_prompt, prompt):
    """Send one prompt, trying each model in order.
    Returns (result, model_used, errors). result is None if every model failed."""
    errors = []
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            result = json.loads(response.text)
            if not isinstance(result, dict):       # a list or plain text is unusable
                raise ValueError("reply was not a JSON object")
            return result, model, errors
        except Exception as e:
            errors.append(f"{model}: {e}")
    return None, None, errors


# ---------- Contact guard ----------
EASTERN_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
PHONE_LIKE = re.compile(r"\+?\d[\d\s\-()]{5,}\d")          # a run of digits, spaces and dashes
EMAIL_OR_LINK = re.compile(r"\S+@\S+|https?://\S+|www\.\S+", re.IGNORECASE)


def invented_contact(answer, facts, question=""):
    """True if the answer contains a phone number, email or link that
    appears in none of the facts (and was not typed by the user)."""
    answer = str(answer).translate(EASTERN_DIGITS)
    known = (" ".join(f["text"] for f in facts) + " " + question).translate(EASTERN_DIGITS)
    known_digits = re.sub(r"\D", "", known)

    for match in PHONE_LIKE.finditer(answer):
        digits = re.sub(r"\D", "", match.group())
        if len(digits) >= 7 and digits not in known_digits:   # 7+ digits = phone-like
            return True
    for match in EMAIL_OR_LINK.finditer(answer):
        if match.group().lower() not in known.lower():
            return True
    return False


# =====================================================================
# qa.py - Step 13b changes (this replaces the earlier Step 13 paste)
#
# In your qa.py, find the line that starts with:   def call_gemini(
# Delete from that line down to the END of the file, then paste
# everything below this box in its place.
#
# Do NOT touch anything above that line: your SYSTEM_PROMPT,
# get_client, gather_facts and fallback stay exactly as they are.
# =====================================================================


def call_gemini(client, system_prompt, prompt):
    """Send one prompt, trying each model in order.
    Returns (result, model_used, errors). result is None if every model failed."""
    errors = []
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            result = json.loads(response.text)
            if not isinstance(result, dict):       # a list or plain text is unusable
                raise ValueError("reply was not a JSON object")
            return result, model, errors
        except Exception as e:
            errors.append(f"{model}: {e}")
    return None, None, errors


# ---------- Contact guard ----------
EASTERN_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
PHONE_LIKE = re.compile(r"\+?\d[\d\s\-()]{5,}\d")          # a run of digits, spaces and dashes
EMAIL_OR_LINK = re.compile(r"\S+@\S+|https?://\S+|www\.\S+", re.IGNORECASE)


def invented_contact(answer, facts, question=""):
    """True if the answer contains a phone number, email or link that
    appears in none of the facts (and was not typed by the user)."""
    answer = str(answer).translate(EASTERN_DIGITS)
    known = (" ".join(f["text"] for f in facts) + " " + question).translate(EASTERN_DIGITS)
    known_digits = re.sub(r"\D", "", known)

    for match in PHONE_LIKE.finditer(answer):
        digits = re.sub(r"\D", "", match.group())
        if len(digits) >= 7 and digits not in known_digits:   # 7+ digits = phone-like
            return True
    for match in EMAIL_OR_LINK.finditer(answer):
        if match.group().lower() not in known.lower():
            return True
    return False


# ---------- Dialect ----------
# Common Jordanian words and their standard Arabic form. The knowledge base is
# written in standard Arabic, so the search works better on the standard wording.
DIALECT = {
    "شو": "ما", "ايش": "ما", "إيش": "ما",
    "قديش": "كم", "أديش": "كم", "اديش": "كم",
    "وين": "أين", "مين": "من", "ليش": "لماذا",
    "ايمتى": "متى", "إيمتى": "متى", "امتى": "متى", "متا": "متى",
    "بقدر": "هل يمكنني أن", "بدي": "أريد أن", "لازم": "يجب أن",
    "باخد": "آخذ", "بتوصلني": "تصلني", "بتوصل": "تصل",
    "تبعت": "لدى", "تبع": "لدى", "هاد": "هذا", "هاي": "هذه", "مش": "ليس",
    "الجداد": "الجدد", "صاحبي": "صديقي", "الزبون": "العميل", "معصب": "غاضب",
}
DIALECT_RE = re.compile(r"(?<!\w)(" + "|".join(map(re.escape, DIALECT)) + r")(?!\w)")


def to_standard(question):
    """Replace dialect words with standard Arabic ones. Other text is unchanged."""
    text = DIALECT_RE.sub(lambda m: DIALECT[m.group()], question)
    return re.sub(r"\s+", " ", text).strip()


def answer_question(question, role, retriever, kb, client):
    """The full pipeline: find facts, ask the AI, check its reply."""
    standard = to_standard(question)                 # same as the question if no dialect words
    facts = gather_facts(standard, retriever, kb)
    value_ids = set(kb.loc[kb["topic"] == "Values", "id"])

    # 1. Completely unrelated question: refuse without calling the AI
    if facts[0]["score"] < FLOOR:
        return {"status": "refused", "answer": REFUSAL, "used_ids": [],
                "facts": facts, "mode": "rule"}

    # 2. No API key: use the fallback
    if client is None:
        return fallback(facts, error="No API key found", value_ids=value_ids)

    # 3. Ask the AI: try each model in order until one works
    facts_text = "\n".join(f"[{f['id']}] {f['text']}" for f in facts)
    prompt = (f"Employee training track: {role}\n\nFACTS:\n{facts_text}\n\n"
              f"ANSWER LANGUAGE: {answer_language(question)}\n\nQUESTION:\n{question}")
    if standard != question:
        prompt += f"\n\nTHE SAME QUESTION IN STANDARD ARABIC:\n{standard}"
    out, model, errors = call_gemini(client, SYSTEM_PROMPT, prompt)
    if out is None or not str(out.get("answer", "")).strip():   # failed, or no answer text
        errors = errors or ["reply had no answer text"]
        return fallback(facts, error=" | ".join(errors), value_ids=value_ids)
    out["model"] = model
    out["answer"] = str(out["answer"])
    if out.get("status") not in ("answered", "partial", "refused"):
        out["status"] = "answered"

    # 4. Check the AI's reply: keep only IDs we actually gave it
    allowed = {f["id"] for f in facts}
    cited = out.get("used_ids")
    out["used_ids"] = [i for i in cited if i in allowed] if isinstance(cited, list) else []

    # An answer with no valid source is not trusted
    if out["status"] != "refused" and not out["used_ids"]:
        out["status"], out["answer"] = "refused", REFUSAL

    # A phone number, email or link that is not in the facts is never shown
    if invented_contact(out["answer"], facts, question):
        out["status"], out["answer"], out["used_ids"] = "refused", REFUSAL, []
        out["guard"] = "contact"

    if out["status"] == "refused":                   # a refusal shows no source badges
        out["used_ids"] = []

    out["facts"] = facts
    out["mode"] = "ai"
    out["errors"] = errors
    return out
