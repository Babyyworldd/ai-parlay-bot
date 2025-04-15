import requests
import random
import schedule
import time
from datetime import datetime
import os

# Load from environment variables
bot_token = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")
api_key = os.getenv("API_KEY")

odds_url = f'https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?regions=us&markets=h2h&oddsFormat=decimal&apiKey={api_key}'
send_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

def send_daily_picks():
    print(f"Sending AI picks at {datetime.now()}...")
    response = requests.get(odds_url)
    games = response.json()

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

    parlay_legs = [f"⚾️ {p['pick']} ({p['odds']})" for p in picks]
    parlay_odds = round((picks[0]['odds'] * picks[1]['odds'] * picks[2]['odds']) - 1, 2)
    parlay_msg = (
        "🔥 *AI Parlay of the Day!*\n\n"
        + "\n".join(parlay_legs) +
        f"\n\n*Estimated Return:* {parlay_odds}x\n"
        "_Let's hit this one hard!_"
    )
    requests.post(send_url, data={'chat_id': chat_id, 'text': parlay_msg, 'parse_mode': 'Markdown'})

schedule.every().day.at("11:00").do(send_daily_picks)
print("Bot is live and waiting to send picks at 11:00 AM daily...")
while True:
    schedule.run_pending()
    time.sleep(1)
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def index():
    return "AI Parlay Bot is running!"

def run_bot():
    send_daily_picks()  # Replace with the main function that starts your bot

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=8080)
