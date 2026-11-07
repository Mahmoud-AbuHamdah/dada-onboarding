"""Run all test cases and save a results file.

Usage:  python run_tests.py
"""
import csv
import os
import re
import time
from datetime import datetime

from data_loader import load_all
from qa import answer_question, get_client
from retrieval import SemanticRetriever, load_model
from router import detect_intent, mentioned_role, pick_scenario
from scenarios import evaluate_response

PAUSE = 4      # seconds between AI calls, to stay under the free-tier rate limit
ROLE = "Sales" # track used for question tests

# ---------- Question tests: (id, question, expected behaviour, expected IDs) ----------
JURY_QA = [
    ("T01", "متى تأسست مجموعة الدادا؟", "answer", ["K01"]),
    ("T02", "ما قيم الشركة الخمس؟", "answer", ["K05", "K06", "K07", "K08", "K09"]),
    ("T03", "كيف أقدم طلب إجازة؟", "answer", ["K16"]),
    ("T04", "كم فترة التجربة؟", "answer", ["K14"]),
    ("T05", "ما رقم هاتف مدير الموارد البشرية؟", "refuse", []),
    ("T09", "هل يمكن أن تشارك معلومات سرية مع صديق؟", "answer", ["K17"]),
]

EXTRA_QA = [
    ("X01", "ما هي رسالة الشركة؟", "answer", ["K04"]),
    ("X02", "هل أحتاج أن أسجل حضوري؟", "answer", ["K15"]),
    ("X03", "ماذا يتم تجهيزه قبل أن أبدأ العمل؟", "answer", ["K11"]),
    ("X04", "What is the company's vision?", "answer", ["K03"]),
    ("X05", "How do I request leave?", "answer", ["K16"]),
    ("X06", "كم يوم إجازة سنوية لي؟", "partial", ["K16"]),
    ("X07", "كم راتبي؟", "refuse", []),
    ("X08", "ما الطقس اليوم؟", "refuse", []),
    ("X09", "من هو المدير العام؟", "refuse", []),
    ("X10", "أين أركن سيارتي؟", "refuse", []),
]

# ---------- Intent tests: (id, message, expected intent, expected scenario/milestone) ----------
INTENT_TESTS = [
    ("T06", "أنا موظف مبيعات وعميل يسأل عن ميزة غير مؤكدة", "scenario", "S02"),
    ("T07", "أنا موظف توصيل والعميل غاضب بسبب التأخير", "scenario", "S04"),
    ("T08", "أكملت نشاط اليوم 30", "progress", "Day 30"),
    ("I01", "أكملت الأيام 1-7", "progress", "Days 1-7"),
    ("I02", "أكملت المرحلة", "progress", None),
    ("I03", "كيف أقدم طلب إجازة؟", "question", None),
    # Known limitations, kept on purpose so the results are honest:
    ("I04", "هل يمكنني مشاركة ملفات مع عميل؟", "question", None),
    ("I05", "Who do I contact when I'm done with onboarding?", "question", None),
]

# ---------- Feedback tests: (id, scenario, response, min score, max score) ----------
FEEDBACK_TESTS = [
    ("FB1", "S02", "لا أعرف إذا كانت هذه الميزة موجودة، سأتحقق من المواصفات أو أسأل المسؤول ثم أرد على العميل.", 4, 5),
    ("FB2", "S02", "أقول له نعم، المنتج فيه هذه الميزة حتى يشتري.", 1, 2),
    ("FB3", "S04", "I apologise, explain the confirmed new delivery time, and escalate to my supervisor if needed.", 4, 5),
]

CONTACT = re.compile(r"\d{6,}|@|\+\d")   # phone numbers, emails


def judge_question(expect, ids, out):
    used, status = set(out["used_ids"]), out["status"]
    if expect == "refuse":
        return "PASS" if status == "refused" and not CONTACT.search(out["answer"]) else "FAIL"
    if expect == "partial":
        if status == "partial" and set(ids) <= used:
            return "PASS"
        return "SAFE" if status == "refused" else "FAIL"
    return "PASS" if status == "answered" and set(ids) <= used else "FAIL"


def main():
    print("Loading data and model...")
    data = load_all()
    model = load_model()
    retriever = SemanticRetriever(data["kb"], model)
    client = get_client()
    if client is None:
        print("WARNING: no API key found, results will use fallback mode.")
    rows = []

    # FAQ tests come straight from the CSV
    faq_qa = []
    for _, r in data["faq"].iterrows():
        ids = [i for i in str(r["expected_knowledge_ids"]).split(";") if i.startswith("K")]
        faq_qa.append((r["id"], r["employee_question_ar"], "answer" if ids else "refuse", ids))

    # 1. Question tests
    qa_tests = JURY_QA + faq_qa + EXTRA_QA
    for n, (tid, q, expect, ids) in enumerate(qa_tests, 1):
        print(f"[{n}/{len(qa_tests)}] {tid}: {q}")
        out = answer_question(q, ROLE, retriever, data["kb"], client)
        rows.append({
            "test_id": tid, "type": "question", "input": q,
            "expected": f"{expect} {' '.join(ids)}".strip(),
            "got": f"{out['status']} {' '.join(out['used_ids'])}".strip(),
            "response": out["answer"],
            "model": out.get("model") or out["mode"],
            "result": judge_question(expect, ids, out),
        })
        time.sleep(PAUSE)

    # 2. Intent tests (no AI call except choosing the scenario, which is local)
    for tid, msg, expect, target in INTENT_TESTS:
        intent = detect_intent(msg)
        got, detail = intent["intent"], ""
        if got == "scenario":
            sc_role = mentioned_role(msg) or ROLE
            options = data["scenarios"][data["scenarios"]["department"] == sc_role]
            detail = pick_scenario(msg, options, model)["id"]
        elif got == "progress":
            detail = intent["milestone"] or ""
        ok = got == expect and (target is None or detail == target)
        rows.append({
            "test_id": tid, "type": "intent", "input": msg,
            "expected": f"{expect} {target or ''}".strip(),
            "got": f"{got} {detail}".strip(),
            "response": "", "model": "rules", "result": "PASS" if ok else "FAIL",
        })

    # 3. Feedback tests
    for tid, sid, resp, lo, hi in FEEDBACK_TESTS:
        print(f"Feedback {tid} on {sid}")
        sc = data["scenarios"][data["scenarios"]["id"] == sid].iloc[0]
        fb = evaluate_response(sc, resp, data["kb"], client, model)
        score = int(fb.get("score", 0))
        rows.append({
            "test_id": tid, "type": "feedback", "input": resp,
            "expected": f"score {lo}-{hi}, value {sc['company_value']}",
            "got": f"score {score}, value {fb['value']['name_en']}",
            "response": f"{fb.get('strengths', '')} | {fb.get('improve', '')}",
            "model": fb.get("model") or fb["mode"],
            "result": "PASS" if lo <= score <= hi else "FAIL",
        })
        time.sleep(PAUSE)

    # Save the results file
    os.makedirs("results", exist_ok=True)
    path = f"results/test_results_{datetime.now():%Y%m%d_%H%M}.csv"
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    counts = {}
    for r in rows:
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    print("\n===== SUMMARY =====")
    print(f"Total tests: {len(rows)}")
    for result, n in sorted(counts.items()):
        print(f"  {result}: {n}")
    for r in rows:
        if r["result"] != "PASS":
            print(f"  {r['result']}  {r['test_id']}: expected [{r['expected']}], got [{r['got']}]")
    print(f"\nSaved: {path}")


if __name__ == "__main__":
    main()