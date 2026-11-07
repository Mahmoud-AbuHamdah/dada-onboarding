SUGGESTIONS = {
    "Days 1-7": "Ask the assistant about the company, its values and onboarding "
                "(for example: ما قيم الشركة؟ or كيف أقدم طلب إجازة؟).",
    "Day 30": "Take the knowledge quiz below and complete one practice scenario.",
    "Day 60": "Practise your other scenarios and read the feedback.",
    "Day 90": "Open My progress and download your learning summary for a human review.",
}


def milestone_key(role, milestone):
    """Milestone names are the same for both roles, so include the role."""
    return f"{role}:{milestone}"


def get_activities(data, role, state):
    """List every activity for this role, and whether it is done."""
    items = []

    plan = data["plan"][data["plan"]["department"] == role]
    for _, r in plan.iterrows():
        items.append({
            "type": "Milestone",
            "name": r["milestone"],
            "done": milestone_key(role, r["milestone"]) in state["done_milestones"],
        })

    scenarios = data["scenarios"][data["scenarios"]["department"] == role]
    for _, r in scenarios.iterrows():
        items.append({
            "type": "Scenario",
            "name": f"{r['id']} · {r['company_value']}",
            "done": r["id"] in state["done_scenarios"],
        })

    items.append({
        "type": "Quiz",
        "name": "Knowledge quiz",
        "done": state["quiz_score"] is not None,
    })
    return items


def completion_percent(items):
    """Share of activities done, as a whole number from 0 to 100."""
    if not items:
        return 0
    return round(100 * sum(i["done"] for i in items) / len(items))