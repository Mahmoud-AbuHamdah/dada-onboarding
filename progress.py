"""Progress calculation. Only numbers here: the pages decide how to show them."""

MILESTONE_AR = {
    "Days 1-7": "الأيام من 1 إلى 7",
    "Day 30": "اليوم 30",
    "Day 60": "اليوم 60",
    "Day 90": "اليوم 90",
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
            "type": "milestone",
            "milestone": r["milestone"],
            "done": milestone_key(role, r["milestone"]) in state["done_milestones"],
        })

    scenarios = data["scenarios"][data["scenarios"]["department"] == role]
    for _, r in scenarios.iterrows():
        items.append({
            "type": "scenario",
            "sid": r["id"],
            "value": r["company_value"],
            "done": r["id"] in state["done_scenarios"],
        })

    items.append({"type": "quiz", "done": role in state["quiz_score"]})
    return items


def completion_percent(items):
    """Share of activities done, as a whole number from 0 to 100."""
    if not items:
        return 0
    return round(100 * sum(i["done"] for i in items) / len(items))
