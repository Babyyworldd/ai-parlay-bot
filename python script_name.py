import requests

# Bot token and chat ID
BOT_TOKEN = "7923690296:AAEKjUOnPhITOMqKitPMq4fg_HzhfN_gtHQ"
CHAT_ID = "1002288236954"

# Message content
message_text = "This is a test message from your AI Parlay Bot."

# Send message
def send_test_message():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message_text,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print("✅ Test message sent successfully!")
    else:
        print(f"❌ Failed to send message: {response.status_code}")
        print(response.text)

send_test_message()
