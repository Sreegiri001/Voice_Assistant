import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
import requests
from urllib.parse import quote_plus

load_dotenv()
app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) if os.getenv("GEMINI_API_KEY") else None
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

@app.get("/")
def home(): return render_template("index.html")

@app.post("/api/chat")
def chat():
    data = request.get_json() or {}
    msg = (data.get("message") or "").strip()
    history = data.get("history", [])[-12:]
    if not msg: return jsonify(error="Message required"), 400
    if not client: return jsonify(error="Configure GEMINI_API_KEY in .env"), 500
    context = "\n".join(f'{x.get("role")}: {x.get("content")}' for x in history)
    prompt = f"""You are Nova, a friendly bilingual Tamil-English voice assistant.
Answer in the language used by the user, including natural Tanglish when appropriate.
Be concise and never claim actions you cannot perform.
Conversation:
{context}
User: {msg}
Assistant:"""
    try:
        result = client.models.generate_content(model=MODEL, contents=prompt)
        return jsonify(answer=result.text or "I could not answer that.")
    except Exception as e: return jsonify(error=str(e)), 502

@app.get("/api/weather")
def weather():
    city = request.args.get("city", "").strip()
    key = os.getenv("WEATHER_API_KEY")
    if not city or not key: return jsonify(error="City and WEATHER_API_KEY are required"), 400
    try:
        r = requests.get("https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": key, "units": "metric"}, timeout=10)
        r.raise_for_status(); d = r.json()
        return jsonify(city=d["name"], temperature=d["main"]["temp"],
                       description=d["weather"][0]["description"],
                       humidity=d["main"]["humidity"])
    except Exception as e: return jsonify(error=str(e)), 502

@app.get("/api/search")
def search():
    q = request.args.get("q", "").strip()
    return jsonify(url="https://www.google.com/search?q=" + quote_plus(q))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
