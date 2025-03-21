# text_analysis.py
import spacy

nlp = spacy.load("en_core_web_sm")

# ------------------------
# Text Analysis Functions
# ------------------------
def extract_person_name(text: str) -> str:
    """Extract a PERSON entity from the text (if any)."""
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return ""

def extract_location(text: str) -> str:
    """Extract a location entity (GPE or LOC) from the text (if any)."""
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:
            return ent.text
    return ""

def analyze_sentiment(text: str) -> str:
    """
    A simple rule-based sentiment analysis.
    For a more robust solution, consider a dedicated sentiment library.
    """
    positive_words = ["happy", "joy", "excited", "great", "good", "love"]
    negative_words = ["sad", "angry", "bad", "depressed", "upset", "hate"]
    pos_count = sum(text.lower().count(word) for word in positive_words)
    neg_count = sum(text.lower().count(word) for word in negative_words)
    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    else:
        return "neutral"