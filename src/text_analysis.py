import spacy
from transformers import pipeline

nlp = spacy.load('en_core_web_sm')

sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english",
    revision="714eb0f"
)

def extract_person_name(text: str) -> str:
    """
    Dynamically extract a PERSON entity from the text.
    Returns the last detected PERSON entity.
    """
    doc = nlp(text)
    persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    return persons[-1] if persons else ""

def extract_location(text: str) -> str:
    """
    Dynamically extract a location (GPE or LOC) from the text.
    Returns the last detected location.
    """
    doc = nlp(text)
    locations = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]]
    return locations[-1] if locations else ""

def analyze_sentiment(text: str) -> str:
    """
    Analyze sentiment using a transformer-based pipeline.
    Returns one of 'positive', 'negative', or 'neutral' based on context.
    """
    try:
        result = sentiment_analyzer(text)
        if result:
            label = result[0]['label'].lower()
            return label
    except Exception:
        # Fallback in case of an error.
        pass
    return "neutral"
