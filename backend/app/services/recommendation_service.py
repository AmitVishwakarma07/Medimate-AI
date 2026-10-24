"""Rule-based wellness recommendations. Pure Python (easy to test and explain in a viva).
Thresholds only decide which gentle suggestion to show; they are NOT medical judgements."""

CATALOG = {
    "sleep_schedule": "Build a consistent sleep schedule",
    "movement_breaks": "Consider taking regular movement breaks",
    "hydration_tracking": "Track hydration through the day",
    "balanced_diet": "Maintain a balanced diet",
    "stress_break": "Try a short daily relaxation break",
    "see_professional": "Discuss persistent or concerning symptoms with a professional",
}


def _avg(values):
    return round(sum(values) / len(values), 1) if values else None


def compute_stats(records):
    """records: recent HealthRecord-like objects (record_type, value)."""
    by = {}
    for r in records:
        by.setdefault(r.record_type, []).append(r.value)
    return {"sleep": _avg(by.get("sleep", [])), "water": _avg(by.get("water", [])),
            "activity": _avg(by.get("activity", []))}


def build(goals, activity_level, has_restrictions, stats, completed_keys):
    recs, needs = [], []

    def add(key, why, text):
        recs.append({"key": key, "title": CATALOG[key], "text": text, "why": why,
                     "completed": key in completed_keys})

    if "better_sleep" in goals or (stats["sleep"] is not None and stats["sleep"] < 7):
        why = ("You chose better sleep as a goal." if "better_sleep" in goals else
               f"Your recent logged sleep averages {stats['sleep']} hours.")
        add("sleep_schedule", why, "Try going to bed and waking up at similar times, and wind down screens "
            "30 minutes earlier. Small steps count.")
    elif "better_sleep" not in goals and stats["sleep"] is None:
        needs.append("Log a few nights of sleep or choose 'Better sleep' as a goal to get sleep suggestions.")

    if has_restrictions:
        if {"be_active", "balanced_diet"} & set(goals) or activity_level:
            recs.append({"key": "see_professional_restrictions", "title": "Check with a professional first",
                         "text": "You told us you have dietary or medical restrictions, so we are not suggesting "
                                 "specific diet or exercise changes. Please ask your doctor or dietitian what is right for you.",
                         "why": "You marked that you have dietary or medical restrictions.",
                         "completed": "see_professional_restrictions" in completed_keys})
    else:
        if "be_active" in goals or activity_level in ("sedentary", "light"):
            why = ("You chose being more active as a goal." if "be_active" in goals else
                   f"You described your activity level as {activity_level}.")
            add("movement_breaks", why, "Stand up and stretch or walk for a few minutes every hour or so. "
                "Start with what feels comfortable.")
        elif activity_level is None and "be_active" not in goals:
            needs.append("Tell us your activity level in Settings to get movement suggestions.")
        if "balanced_diet" in goals:
            add("balanced_diet", "You chose a balanced diet as a goal.",
                "Add one extra vegetable or fruit serving to a meal you already eat.")

    if "hydration" in goals or (stats["water"] is not None and stats["water"] < 1.5):
        why = ("You chose hydration as a goal." if "hydration" in goals else
               f"Your recent logged water intake averages {stats['water']} L per day.")
        add("hydration_tracking", why, "Keep a bottle nearby and log your water once or twice a day.")
    elif stats["water"] is None and "hydration" not in goals:
        needs.append("Log your daily water intake or choose 'Hydration' as a goal for hydration suggestions.")

    if "manage_stress" in goals:
        add("stress_break", "You chose managing stress as a goal.",
            "Take 5 minutes for slow breathing, a short walk, or a call with someone you trust.")

    # Always-on safety suggestion
    add("see_professional", "General safety reminder for everyone.",
        "If a symptom is persistent, worsening, or worrying you, please talk to a qualified healthcare professional.")

    if len(recs) == 1:  # only the safety reminder => not enough info, ask instead of guessing
        needs.insert(0, "We don't have enough information yet. Pick at least one goal in Settings or log some records.")
    return {"recommendations": recs, "needs_more_info": needs,
            "note": "Suggestions are general wellness ideas, not medical advice, and cannot promise any health outcome."}
