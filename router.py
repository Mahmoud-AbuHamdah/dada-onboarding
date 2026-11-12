import re

import numpy as np

from retrieval import normalize_ar

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

DONE_WORDS = ["اكملت", "انهيت", "انتهيت", "خلصت", "انجزت",
              "completed", "finished", "done"]
SCENARIO_WORDS = ["عميل", "زبون", "موقف", "سيناريو",
                  "customer", "client", "scenario", "practice", "practise"]

MILESTONES = [
    ("Days 1-7", r"\b1\s*-?\s*7\b|الاسبوع الاول|اول اسبوع|first week|week 1"),
    ("Day 30", r"\b30\b|ثلاثين"),
    ("Day 60", r"\b60\b|ستين"),
    ("Day 90", r"\b90\b|تسعين"),
]


# Words that usually start a question: formal Arabic, Jordanian dialect and English
QUESTION_STARTS = {normalize_ar(w) for w in [
    "هل", "ما", "ماذا", "متى", "كيف", "من", "أين", "كم", "لماذا",
    "شو", "وين", "قديش", "مين", "ليش", "إيمتى",
    "what", "who", "when", "where", "why", "how", "which",
    "can", "could", "do", "does", "is", "are", "should",
]}


def clean(message):
    """Normalize the message the same way as the knowledge base."""
    return normalize_ar(message).translate(ARABIC_DIGITS)


def looks_like_question(message):
    """True if the message ends with a question mark or starts with a question word."""
    if message.strip().endswith(("?", "؟")):
        return True
    words = clean(message).split()
    return bool(words) and words[0] in QUESTION_STARTS


def detect_intent(message):
    """Decide what kind of message this is: progress, scenario or question."""
    text = clean(message)
    has_done = any(w in text for w in DONE_WORDS)
    has_scenario = any(w in text for w in SCENARIO_WORDS)

    # A message phrased as a question is answered as a question first.
    # If it also mentions a customer situation, a scenario can follow
    # when the knowledge base has no answer.
    if looks_like_question(message) and (has_done or has_scenario):
        return {"intent": "question", "scenario_if_unanswered": has_scenario}

    if has_done:
        for name, pattern in MILESTONES:
            if re.search(pattern, text):
                return {"intent": "progress", "milestone": name}
        return {"intent": "progress", "milestone": None}   # which one? ask

    if has_scenario:
        return {"intent": "scenario"}

    return {"intent": "question"}


def mentioned_role(message):
    text = clean(message)
    if "مبيعات" in text or "sales" in text:
        return "Sales"
    if "توصيل" in text or "تسليم" in text or "delivery" in text:
        return "Delivery"
    return None


def pick_scenario(message, scenarios, model):
    texts = ("passage: " + scenarios["scenario_ar"]).tolist()
    vecs = model.encode(texts, normalize_embeddings=True)
    q = model.encode(["query: " + message], normalize_embeddings=True)[0]
    best = int(np.argmax(vecs @ q))
    return scenarios.iloc[best]
