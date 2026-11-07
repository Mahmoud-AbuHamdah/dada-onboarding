import re

import numpy as np

from retrieval import normalize_ar

# Arabic-Indic digits (٠-٩) -> normal digits (0-9)
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# Words are written already normalized (no hamza on alef, ة -> ه)
DONE_WORDS = ["اكملت", "انهيت", "انتهيت", "خلصت", "انجزت",
              "completed", "finished", "done"]
SCENARIO_WORDS = ["عميل", "زبون", "موقف", "سيناريو",
                  "customer", "client", "scenario", "practice", "practise"]

MILESTONES = [
    ("Days 1-7", r"1\s*-\s*7|الاسبوع الاول|اول اسبوع|first week|week 1"),
    ("Day 30", r"\b30\b|ثلاثين"),
    ("Day 60", r"\b60\b|ستين"),
    ("Day 90", r"\b90\b|تسعين"),
]


def clean(message):
    """Normalize the message the same way as the knowledge base."""
    return normalize_ar(message).translate(ARABIC_DIGITS)


def detect_intent(message):
    """Decide what kind of message this is: progress, scenario or question."""
    text = clean(message)

    if any(w in text for w in DONE_WORDS):
        for name, pattern in MILESTONES:
            if re.search(pattern, text):
                return {"intent": "progress", "milestone": name}
        return {"intent": "progress", "milestone": None}   # which one? ask

    if any(w in text for w in SCENARIO_WORDS):
        return {"intent": "scenario"}

    return {"intent": "question"}


def mentioned_role(message):
    """Return the role named in the message, if any."""
    text = clean(message)
    if "مبيعات" in text or "sales" in text:
        return "Sales"
    if "توصيل" in text or "تسليم" in text or "delivery" in text:
        return "Delivery"
    return None


def pick_scenario(message, scenarios, model):
    """Choose the scenario whose situation is closest in meaning to the message."""
    texts = ("passage: " + scenarios["scenario_ar"]).tolist()
    vecs = model.encode(texts, normalize_embeddings=True)
    q = model.encode(["query: " + message], normalize_embeddings=True)[0]
    best = int(np.argmax(vecs @ q))
    return scenarios.iloc[best]