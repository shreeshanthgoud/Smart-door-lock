import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

print()
print("================================")
print("   TELEGRAM DEBUG TEST")
print("================================")
print()
print("Press ACCEPT or REJECT in Telegram.")
print()
print("Waiting for Telegram updates...")
print()


offset = None

while True:

    try:

        params = {
            "timeout": 10
        }

        if offset is not None:
            params["offset"] = offset

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        data = response.json()

        if not data.get("ok"):
            print()
            print("❌ Telegram API error:")
            print(data)
            time.sleep(2)
            continue

        updates = data.get("result", [])

        for update in updates:

            print()
            print("================================")
            print("NEW TELEGRAM UPDATE")
            print("================================")
            print(update)
            print("================================")
            print()

            # Move to next update
            offset = update["update_id"] + 1

            # Check for button press
            callback = update.get("callback_query")

            if callback:

                print("🎯 CALLBACK QUERY FOUND!")

                callback_data = callback.get("data")

                print("Button data:", callback_data)

                if callback_data == "visitor_accept":
                    print()
                    print("✅ ACCEPT BUTTON DETECTED")
                    print()

                elif callback_data == "visitor_reject":
                    print()
                    print("❌ REJECT BUTTON DETECTED")
                    print()

    except Exception as error:

        print()
        print("❌ Error:")
        print(error)
        print()

        time.sleep(2)