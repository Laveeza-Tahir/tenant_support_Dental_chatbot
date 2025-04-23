from difflib import SequenceMatcher

def is_similar(a: str, b: str, threshold: float = 0.8) -> bool:
    return SequenceMatcher(None, a, b).ratio() > threshold

def detect_intent(text: str) -> str:
    t = text.lower()

    handoff_keywords = ["live", "human", "whatsapp", "agent", "humman", "talk to human", "connect to human"]
    if any(is_similar(word, kw) for word in t.split() for kw in handoff_keywords):
        return "handoff"

    if any(w in t for w in ["book", "appointment", "schedule"]):
        return "appointment"
    if any(w in t for w in ["faq", "what is", "how", "why", "?"]):
        return "faqs"
    if any(w in t for w in ["name", "age", "history", "intake"]):
        return "intake"
    if any(w in t for w in ["contact", "address", "hours", "timing"]):
        return "contact_info"

    return "faqs"
