import os
import time
import threading
import asyncio
import logging
import schedule
import nest_asyncio
from flask import Flask
from telegram import Bot
from telegram.ext import Application
import gspread
import json
from google.oauth2.service_account import Credentials
from datetime import datetime

def connect_to_google_sheets():
    creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if not creds_json:
        raise Exception("Missing Google credentials!")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client

BOT_TOKEN = os.getenv('BOT_TOKEN')
VIP_CHAT_ID = os.getenv('VIP_CHAT_ID')
FREE_CHAT_ID = os.getenv('FREE_CHAT_ID')
SHEET_ID = '1-3gYwy14lTqZ3CWiB-2Np1RDeX7cgLS2rvHrlonXW1Y'

app = Flask(__name__)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

bot_app = Application.builder().token(BOT_TOKEN).build()

def send_text_message(chat_id, message):
    try:
        bot = Bot(BOT_TOKEN)
        bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
    except Exception as e:
        logging.error(f"Failed to send message: {e}")

def generate_daily_vip():
    message = (
        "<b>🔥 DAILY VIP DROP 🔥</b>\n\n"
        "⭐️ <u>Today's VIP Picks</u> ⭐️\n\n"
        "✅ Pick 1: Team A ML\n"
        "✅ Pick 2: Player X over 20.5 Points\n"
        "✅ Pick 3: Team B -1.5 Spread\n\n"
        "⏰ <b>LOCK IN!</b>\n"
        "⚡️ Let's cash big today!"
    )
    send_text_message(VIP_CHAT_ID, message)

def generate_vip_mini_parlay():
    message = (
        "<b>⚡️ MINI VIP PARLAY ⚡️</b>\n\n"
        "✅ Leg 1: Player Y Over 5.5 Assists\n"
        "✅ Leg 2: Player Z Over 1.5 Threes Made\n\n"
        "Parlay it up for some juicy value!\n"
        "⭐️ Good luck VIP fam ⭐️"
    )
    send_text_message(VIP_CHAT_ID, message)

def send_vip_recap():
    message = (
        "<b>📊 VIP DAILY RECAP 📊</b>\n\n"
        "✅ Pick 1: ✅ WIN\n"
        "✅ Pick 2: ❌ LOSS\n"
        "✅ Pick 3: ✅ WIN\n\n"
        "<b>RESULT:</b> 2-1 on the day!\n"
        "Let's keep building the bankroll!"
    )
    send_text_message(VIP_CHAT_ID, message)
    write_vip_results_to_sheet(2, 1)  # Example: 2 wins, 1 loss

def write_vip_results_to_sheet(wins, losses):
    try:
        client = connect_to_google_sheets()
        sheet = client.open_by_key(SHEET_ID).sheet1
        today = datetime.now().strftime("%Y-%m-%d")
        sheet.append_row([today, wins, losses])
        print("✅ VIP results written to Google Sheet!")
    except Exception as e:
        logging.error(f"Failed to write to Google Sheets: {e}")

def schedule_tasks():
    schedule.every().day.at("12:00").do(generate_daily_vip)
    schedule.every().day.at("12:30").do(generate_vip_mini_parlay)
    schedule.every().day.at("23:30").do(send_vip_recap)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

async def start_bot():
    print("✅ Inside start_bot async function...")
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await bot_app.updater.wait_until_closed()

def run_telegram_bot():
    print("✅ run_telegram_bot starting...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == '__main__':
    print("✅ Starting Scheduler...")
    threading.Thread(target=run_scheduler, daemon=True).start()

    print("✅ Starting Bot Service...")
    nest_asyncio.apply()
    schedule_tasks()

    try:
        loop = asyncio.get_event_loop()
        loop.create_task(start_bot())
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    except Exception as e:
        print(f"Error starting app: {e}")
