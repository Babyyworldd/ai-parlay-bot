import os
import time
import threading
import subprocess  # for the cURL helper
from datetime import datetime

import requests
import random
import schedule
from flask import Flask

# Load from environment variables
bot_token = os.getenv("BOT_TOKEN")
chat_id   = os.getenv("CHAT_ID")
api_key   = os.getenv("API_KEY")

odds_url = (
    f'https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/'
    f'?regions=us&markets=h2h&oddsFormat=decimal&apiKey={api_key}'
)
send_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

app = Flask(__name__)

@app.route('/')
def home():
    return "AI Parlay Bot is running"
    
@app.route('/test')
def test_send():
    send_daily_picks()
    return "Test picks sent!"
    
def send_daily_picks():
    """Fetch odds, pick 3 games at random, and send both single picks and a parlay."""
    now = datetime.now()
    print(f"[{now.isoformat()}] Sending AI picks…")

    response = requests.get(odds_url)
    print("ODDS API STATUS:", response.status_code)
    print("ODDS API RESPONSE:", response.text)

    try:
        games = response.json()
    except Exception as e:
        print("❌ Error parsing JSON from odds API:", e)
        return

    picks = []
    for game in games:
        try:
            home     = game["home_team"]
            away     = game["away_team"]
            start    = game["commence_time"]
            outcomes = game["bookmakers"][0]["markets"][0]["outcomes"]
            pick     = random.choice(outcomes)

            picks.append({
                "matchup":    f"{away} vs {home}",
                "pick":       pick["name"],
                "odds":       round(pick["price"], 2),
                "start_time": datetime.fromisoformat(start).strftime("%I:%M %p EST"),
                "confidence": random.randint(70, 90)
            })

            if len(picks) == 3:
                break

        except (IndexError, KeyError) as e:
            # skip games that don't have the expected structure
            continue

    # Send each individual pick
    for p in picks:
        msg = (
            "⚾️ *AI MLB Pick*\n\n"
            f"*Game:* {p['matchup']}\n"
            f"*Pick:* {p['pick']} ({p['odds']}) ⚾️\n"
            f"*Start Time:* {p['start_time']}\n"
            f"*Confidence:* {p['confidence']}%\n\n"
            "_Backed by real-time odds_"
        )
        requests.post(send_url, data={
            'chat_id':    chat_id,
            'text':       msg,
            'parse_mode': 'Markdown'
        })

    # Send the parlay
    if len(picks) == 3:
        parlay_legs = [f"⚾️ {p['pick']} ({p['odds']})" for p in picks]
        parlay_odds = round((picks[0]['odds'] * picks[1]['odds'] * picks[2]['odds']) - 1, 2)
        parlay_msg = (
            "🔥 *AI Parlay of the Day!*\n\n"
            + "\n".join(parlay_legs) +
            f"\n\n*Estimated Return:* {parlay_odds}x\n"
            "_Let's hit this one hard!_"
        )
        requests.post(send_url, data={
            'chat_id':    chat_id,
            'text':       parlay_msg,
            'parse_mode': 'Markdown'
        })

# Schedule task to run daily at 11:00 AM
schedule.every().day.at("11:00").do(send_daily_picks)

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def send_json_with_curl():
    """Optional helper: send a JSON payload via cURL."""
    api_endpoint = "https://api.example.com/endpoint"
    json_payload = '{"key1": "value1", "key2": "value2"}'

    headers = [
        "Content-Type: application/json",
        "Authorization: Bearer YOUR_ACCESS_TOKEN"  # ← replace me
    ]

    curl_cmd = [
        "curl", "-X", "POST",
        "-H", headers[0],
        "-H", headers[1],
        "-d", json_payload,
        api_endpoint
    ]

    try:
        result = subprocess.run(curl_cmd, check=True, text=True, capture_output=True)
        print("cURL Response:\n", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error executing cURL command:\n", e.stderr)

if __name__ == '__main__':
    # Start the Flask server and scheduler in parallel threads
    threading.Thread(target=run_flask,    daemon=True).start()
    threading.Thread(target=run_scheduler, daemon=True).start()

schedule.every().day.at("15:00").do(send_daily_picks)

    # If you ever want to fire off the cURL demo on startup, uncomment:
    # send_json_with_curl()
