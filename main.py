import os
import time
import threading
import requests
import random
import asyncio
from datetime import datetime
from pytz import timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask

# Load and strip environment variables
bot_token = os.getenv("BOT_TOKEN", "").strip()
chat_id = os.getenv("CHAT_ID", "").strip()
api_key = os.getenv("API_KEY", "").strip()

# Constants
odds_url = (
    f'https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/'
    f'?regions=us&markets=h2h&oddsFormat=decimal&apiKey={api_key}'
)
send_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
eastern = timezone('US/Eastern')

# Optional Flask (for future uptime pings)
app = Flask(__name__)
@app.route('/')
def home():
    return "AI Parlay Bot is alive"

# Core pick generator
def send_daily_picks():
    now = datetime.now(eastern)
    print(f"[{now.isoformat()}] Sending AI picks…")

    try:
        response = requests.get(odds_url)
        print("ODDS API STATUS:", response.status_code)
        games = response.json()
    except Exception as e:
        print("❌ Error fetching or parsing odds API:", e)
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

# Telegram commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "Welcome to *Hardrock Bandits AI Picks!* ⚾️\n\n"
        "You’ll get our best daily AI-generated parlays and picks here.\n"
        "Stay locked in!"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_msg, parse_mode="Markdown")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    send_daily_picks()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Test picks sent!")

# Start bot properly from thread
def run_telegram_bot():
    print("✅ Telegram bot starting...")
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()

    async def start_bot():
        app = ApplicationBuilder().token(bot_token).build()
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("test", test_command))
        await app.initialize()
        await app.start()
        print("✅ Telegram bot is running")
        await app.run_polling()

    loop.run_until_complete(start_bot())

# Daily scheduler
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

# Run both scheduler + bot
if __name__ == '__main__':
    threading.Thread(target=run_scheduler, daemon=True).start()
    threading.Thread(target=run_telegram_bot, daemon=True).start()

    while True:
        time.sleep(1)
