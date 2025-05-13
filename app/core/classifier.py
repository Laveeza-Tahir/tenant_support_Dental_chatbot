from difflib import SequenceMatcher
import logging
import re

def is_similar(a: str, b: str, threshold: float = 0.8) -> bool:
    """
    Checks if two strings are similar above a threshold using SequenceMatcher.
    """
    return SequenceMatcher(None, a, b).ratio() > threshold

def detect_intent(text: str) -> str:
    """
    Detects the intent of a given text using fuzzy matching.
    """
    t = text.lower().strip()
    
    logging.info(f"Detecting intent for text: '{t}'")
    
    # HANDLE SIMPLE LOCATION REQUESTS FIRST
    # If the message starts with "location" or contains only "location" with optional pleasantries
    if t.startswith("location") or re.match(r"^.*?\blocation\b.*?(?:plz|pls|please)?$", t):
        logging.info(f"Simple location request detected: '{t}'")
        return "contact_info"

    # Define a set of keywords for each intent
    handoff_keywords = ["live", "human", "whatsapp", "agent", "humman", "talk to human", "connect to human"]
    appointment_keywords = ["book", "appointment", "schedule", "visit", "dentist", "checkup"]
    faq_keywords = ["faq", "what is", "how", "why", "?"]
    # intake_keywords = ["name", "age", "history", "intake", "patient info"]
    contact_keywords = ["contact", "address", "hours", "timing", "location", "reach us", 
                        "where", "office", "clinic", "directions", "find", "map"]

    # First, check for exact phrase matches for location queries
    location_phrases = ["where is", "location of", "office location", "clinic location", 
                        "address of", "directions to", "how to find", "where are you"]
    
    for phrase in location_phrases:
        if phrase in t:
            logging.info(f"Found location phrase '{phrase}' in '{t}'")
            return "contact_info"
    
    # If "location" and "clinic/office/dental" are in the same query, it's likely about location
    if "location" in t and any(word in t for word in ["clinic", "office", "dental"]):
        logging.info(f"Found location context in '{t}'")
        return "contact_info"
    
    # Check for individual words "location", "address", "where" with high priority
    # Changed from t.split() to just checking if word is in t
    if any(word in t for word in ["location", "address", "where", "office", "directions"]):
        logging.info(f"Found direct location word in '{t}'")
        return "contact_info"

    # Check for intent match using fuzzy matching for "handoff" and other intents
    if any(is_similar(word, kw) for word in t.split() for kw in handoff_keywords):
        return "handoff"

    if any(is_similar(word, kw) for word in t.split() for kw in appointment_keywords):
        return "appointment"
    
    if any(is_similar(word, kw) for word in t.split() for kw in contact_keywords):
        logging.info(f"Found fuzzy match for contact_info in '{t}'")
        return "contact_info"
    
    if any(is_similar(word, kw) for word in t.split() for kw in faq_keywords):
        return "faqs"
    
    # Default to "faqs" if no matches found
    logging.info(f"No intent match found for '{t}', defaulting to faqs")
    return "faqs"

