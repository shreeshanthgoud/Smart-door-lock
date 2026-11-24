import os
import threading

import requests
from dotenv import load_dotenv

load_dotenv()

ESP32_URL = os.getenv("ESP32_URL", "http://192.168.174.1")
ESP32_KEY = os.getenv("ESP32_KEY", "Hm7kQ29xvP4tLw")


def unlock_door():
    """Sends the unlock command in the background so the camera never freezes."""
    def _send():
        try:
            r = requests.get(
                f"{ESP32_URL}/unlock",
                params={"key": ESP32_KEY},
                timeout=5,
            )
            print(f"[door] ESP32 replied: {r.status_code} {r.text}")
        except Exception as e:
            print(f"[door] could not reach the ESP32: {e}")

    threading.Thread(target=_send, daemon=True).start()