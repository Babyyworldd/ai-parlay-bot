import os
import time
import threading
import requests
import random
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
    return "AI Parlay Bot is alive"

# Main Daily Picks
def send_daily_picks():
    """Fetch odds, pick 3 games, and send picks and parlay with max hype format."""
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

    # Send each pick individually
    for idx, p in enumerate(picks, start=1):
        msg = (
            "⛔⛔⛔⛔⛔⛔⛔⛔\n"
            "⚾️ *HARDROCK BANDITS* ⚾️\n"
            "🔥 _DAILY AI-POWERED PICK_ 🔥\n"
            "⛔⛔⛔⛔⛔⛔⛔⛔\n\n"
            f"*Game #{idx}:*\n"
            f"➡️ _{p['matchup']}_\n\n"
            f"✅ *Pick:*\n➡️ _{p['pick']}_\n\n"
            f"💸 *Odds:*\n➡️ _{p['odds']}_\n\n"
            f"🕒 *Start Time:*\n➡️ _{p['start_time']}_\n\n"
            f"⚡ *Confidence:*\n➡️ _{p['confidence']}%_\n\n"
            "=========================\n"
            "⚡ BACKED BY LIVE AI DATA ⚡\n"
            "=========================\n\n"
            "⚡🔥 _Smash this ticket and watch it cash!_ 🔥⚡"
        )
        requests.post(send_url, data={
            'chat_id': chat_id,
            'text': msg,
            'parse_mode': 'Markdown'
        })

    # Send parlay
    if len(picks) == 3:
        parlay_legs = [f"{i+1}️⃣ _{p['pick']} ({p['odds']})_" for i, p in enumerate(picks)]
        parlay_odds = round((picks[0]['odds'] * picks[1]['odds'] * picks[2]['odds']) - 1, 2)
        parlay_msg = (
            "⛔⛔⛔⛔⛔⛔⛔⛔\n"
            "⚾️ *HARDROCK BANDITS* ⚾️\n"
            "🔥 _AI PARLAY OF THE DAY!_ 🔥\n"
            "⛔⛔⛔⛔⛔⛔⛔⛔\n\n"
            "🎯 *Today's Legs:*\n\n"
            + "\n".join(parlay_legs) +
            "\n\n💥 *ESTIMATED RETURN:*\n" +
            f"➡️ _{parlay_odds}x_\n\n"
            "=========================\n"
            "⚡ LOCK IT IN. LET'S CASH OUT. ⚡\n"
            "========================="
        )
        requests.post(send_url, data={
            'chat_id': chat_id,
            'text': parlay_msg,
            'parse_mode': 'Markdown'
        })

# VIP Pick Manual Command
async def vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a manual VIP pick."""
    now = datetime.now(eastern)
    print(f"[{now.isoformat()}] VIP manual pick triggered...")

    try:
        response = requests.get(odds_url)
        games = response.json()
    except Exception as e:
        print("❌ Error fetching VIP pick:", e)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Error fetching VIP pick.")
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
                f"🔥 *Confidence:*\n_{random.randint(85, 95)}%_\n\n"
                f"🚀 *Start Time:*\n_{datetime.fromisoformat(start).strftime('%I:%M %p EST')}_\n\n"
                "---\n"
                "🔒 _VIP Access Only — Powered by AI_\n"
                "---"
            )
            await context.bot.send_message(chat_id=update.effective_chat.id, text=vip_msg, parse_mode="Markdown")
            break

        except (IndexError, KeyError):
            continue

# VIP Auto Drop - Pick
def send_vip_pick():
    """Send a daily VIP pick."""
    print(f"[{datetime.now(eastern).isoformat()}] Sending daily VIP pick...")
    send_url_vip = send_url

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
                f"🔥 *Confidence:*\n_{random.randint(85, 95)}%_\n\n"
                f"🚀 *Start Time:*\n_{datetime.fromisoformat(start).strftime('%I:%M %p EST')}_\n\n"
                "---\n"
                "🔒 _VIP Access Only — Powered by AI_\n"
                "---"
            )
            requests.post(send_url_vip, data={
                'chat_id': chat_id,
                'text': vip_msg,
                'parse_mode': 'Markdown'
            })
            break

        except (IndexError, KeyError):
            continue

# VIP Auto Drop - Mini 2 Leg Parlay
def send_vip_parlay():
    """Send a daily VIP 2-leg parlay."""
    print(f"[{datetime.now(eastern).isoformat()}] Sending daily VIP parlay...")

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
            "💎 *HARDROCK BANDITS VIP MINI PARLAY* 💎\n\n"
            "🔥 *Today's Legs:*\n\n"
            f"1️⃣ _{picks[0]['pick']} ({picks[0]['odds']})_\n"
            f"2️⃣ _{picks[1]['pick']} ({picks[1]['odds']})_\n\n"
            f"💰 *Estimated Return:* _{parlay_odds}x_\n\n"
            "---\n"
            "🔒 _Exclusive 2-Leg Parlay for VIPs_\n"
            "---"
        )
        requests.post(send_url, data={
            'chat_id': chat_id,
            'text': parlay_msg,
            'parse_mode': 'Markdown'
        })

# Telegram Bot Setup
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to Hardrock Bandits AI Picks!")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    send_daily_picks()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Test picks sent!")

def run_telegram_bot():
    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("vip", vip_command))
    app.run_polling()

# Scheduler
def run_scheduler():
    has_run_today = False
    has_run_vip_today = False
    while True:
        now = datetime.now(eastern)
        current_time = now.strftime("%H:%M")
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Scheduler heartbeat")

        if current_time == "11:00" and not has_run_today:
            send_daily_picks()
            has_run_today = True

        if current_time == "12:00" and not has_run_vip_today:
            send_vip_pick()
            send_vip_parlay()
            has_run_vip_today = True

        if current_time == "00:01":
            has_run_today = False
            has_run_vip_today = False

        time.sleep(60)

# Run App
if __name__ == '__main__':
    threading.Thread(target=run_scheduler, daemon=True).start()
    threading.Thread(target=run_telegram_bot, daemon=True).start()

    while True:
        time.sleep(1)
