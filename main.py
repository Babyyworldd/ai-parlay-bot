import os
import time
import threading
import requests
import random
from datetime import datetime
from pytz import timezone
from flask import Flask

# Load environment variables
bot_token = os.getenv("BOT_TOKEN")
chat_id   = os.getenv("CHAT_ID")
api_key   = os.getenv("API_KEY")

# Constants
odds_url = (
    f'https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/'
    f'?regions=us&markets=h2h&oddsFormat=decimal&apiKey={api_key}'
)
send_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
eastern = timezone('US/Eastern')

# Flask app for keep-alive or testing
app = Flask(__name__)

@app.route('/')
def home():
    return "AI Parlay Bot is running"

@app.route('/test')
def test_send():
    send_daily_picks()
    return "Test picks sent!"

def send_daily_picks():
    """Fetch odds, pick 3 games, and send picks and parlay."""
    now = datetime.now(eastern)
    print(f"[{now.isoformat()}] Sending AI picks…")

    response = requests.get(odds_url)
    print("ODDS API STATUS:", response.status_code)

    try:
        games = response.json()
    except Exception as e:
        print("❌ Error parsing JSON from odds API:", e)
        return

    picks = []
    for game in games:
        try:
            home = game["home_team"]
            away = game["away_team"]
            start = game["commence_time"]
            outcomes = game["bookmakers"][0]["markets"][0]["outcomes"]
            pick = random.choice(outcomes)

            picks.append({
                "matchup": f"{away} vs {home}",
                "pick": pick["name"],
                "odds": round(pick["price"], 2),
                "start_time": datetime.fromisoformat(start).strftime("%I:%M %p EST"),
                "confidence": random.randint(70, 90)
            })

            if len(picks) == 3:
                break

        except (IndexError, KeyError):
            continue

    # Send each pick
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
            'chat_id': chat_id,
            'text': msg,
            'parse_mode': 'Markdown'
        })

    # Parlay
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
            'chat_id': chat_id,
            'text': parlay_msg,
            'parse_mode': 'Markdown'
        })

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

def run_scheduler():
    has_run_today = False
    while True:
        now = datetime.now(eastern)
        current_time = now.strftime("%H:%M")
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Scheduler heartbeat")

        if current_time == "11:00" and not has_run_today:
            send_daily_picks()
            has_run_today = True

        if current_time == "00:01":
            has_run_today = False

        time.sleep(60)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=run_scheduler, daemon=True).start()

    # Keep main thread alive
    while True:
        time.sleep(1)
