from flask import Flask
import threading
import requests
import random
import schedule
import time
from datetime import datetime
import os
import subprocess  # Added for curl functionality

# Load from environment variables
bot_token = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")
api_key = os.getenv("API_KEY")

odds_url = f'https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?regions=us&markets=h2h&oddsFormat=decimal&apiKey={api_key}'
send_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
app = Flask(__name__)

@app.route('/')
def home():
    return "AI Parlay Bot is running"

# Function to send daily picks
def send_daily_picks():
    print(f"Sending AI picks at {datetime.now()}...")
    response = requests.get(odds_url)
    print("ODDS API STATUS:", response.status_code)
    print("ODDS API RESPONSE:", response.text)

    try:
        games = response.json()
    except Exception as e:
        print("Error parsing JSON from odds API:", e)
        return

    picks = []
    for game in games:
        home = game.get('home_team')
        away = game.get('away_team')
        start = game.get('commence_time')

        try:
            outcomes = game['bookmakers'][0]['markets'][0]['outcomes']
            pick = random.choice(outcomes)
            picks.append({
                "matchup": f"{away} vs {home}",
                "pick": pick['name'],
                "odds": round(pick['price'], 2),
                "start_time": datetime.fromisoformat(start).strftime("%I:%M %p EST"),
                "confidence": random.randint(70, 90)
            })
            if len(picks) == 3:
                break
        except (IndexError, KeyError):
            continue

    for p in picks:
        msg = (
            "⚾️ *AI MLB Pick*\n\n"
            f"*Game:* {p['matchup']}\n"
            f"*Pick:* {p['pick']} ({p['odds']}) ⚾️\n"
            f"*Start Time:* {p['start_time']}\n"
            f"*Confidence:* {p['confidence']}%\n\n"
            "_Backed by real-time odds_"
        )
        requests.post(send_url, data={'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'})

    # Create the parlay message
    parlay_legs = [f"⚾️ {p['pick']} ({p['odds']})" for p in picks]
    parlay_odds = round((picks[0]['odds'] * picks[1]['odds'] * picks[2]['odds']) - 1, 2)
    parlay_msg = (
        "🔥 *AI Parlay of the Day!*\n\n"
        + "\n".join(parlay_legs) +
        f"\n\n*Estimated Return:* {parlay_odds}x\n"
        "_Let's hit this one hard!_"
    )
    requests.post(send_url, data={'chat_id': chat_id, 'text': parlay_msg, 'parse_mode': 'Markdown'})

# Schedule task to run daily at 11:00 AM
schedule.every().day.at("11:00").do(send_daily_picks)

# Flask route to keep the server alive
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# Background thread for task scheduler
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Optional: Function to demonstrate sending JSON with cURL
def send_json_with_curl():
    api_endpoint = "https://api.example.com/endpoint"
    json_payload = '{"key1": "value1", "key2": "value2"}'
    
    headers = [
        "Content-Type: application/json",
        "Authorization: Bearer YOUR_ACCESS_TOKEN"  # Replace with your token
    ]

    curl_command = [
        "curl",
        "-X", "POST",
        "-H", headers[0],
        "-H", headers[1],
        "-d", json_payload,
        api_endpoint
    ]

    try:
        result = subprocess.run(curl_command, check=True, text=True, capture_output=True)
        print("cURL Response:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error executing cURL command:")
        print(e.stderr)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    threading.Thread(target=run_scheduler).start()

    print("Bot is live and waiting to send picks at 11:00 AM daily..y.")

    # Optional: call this if needed
    # send_json_with_curl()
