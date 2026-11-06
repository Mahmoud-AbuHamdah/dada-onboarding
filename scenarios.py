from qa import call_gemini

FEEDBACK_PROMPT = """You are a friendly onboarding coach at "Dada Group Academy". A new employee is practising a FICTIONAL workplace scenario.

You receive: the scenario, the company value it trains, a suggested good response, and the employee's response.

RULES:
1. Compare the employee's response with the suggested good response and the value.
2. Be encouraging and specific: say what they did well and give one or two concrete improvements.
3. Connect your feedback explicitly to the company value given.
4. Judge only the response. Do not invent company policies, product specifications, prices or contacts.
5. This is practice only, not a performance evaluation.
6. Reply in the same language as the employee's response (Arabic or English).
7. Score from 1 to 5: 5 = covers all key points of the suggested response; 3 = covers some; 1 = misses them, or does something harmful such as inventing information or hiding a problem.

Return JSON only:
{"score": 1, "strengths": "...", "improve": "...", "value_link": "one sentence linking the response to the value"}
"""


def value_info(kb, value_en):
    """Look up a company value in the knowledge base (K05-K09)."""
    row = kb[(kb["topic"] == "Values") & (kb["keyword_en"] == value_en)].iloc[0]
    name_ar = row["answer_ar"].split(" من القيم")[0]   # "النزاهة من القيم..." -> "النزاهة"
    return {"id": row["id"], "name_en": value_en, "name_ar": name_ar}


def evaluate_response(scenario, response_text, kb, client, model):
    """Give feedback on the employee's response to one scenario."""
    value = value_info(kb, scenario["company_value"])
    errors = []

    # 1. Try Gemini
    if client is not None:
        prompt = (
            f"SCENARIO: {scenario['scenario_ar']}\n"
            f"VALUE: {value['name_en']} ({value['name_ar']})\n"
            f"SUGGESTED GOOD RESPONSE: {scenario['suggested_good_response_ar']}\n"
            f"EMPLOYEE RESPONSE: {response_text}"
        )
        out, used_model, errors = call_gemini(client, FEEDBACK_PROMPT, prompt)
        if out is not None and "score" in out:
            out.update(mode="ai", model=used_model, errors=errors, value=value)
            return out
    else:
        errors = ["No API key found"]

    # 2. Fallback: compare meaning with the local AI model
    vecs = model.encode(
        ["query: " + response_text, "passage: " + scenario["suggested_good_response_ar"]],
        normalize_embeddings=True,
    )
    similarity = float(vecs[0] @ vecs[1])
    score = 4 if similarity >= 0.85 else 3 if similarity >= 0.80 else 2
    return {
        "score": score,
        "strengths": "",
        "improve": "Compare your response with the suggested response below.",
        "value_link": f"This scenario practises the value {value['name_en']} ({value['name_ar']}).",
        "mode": "fallback", "errors": errors, "value": value, "similarity": similarity,
    }