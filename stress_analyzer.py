# stress_analyzer.py
from transformers import pipeline
from datetime import datetime

# Load models
sentiment_pipeline = pipeline("sentiment-analysis")
emotion_pipeline = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)

session_scores = {}  # in-memory

def compute_stress_score(text, pause_variation):
    score = 50

    # Sentiment-based
    sentiment = sentiment_pipeline(text)[0]
    score += 20 if sentiment['label'] == 'POSITIVE' else -30 * sentiment['score']

    # Emotion-based
    emotion_weights = {
        "anger": -15,
        "sadness": -20,
        "fear": -25,
        "joy": +10,
        "love": +5
    }
    emotions = emotion_pipeline(text)[0]
    for emo in emotions:
        if emo['label'].lower() in emotion_weights:
            score += emotion_weights[emo['label'].lower()] * emo['score']

    # Pause variation effect
    if pause_variation > 500:
        score -= 10
    elif pause_variation > 1000:
        score -= 20

    # Time-based factor
    hour = datetime.now().hour
    if hour >= 22 or hour <= 5:
        score -= 5  # night time stress

    return max(1, min(100, int(score)))

def track_and_feedback(session_id, text, pause_variation):
    score = compute_stress_score(text, pause_variation)
    session_scores[session_id] = score

    if score < 10:
        return score, "⚠️ Please contact an emergency helpline or someone you trust immediately."
    elif score < 30:
        return score, "💡 Try spending time with a friend or family member. Connection helps."
    return score, ""
