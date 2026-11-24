import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


print()
print("================================")
print("   TELEGRAM CONNECTION TEST")
print("================================")
print()

print("Bot token loaded:", bool(BOT_TOKEN))
print("Chat ID loaded:", bool(CHAT_ID))
print()


# Test 1: Check bot
print("Checking bot...")

response = requests.get(
    f"https://api.telegram.org/bot{BOT_TOKEN}/getMe",
    timeout=10
)

print("getMe response:")
print(response.text)
print()


# Test 2: Send simple message
print("Sending test message...")

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": "✅ AI Visitor Access System - Telegram connection test"
    },
    timeout=10
)

print("sendMessage response:")
print(response.text)
print()


if response.ok:
    print("================================")
    print("✅ MESSAGE SENT SUCCESSFULLY")
    print("================================")
else:
    print("================================")
    print("❌ MESSAGE FAILED")
    print("================================")