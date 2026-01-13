from flask import Flask, render_template, request, jsonify
import os, uuid, random, threading, time, re, urllib.parse
from gtts import gTTS
from dotenv import load_dotenv
from openai import OpenAI
from pytube import Search

# ================= LOAD ENV =================
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
VOICE_DIR = "static/voice"
os.makedirs(VOICE_DIR, exist_ok=True)

# ================= WEBSITE RULES =================
NEW_TAB_ONLY = {
    "open google": "https://www.google.com",
    "open amazon": "https://www.amazon.in",
    "open bank": "https://www.onlinesbi.sbi",
    "open sbi": "https://www.onlinesbi.sbi",
    "open hdfc": "https://www.hdfcbank.com",
    "open youtube": "https://www.youtube.com"   # YouTube homepage
}

IFRAME_ONLY = {
    "open tesla": "https://www.tesla.com",
    "open share market": "https://www.tradingview.com",
    "open market": "https://www.tradingview.com",
    "open tradingview": "https://www.tradingview.com",
    "open wikipedia": "https://en.wikipedia.org",
    "open github": "https://github.com"
}

REMINDERS = []
ALARMS = []

# ================= VOICE =================
def make_voice(text):
    filename = f"{uuid.uuid4()}.mp3"
    path = os.path.join(VOICE_DIR, filename)
    gTTS(text=text, lang="en").save(path)
    return f"/static/voice/{filename}"

# ================= REMINDER / ALARM =================
def reminder_task(seconds, text):
    time.sleep(seconds)
    REMINDERS.append({
        "text": f"🔔 REMINDER: {text}",
        "voice": make_voice(f"Reminder: {text}")
    })

def alarm_task(seconds, text):
    time.sleep(seconds)
    ALARMS.append({
        "text": f"⏰ ALARM: {text}",
        "voice": make_voice(f"Alarm alert. Time to {text}")
    })

# ================= AI RESPONSE =================
def get_ai_response(msg):
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Elon Musk. Be concise and confident."},
                {"role": "user", "content": msg}
            ],
            temperature=0.6
        )
        return "ELON: " + res.choices[0].message.content.strip()
    except:
        return "ELON: AI offline. Please try again."

# ================= ROUTES =================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message", "").lower().strip()
    reply = ""
    iframe = ""
    new_tab = ""

    # ---------- WEBSITE ----------
    if msg in NEW_TAB_ONLY:
        reply = f"Opening {msg.replace('open','').title()}"
        new_tab = NEW_TAB_ONLY[msg]

    elif msg in IFRAME_ONLY:
        reply = f"Opening {msg.replace('open','').title()}"
        iframe = IFRAME_ONLY[msg]

    # ---------- SONG (DIRECT PLAY FIRST VIDEO IN NEW TAB) ----------
    elif msg.startswith("play "):
        song = msg.replace("play ", "")
        try:
            search = Search(song)
            first_video = search.results[0].watch_url
            new_tab = first_video + "&autoplay=1"
            reply = f"Playing {song.title()}"
            iframe = ""
        except:
            q = urllib.parse.quote(song)
            new_tab = f"https://www.youtube.com/results?search_query={q}"
            reply = f"Playing {song.title()} (search page)"
            iframe = ""

    # ---------- RANDOM SONG ----------
    elif msg == "play random song":
        song = random.choice(["kesariya","rocket man"])
        try:
            search = Search(song)
            first_video = search.results[0].watch_url
            new_tab = first_video + "&autoplay=1"
            reply = f"Playing {song.title()}"
            iframe = ""
        except:
            q = urllib.parse.quote(song)
            new_tab = f"https://www.youtube.com/results?search_query={q}"
            reply = f"Playing {song.title()} (search page)"
            iframe = ""

    # ---------- REMINDER ----------
    elif msg.startswith("remind me"):
        try:
            match = re.search(r"remind me in (\d+)\s*(second|seconds|minute|minutes)\s*to (.+)", msg)
            amount, unit, text = int(match.group(1)), match.group(2), match.group(3)
            seconds = amount * 60 if "minute" in unit else amount
            threading.Thread(target=reminder_task, args=(seconds, text), daemon=True).start()
            reply = f"Reminder set for {text}"
        except:
            reply = "Format error. Example: remind me in 1 minute to drink water"

    # ---------- ALARM ----------
    elif msg.startswith("alarm"):
        try:
            match = re.search(r"alarm in (\d+)\s*(second|seconds|minute|minutes)\s*(.+)", msg)
            amount, unit, text = int(match.group(1)), match.group(2), match.group(3)
            seconds = amount * 60 if "minute" in unit else amount
            threading.Thread(target=alarm_task, args=(seconds, text), daemon=True).start()
            reply = f"Alarm set for {text}"
        except:
            reply = "Format error. Example: alarm in 1 minute wake up"

    # ---------- AI ----------
    else:
        reply = get_ai_response(msg)

    return jsonify({
        "reply": reply,
        "iframe": iframe,
        "new_tab": new_tab,
        "voice": make_voice(reply)
    })

@app.route("/reminders")
def reminders():
    if REMINDERS:
        return jsonify(REMINDERS.pop(0))
    return jsonify({})

@app.route("/alarms")
def alarms():
    if ALARMS:
        return jsonify(ALARMS.pop(0))
    return jsonify({})

if __name__ == "__main__":
    print("🚀 COMMANDER ELON RUNNING")
    app.run(debug=True)
