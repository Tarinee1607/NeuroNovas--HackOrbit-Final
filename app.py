from flask import Flask, render_template, request, jsonify, redirect, session
from flask_session import Session
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import requests
import os

from translate import detect_lang, translate_english, translate_hindi
from memory import add_message, search_similar
from response_controller import classify_msg, adjust_sp
from transformers import pipeline

# Initialize app
app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Load environment variables
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")  # 👈 Make sure your .env has this

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client["emotion_app"]
users = db["users"]

# Mistral & Transformers Setup
url = "https://api.mistral.ai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json"
}

sentiment_model = pipeline("sentiment-analysis")
emotion_model = pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion")

# In-memory session score
session_scores = {}



@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html")

@app.route("/login")
def login():
    return render_template("auth.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not all(k in data for k in ("name", "email", "password", "emergencyContact")):
        return jsonify({"error": "Incomplete fields"}), 400
    if users.find_one({"email": data["email"]}):
        return jsonify({"error": "User already exists"}), 409
    users.insert_one(data)
    return jsonify({"success": True}), 201

@app.route("/signin", methods=["POST"])
def signin():
    data = request.get_json()
    user = users.find_one({"email": data["email"], "password": data["password"]})
    if user:
        session["user"] = {
            "name": user.get("name"),
            "email": user.get("email"),
            "emergencyContact": user.get("emergencyContact")
        }
        return jsonify(session["user"])
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/languageprocessing", methods=["POST"])
def process_language():
    try:
        data = request.get_json()
        user_msg = data.get("message")
        session_id = data.get("session_id") or "temp-session"
        email = data.get("email")

        # Fetch user details
        user = users.find_one({"email": email})
        emergency_contact = user.get("emergencyContact") if user else "Not Available"

        # Translate if not English
        o_lang = detect_lang(user_msg)
        t_msg = translate_english(user_msg) if o_lang != 'en' else user_msg

        # Classify and adjust system prompt
        context_type = classify_msg(t_msg)
        system_prompt = adjust_sp(context_type)

        # Context messages from memory
        related_msgs = search_similar(t_msg)
        context_msgs = []
        if context_type in ["emotional", "normal"]:
            for m in related_msgs:
                context_msgs.append({
                    "role": "user" if m["sender"] == "user" else "assistant",
                    "content": m["message"]
                })

        # Mistral payload
        conversation = [{"role": "system", "content": system_prompt}] + context_msgs + [{"role": "user", "content": t_msg}]
        temperature = 0.5 if context_type == "greeting" else (0.3 if context_type == "offensive" else 0.8)

        payload = {
            "model": "mistral-tiny",
            "temperature": temperature,
            "max_tokens": 400,
            "top_p": 0.9,
            "messages": conversation
        }

        # Get response from Mistral
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
        bot_reply = res.json()["choices"][0]["message"]["content"].strip()

        if o_lang != 'en':
            bot_reply = translate_hindi(bot_reply)

        # Save to memory
        add_message(session_id, "user", user_msg)
        add_message(session_id, "bot", bot_reply)

        # Mental Health Score Logic
        sentiment = sentiment_model(t_msg)[0]
        emotion = emotion_model(t_msg)[0]
        score = 100

        if sentiment['label'].lower() == 'negative':
            score -= 30
        if emotion['label'] in ['sadness', 'anger', 'fear']:
            score -= 30
        if emotion['label'] == 'disgust':
            score -= 40
        if 0 <= datetime.now().hour <= 5:
            score -= 10

        score = max(1, min(100, score))
        session_scores[session_id] = score

        suggestion = ""
        if score < 10:
            suggestion = f"⚠️ Please contact emergency support or call {emergency_contact}."
        elif score < 30:
            suggestion = "🧸 You might feel better by talking to someone close."

        return jsonify({
            "reply": bot_reply,
            "score": score,
            "suggestion": suggestion
        })

    except Exception as e:
        print("Error:", e)
        return jsonify({"reply": "Sorry, I couldn't process that.", "score": 0})

@app.route("/get_score", methods=["POST"])
def get_score():
    data = request.json
    session_id = data.get("session_id") or "temp-session"
    score = session_scores.get(session_id, 50)
    return jsonify({"score": score})

# ----------------- RUN APP ----------------- #
if __name__ == "__main__":
    app.run(debug=True)
