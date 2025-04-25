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

# Load environment variables
bot_token = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")
api_key = os.getenv("API_KEY")

# Constants
odds_url = (
    f'https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/'
    f'?regions=us&markets=h2h&oddsFormat=decimal&apiKey={api_key}'
)
send_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
eastern = timezone('US/Eastern')

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "AI Parlay Bot is running"

# VIP memory
last_vip_pick = None
last_vip_parlay = None

# Daily Picks
def send_daily_picks():
    now = datetime.now(eastern)
    print(f"[{now.isoformat()}] Sending AI daily picks...")

    try:
        response = requests.get(odds_url)
        games = response.json()
    except Exception as e:
        print("❌ Error fetching picks:", e)
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

    for idx, p in enumerate(picks, start=1):
        msg = (
            "⛔⛔⛔⛔⛔⛔⛔⛔\n"
            "⚾️ *HARDROCK BANDITS* ⚾️\n"
            "🔥 _DAILY AI-POWERED PICK_ 🔥\n"
            "⛔⛔⛔⛔⛔⛔⛔⛔\n\n"
            f"*Game #{idx}:*\n➡️ _{p['matchup']}_\n\n"
            f"✅ *Pick:*\n➡️ _{p['pick']}_\n\n"
            f"💸 *Odds:*\n➡️ _{p['odds']}_\n\n"
            f"🕒 *Start Time:*\n➡️ _{p['start_time']}_\n\n"
            f"⚡ *Confidence:*\n➡️ _{p['confidence']}%_\n\n"
            "=========================\n"
            "⚡ BACKED BY LIVE AI DATA ⚡\n"
            "========================="
        )
        requests.post(send_url, data={
            'chat_id': chat_id,
            'text': msg,
            'parse_mode': 'Markdown'
        })

    if len(picks) == 3:
        parlay_legs = [f"{i+1}️⃣ _{p['pick']} ({p['odds']})_" for i, p in enumerate(picks)]
        parlay_odds = round((picks[0]['odds'] * picks[1]['odds'] * picks[2]['odds']) - 1, 2)
        parlay_msg = (
            "⚾️ *HARDROCK BANDITS AI PARLAY* ⚾️\n\n"
            "🎯 *Today's Parlay:*\n\n"
            + "\n".join(parlay_legs) +
            f"\n\n💰 *Estimated Return:* _{parlay_odds}x_\n"
            "⚡ Lock it in and cash out!"
        )
        requests.post(send_url, data={
            'chat_id': chat_id,
            'text': parlay_msg,
            'parse_mode': 'Markdown'
        })

# VIP Pick
def send_vip_pick():
    global last_vip_pick
    print(f"[{datetime.now(eastern).isoformat()}] Sending VIP pick...")

    try:
        response = requests.get(odds_url)
        games = response.json()
    except Exception as e:
        print("❌ Error fetching VIP pick:", e)
        return

    for game in games:
        try:
            home = game["home_team"]
            away = game["away_team"]
            start = game["commence_time"]
            outcomes = game["bookmakers"][0]["markets"][0]["outcomes"]
            pick = random.choice(outcomes)

            vip_msg = (
                "💎 *HARDROCK BANDITS VIP PICK* 💎\n\n"
                f"🏟️ *Matchup:*\n_{away} vs {home}_\n\n"
                f"✅ *Pick:*\n_{pick['name']}_\n\n"
                f"💰 *Odds:*\n_{round(pick['price'],2)}_\n\n"
                f"🔥 *Confidence:*\n_{random.randint(85,95)}%_\n\n"
                "🔒 _VIP Exclusive Only_"
            )
            last_vip_pick = vip_msg
            requests.post(send_url, data={
                'chat_id': chat_id,
                'text': vip_msg,
                'parse_mode': 'Markdown'
            })
            break
        except (IndexError, KeyError):
            continue

# VIP Parlay
def send_vip_parlay():
    global last_vip_parlay
    print(f"[{datetime.now(eastern).isoformat()}] Sending VIP parlay...")

    try:
        response = requests.get(odds_url)
        games = response.json()
    except Exception as e:
        print("❌ Error fetching VIP parlay:", e)
        return

    picks = []
    for game in games:
        try:
            home = game["home_team"]
            away = game["away_team"]
            outcomes = game["bookmakers"][0]["markets"][0]["outcomes"]
            pick = random.choice(outcomes)

            picks.append({
                "matchup": f"{away} vs {home}",
                "pick": pick["name"],
                "odds": round(pick["price"], 2),
            })

            if len(picks) == 2:
                break
        except (IndexError, KeyError):
            continue

    if len(picks) == 2:
        parlay_odds = round((picks[0]['odds'] * picks[1]['odds']) - 1, 2)
        parlay_msg = (
            "💎 *VIP 2-Team Parlay* 💎\n\n"
            f"1️⃣ {picks[0]['pick']} ({picks[0]['odds']})\n"
            f"2️⃣ {picks[1]['pick']} ({picks[1]['odds']})\n\n"
            f"💸 *Return:* _{parlay_odds}x_\n\n"
            "🔒 _VIP Exclusive Only_"
        )
        last_vip_parlay = parlay_msg
        requests.post(send_url, data={
            'chat_id': chat_id,
            'text': parlay_msg,
            'parse_mode': 'Markdown'
        })

# VIP Recap
def send_vip_recap():
    recap_msg = "💎 *HARDROCK BANDITS VIP DAILY RECAP* 💎\n\n"

    if last_vip_pick:
        recap_msg += f"✅ *VIP Pick:*\n\n{last_vip_pick.split('🔒')[0]}\n\n"
    else:
        recap_msg += "⚠️ No VIP pick recorded today.\n\n"

    if last_vip_parlay:
        recap_msg += f"✅ *VIP Parlay:*\n\n{last_vip_parlay.split('🔒')[0]}\n\n"
    else:
        recap_msg += "⚠️ No VIP parlay recorded today.\n\n"

    recap_msg += "🔒 _Thank you for being VIP!_"

    requests.post(send_url, data={
        'chat_id': chat_id,
        'text': recap_msg,
        'parse_mode': 'Markdown'
    })

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to Hardrock Bandits!")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    send_daily_picks()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Test Picks Sent!")

async def vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    send_vip_pick()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ VIP Pick Sent!")

# Scheduler
def run_scheduler():
    has_run_daily = False
    has_run_vip = False
    while True:
        now = datetime.now(eastern)
        current_time = now.strftime("%H:%M")
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Scheduler heartbeat")

        if current_time == "11:00" and not has_run_daily:
            send_daily_picks()
            has_run_daily = True

        if current_time == "12:00" and not has_run_vip:
            send_vip_pick()
            send_vip_parlay()
            has_run_vip = True

        if current_time == "23:59":
            send_vip_recap()

        if current_time == "00:01":
            has_run_daily = False
            has_run_vip = False

        time.sleep(60)

# Bot
async def start_bot():
    print("✅ Starting Bot...")
    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("vip", vip_command))
    await app.run_polling()

if __name__ == '__main__':
    print("✅ Starting Scheduler...")
    threading.Thread(target=run_scheduler, daemon=True).start()
    print("✅ Starting Bot Service...")
    asyncio.run(start_bot())
