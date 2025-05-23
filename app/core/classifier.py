from difflib import SequenceMatcher

def is_similar(a: str, b: str, threshold: float = 0.8) -> bool:
    """
    Checks if two strings are similar above a threshold using SequenceMatcher.
    """
    return SequenceMatcher(None, a, b).ratio() > threshold

def detect_intent(text: str) -> str:
    """
    Detects the intent of a given text using fuzzy matching.
    """
    t = text.lower()

    # Define a set of keywords for each intent
    handoff_keywords = ["live", "human", "whatsapp", "agent", "humman", "talk to human", "connect to human"]
    appointment_keywords = ["book", "appointment", "schedule", "visit", "dentist", "checkup"]
    faq_keywords = ["faq", "what is", "how", "why", "?", "tell me about", "explain", "information", "details", "guide", "help"]
    # intake_keywords = ["name", "age", "history", "intake", "patient info"]
    contact_keywords = ["contact", "address", "hours", "timing", "location", "reach us"]

    # Check for intent match using fuzzy matching for "handoff" and other intents
    if any(is_similar(word, kw) for word in t.split() for kw in handoff_keywords):
        return "handoff"

    if any(is_similar(word, kw) for word in t.split() for kw in appointment_keywords):
        return "appointment"
    
    if any(is_similar(word, kw) for word in t.split() for kw in faq_keywords):
        return "faqs"
    
    # if any(is_similar(word, kw) for word in t.split() for kw in intake_keywords):
    #     return "intake"
    
    if any(is_similar(word, kw) for word in t.split() for kw in contact_keywords):
        return "contact_info"

    # Default to "faqs" if no matches found
    return "faqs"
