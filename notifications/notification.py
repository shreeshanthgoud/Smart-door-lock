import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def telegram_url(method):
    return f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"


def clear_old_updates():
    """
    Clear old Telegram updates before sending a new visitor request.
    This prevents old messages/buttons from interfering.
    """

    try:
        response = requests.get(
            telegram_url("getUpdates"),
            params={"offset": -1},
            timeout=10
        )

        if not response.ok:
            print("❌ Could not clear Telegram updates.")
            return

        data = response.json()
        updates = data.get("result", [])

        if updates:
            last_id = updates[-1]["update_id"]

            requests.get(
                telegram_url("getUpdates"),
                params={"offset": last_id + 1},
                timeout=10
            )

            print("✅ Old Telegram updates cleared.")

    except requests.RequestException as error:
        print("❌ Telegram error while clearing updates:")
        print(error)


def send_visitor_photo(image_path):
    """
    Send visitor photo with ACCEPT / REJECT buttons.
    """

    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Telegram credentials are missing.")
        return False

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False

    # Remove old updates first
    clear_old_updates()

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "✅ ACCEPT",
                    "callback_data": "visitor_accept"
                },
                {
                    "text": "❌ REJECT",
                    "callback_data": "visitor_reject"
                }
            ]
        ]
    }

    try:

        with open(image_path, "rb") as photo:

            response = requests.post(
                telegram_url("sendPhoto"),
                data={
                    "chat_id": CHAT_ID,
                    "caption": (
                        "🚨 Unknown Visitor Detected!\n\n"
                        "Someone is requesting access "
                        "to the door."
                    ),
                    "reply_markup": json.dumps(keyboard)
                },
                files={
                    "photo": photo
                },
                timeout=15
            )

        if response.ok:

            print("✅ Visitor image and buttons sent.")
            return True

        print("❌ Telegram sendPhoto error:")
        print(response.text)

        return False

    except requests.RequestException as error:

        print("❌ Telegram connection error:")
        print(error)

        return False


def check_user_decision(last_update_id=0):
    """
    Check Telegram for ACCEPT / REJECT button presses.
    """

    try:

        response = requests.get(
            telegram_url("getUpdates"),
            params={
                "offset": last_update_id + 1,
                "timeout": 5,
                "allowed_updates": json.dumps(
                    ["callback_query"]
                )
            },
            timeout=10
        )

        if not response.ok:

            print("❌ getUpdates error:")
            print(response.text)

            return None, last_update_id

        data = response.json()

        if not data.get("ok"):

            print("❌ Telegram API error:")
            print(data)

            return None, last_update_id

        updates = data.get("result", [])

        for update in updates:

            update_id = update.get("update_id")

            print(f"Telegram update received: {update_id}")

            callback = update.get("callback_query")

            if callback is None:

                last_update_id = update_id
                continue

            callback_data = callback.get("data")

            print(f"🎯 Button pressed: {callback_data}")

            # Check that the button came from your chat
            message = callback.get("message", {})
            chat = message.get("chat", {})
            chat_id = str(chat.get("id"))

            if chat_id != str(CHAT_ID):

                print("⚠️ Unauthorized Telegram chat.")

                last_update_id = update_id
                continue

            # Tell Telegram we received the button press
            callback_id = callback.get("id")

            try:

                requests.post(
                    telegram_url("answerCallbackQuery"),
                    data={
                        "callback_query_id": callback_id
                    },
                    timeout=5
                )

            except requests.RequestException:
                pass

            # Return decision
            if callback_data == "visitor_accept":

                return "ACCEPT", update_id

            elif callback_data == "visitor_reject":

                return "REJECT", update_id

            last_update_id = update_id

        return None, last_update_id

    except requests.RequestException as error:

        print("❌ Telegram connection error:")
        print(error)

        return None, last_update_id
def send_access_result(decision):
    """
    Send the final access decision to Telegram.
    """

    if decision == "ACCEPT":
        message = "✅ ACCESS GRANTED\n\nVisitor access has been approved."

    elif decision == "REJECT":
        message = "❌ ACCESS NOT GRANTED\n\nVisitor access has been rejected."

    else:
        return False

    try:
        response = requests.post(
            telegram_url("sendMessage"),
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=10
        )

        if response.ok:
            print("✅ Access result sent to Telegram.")
            return True

        print("❌ Failed to send access result:")
        print(response.text)
        return False

    except requests.RequestException as error:
        print("❌ Telegram error:")
        print(error)
        return False