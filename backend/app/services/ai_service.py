"""Chatbot brain.
1. Emergency check (always first, always rule-based).
2. Medicine/dosage guard (never gives prescriptions or doses).
3. Optional external LLM - ONLY if an API key is configured AND the user
   gave consent in Settings. Only the typed question is sent, never health records.
4. Otherwise a rule-based keyword fallback (this is NOT an LLM and says so)."""
import json
import urllib.request

from .. import config

DISCLAIMER = ("General educational information only - not medical advice, diagnosis or treatment. "
              "I am not a doctor. Please talk to a qualified healthcare professional about your own situation.")

EMERGENCY_WORDS = [
    "chest pain", "can't breathe", "cannot breathe", "trouble breathing", "difficulty breathing",
    "shortness of breath", "unconscious", "fainted", "seizure", "stroke", "face drooping",
    "slurred speech", "severe bleeding", "suicid", "kill myself", "overdose", "worst headache",
    "coughing blood", "vomiting blood", "heart attack",
]
EMERGENCY_REPLY = (
    "Some of what you describe could be an emergency. Please contact your local emergency "
    "services (for example 112 in India, 911 in the US, 999 in the UK) or go to the nearest "
    "emergency department right away. If you are thinking about harming yourself, reach out to "
    "local emergency services or a crisis helpline now. Please do not wait for an online answer, "
    "and if possible ask someone nearby to stay with you."
)
MEDICINE_WORDS = ["dose", "dosage", "how many mg", " mg", "prescribe", "prescription", "tablet", "antibiotic",
                  "stop taking", "which medicine", "what medicine", "painkiller"]
MEDICINE_REPLY = (
    "I can't recommend specific medicines, doses, or changes to prescribed treatment - that needs "
    "someone who knows your health history. Please ask a doctor or pharmacist. Never stop or change "
    "a prescribed medicine without their advice. I'm happy to share general lifestyle information instead."
)

# (keywords, answer). First match wins.
RULES = [
    (["when should i seek", "when to seek", "see a doctor", "seek medical", "should i worry", "when to see"],
     "General signs that deserve professional assessment include: symptoms that are severe, sudden, getting "
     "worse, or lasting longer than expected; symptoms that interfere with daily life; or anything that feels "
     "'not right' to you. Seek urgent care for chest pain, trouble breathing, sudden weakness or numbness, "
     "confusion, slurred speech, or severe bleeding. When unsure, contacting a doctor or a local health "
     "helpline is always reasonable."),
    (["headache", "head ache", "migraine"],
     "Common, usually non-serious contributors to headaches include tension and stress, not enough sleep, "
     "dehydration, skipped meals, long screen time or eye strain, and changes in caffeine intake. Migraines "
     "are a separate condition that a doctor can assess. Gentle habits like regular sleep, drinking water, "
     "and screen breaks help some people. See a professional if headaches are frequent, unusually severe, or "
     "follow a head injury; seek emergency help for a sudden 'worst ever' headache or one with fever and stiff "
     "neck, confusion, weakness, or vision/speech changes."),
    (["blood pressure", "systolic", "diastolic", "bp "],
     "Blood pressure is the force of blood pushing against artery walls. It is written as two numbers in mmHg: "
     "systolic (when the heart beats) over diastolic (between beats). One reading can vary with stress, "
     "activity, caffeine, and time of day, so trends measured consistently matter more than a single number. "
     "What a reading means for you depends on your health context, so please discuss your readings with a "
     "clinician."),
    (["heart rate", "pulse", "bpm"],
     "Heart rate is how many times your heart beats per minute (bpm). It naturally changes with activity, "
     "emotions, caffeine, sleep, and fitness. Measuring at similar times (for example, resting in the morning) "
     "makes trends easier to compare. If you notice palpitations, dizziness, or fainting, speak to a healthcare "
     "professional."),
    (["fever", "high temperature", "temperature is high"],
     "A fever is a temporary rise in body temperature, often a sign that the body is fighting an infection. "
     "General comfort measures many people use: rest, drink plenty of fluids, and wear light clothing. "
     "Please contact a doctor if the fever is very high, lasts more than a couple of days, keeps coming back, "
     "or if the person is a baby, an older adult, pregnant, or has a long-term health condition. Seek emergency "
     "help for a fever with confusion, a stiff neck, trouble breathing, a seizure, or a spreading rash. I can't "
     "recommend medicines or doses - a doctor or pharmacist can advise on that."),
    (["cough", "cold ", "sore throat", "runny nose", "flu "],
     "Coughs and colds are very common and usually settle on their own. Rest, fluids, and warm drinks help many "
     "people feel more comfortable. See a healthcare professional if symptoms last more than a couple of weeks, "
     "keep getting worse, or come with a high fever, chest pain, or breathing difficulty (get urgent help for the "
     "last two). Ask a pharmacist or doctor before taking any medicine."),
    (["nausea", "vomit", "diarrh", "stomach ache", "stomach pain", "upset stomach"],
     "For an upset stomach, many people rest and take small, frequent sips of water to stay hydrated. Please see a "
     "healthcare professional if it lasts more than a day or two, or if there is blood, severe pain, signs of "
     "dehydration (very dry mouth, dizziness, very little urine), or if it affects a child, an older adult, or "
     "someone with a health condition."),
    (["sleep", "insomnia", "tired", "rest well"],
     "Habits many people find helpful for sleep: keep a consistent bed and wake time, get daylight in the "
     "morning, limit caffeine later in the day, keep screens dim or off before bed, and keep the bedroom cool, "
     "dark, and quiet. If poor sleep lasts for weeks or affects your daytime life, a healthcare professional "
     "can help look into it."),
    (["water", "hydrat", "thirst", "drink enough"],
     "Healthy hydration habits: keep a water bottle visible, sip regularly instead of waiting for thirst, drink "
     "a glass with meals, and add flavour with lemon or mint if plain water is boring. Needs vary with weather, "
     "activity, and health conditions, so ask a professional if you have a condition that affects fluids."),
    (["stress", "anxiety", "anxious", "relax", "overwhelm"],
     "Many people find short breaks, slow breathing, light exercise, time outdoors, and talking with someone "
     "they trust helpful for everyday stress. If stress or low mood is persistent or affecting daily life, "
     "please reach out to a mental-health professional."),
    (["exercise", "workout", "active", "movement", "walk"],
     "Regular movement, even short walks or stretch breaks, is linked with better wellbeing. Start small and "
     "build gradually. If you have a health condition, are returning after a long break, or feel unwell during "
     "activity, check with a healthcare professional first."),
    (["diet", "food", "eat ", "nutrition", "meal"],
     "A balanced eating pattern generally includes vegetables, fruit, whole grains, protein sources, and "
     "limited highly processed foods. Individual needs differ a lot (allergies, conditions, age), so a "
     "registered dietitian or doctor can give personal guidance."),
]
SYMPTOM_WORDS = ["feeling", "symptom", " pain", "ache", " sick", " ill ", "unwell", "dizzy", "rash", "swelling", "weak "]
SYMPTOM_REPLY = (
    "I'm sorry you're not feeling well. I can't tell what is causing symptoms or diagnose anything, but general "
    "steps many people take are resting, staying hydrated, and noting when symptoms started and how they change. "
    "Please talk to a doctor or a local health service if symptoms are severe, getting worse, last more than a few "
    "days, or worry you. If you have chest pain, trouble breathing, sudden weakness or confusion, or severe "
    "bleeding, contact your local emergency services immediately."
)
DEFAULT_REPLY = (
    "I'm a simple rule-based helper, so I only know a few general topics: headaches, sleep, hydration, blood "
    "pressure, heart rate, fever, coughs and colds, stomach upsets, stress, exercise, diet, and when to seek medical help. Try rephrasing with one of "
    "those topics, or ask a healthcare professional for anything specific to you."
)


def _contains(text, words):
    return any(w in text for w in words)


def rule_based_reply(message: str) -> dict:
    text = f" {message.lower()} "
    if _contains(text, EMERGENCY_WORDS):
        return {"reply": EMERGENCY_REPLY, "source": "rule_based", "emergency": True}
    if _contains(text, MEDICINE_WORDS):
        return {"reply": MEDICINE_REPLY, "source": "rule_based", "emergency": False}
    for keywords, answer in RULES:
        if _contains(text, keywords):
            return {"reply": answer, "source": "rule_based", "emergency": False}
    if _contains(text, SYMPTOM_WORDS):
        return {"reply": SYMPTOM_REPLY, "source": "rule_based", "emergency": False}
    return {"reply": DEFAULT_REPLY, "source": "rule_based", "emergency": False}


SYSTEM_PROMPT = (
    "You are a general health-education assistant in a college demo app. Give short, plain-language, general "
    "information only. You are not a doctor. Do not diagnose, do not recommend prescription medicines or "
    "doses, and never advise stopping prescribed treatment. Do not invent studies or references. For possibly "
    "serious symptoms advise professional assessment; for emergencies tell the user to contact local "
    "emergency services immediately."
)


def llm_configured() -> bool:
    return bool(config.LLM_API_KEY and config.LLM_MODEL)


def llm_reply(message: str):
    """Call any OpenAI-compatible /chat/completions API. Returns text or None on any failure."""
    body = json.dumps({
        "model": config.LLM_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message}],
        "max_tokens": 500,
    }).encode("utf-8")
    req = urllib.request.Request(
        config.LLM_BASE_URL.rstrip("/") + "/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {config.LLM_API_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"].strip()
    except Exception:
        return None  # caller falls back to the rule-based answer


def answer(message: str, user_consented: bool) -> dict:
    base = rule_based_reply(message)
    # Emergency and medicine questions are always handled locally, never delegated.
    if base["emergency"] or base["reply"] in (MEDICINE_REPLY,):
        return {**base, "disclaimer": DISCLAIMER}
    if llm_configured() and user_consented:
        text = llm_reply(message)
        if text:
            return {"reply": text, "source": "llm", "emergency": False, "disclaimer": DISCLAIMER}
    return {**base, "disclaimer": DISCLAIMER}
