# AI Smart Door Lock

A face-recognition door lock with remote owner approval. A camera recognises who is at the door. Registered people are let in automatically. For an unknown visitor, the system sends their photo to the owner's Telegram with **Accept / Reject** buttons, and the door unlocks only if the owner accepts.

## How it works

```
Webcam -> face detection -> face embedding -> compare with registered faces
                                                   |
                        known face ----------------+----> unlock command
                        unknown face -> photo to Telegram -> owner taps Accept
                                                   |
                                    Wi-Fi command -> ESP32 -> servo unlocks
                                                   |
                                      auto-relocks after 5 seconds
```

1. **Capture:** OpenCV reads frames from the webcam.
2. **Recognise:** each face is cropped to 160x160 and converted to an embedding. Its Euclidean distance to every registered embedding is measured. A distance of **0.8 or less** means a known person.
3. **Known person:** the door opens automatically after several consecutive matching frames, as long as no unknown face is in view.
4. **Unknown person:** a snapshot is sent to the owner's Telegram with Accept and Reject buttons. No answer within 60 seconds means **reject**.
5. **Unlock:** the laptop sends a key-protected HTTP command to the ESP32, which turns the servo and relocks after 5 seconds.

## Features

- Real-time face recognition with OpenCV and face embeddings
- Remote approval of unknown visitors through Telegram
- ESP32 web server controlling a servo lock over Wi-Fi
- Fail-safe design: any error, timeout or rejection keeps the door locked
- Secret API key protecting the ESP32 unlock command
- Automatic relock after 5 seconds
- Telegram and network calls run in background threads, so the video never freezes
- Only the owner's Telegram chat can approve entry

## Hardware

| Component | Role |
|---|---|
| ESP32 development board | Wi-Fi controller that receives the unlock command |
| Servo motor (SG90 or similar) | Moves the latch between locked and unlocked |
| Jumper wires | Connections |
| Laptop with webcam | Runs the face recognition |
| 5V supply (optional) | Separate power for the servo if USB power is not enough |

### Wiring

| Servo wire | ESP32 pin |
|---|---|
| Red (power) | 5V / VIN |
| Brown or black (ground) | GND |
| Orange or yellow (signal) | GPIO 18 |

If the servo twitches or the ESP32 restarts, power the servo from a separate 5V supply and connect its ground to the ESP32 GND.

## Tech stack

- **Language:** Python 3, C++ (Arduino)
- **Computer vision:** OpenCV, NumPy, a face detector and a face-embedding model
- **Notifications:** Telegram Bot API (`requests`)
- **Hardware:** ESP32 (Arduino core 3.x), servo motor
- **Config:** `python-dotenv`

## Project structure

```
smart-door-lock/
├── ai/door_access/
│   ├── access_control/
│   ├── camera/
│   ├── face_recognition/        # detector and embedder
│   ├── known_faces/             # registered faces (not committed)
│   ├── models/
│   ├── notifications/
│   │   └── notification.py     # Telegram approval flow
│   ├── recognize_visitor.py     # main program
│   ├── register_face.py         # add a new person
│   ├── door_control.py          # sends the unlock command to the ESP32
│   ├── config.py
│   ├── requirements.txt
│   └── .env.example
├── esp32/
│   └── door_lock.ino            # ESP32 sketch
└── README.md
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>/ai/door_access
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Create the Telegram bot

1. In Telegram, message `@BotFather` and send `/newbot`. Copy the **bot token**.
2. Send any message to your new bot.
3. Open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser and copy the number after `"chat":{"id":`. That is your **chat ID**.

### 3. Configure the environment

Copy `.env.example` to `.env` and fill in your values:

```
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
ESP32_URL=http://<esp32-ip>
ESP32_KEY=your-secret-key
```

Never commit `.env`.

### 4. Flash the ESP32

1. Install the Arduino IDE and the **esp32 by Espressif** board package.
2. Open `esp32/door_lock.ino` and set `WIFI_SSID`, `WIFI_PASS` and `API_KEY`. The key must match `ESP32_KEY` in `.env`.
3. Select **ESP32 Dev Module**, upload the sketch, and hold the **BOOT** button if the upload stalls at `Connecting......`.
4. Open the Serial Monitor at **115200** baud, press **EN**, and note the printed `ESP32 IP`. Use it as `ESP32_URL`.

The ESP32 needs a **2.4 GHz** Wi-Fi network, and the laptop must be on the same network.

Test it in a browser:

```
http://<esp32-ip>/status
http://<esp32-ip>/unlock?key=<your-secret-key>
```

### 5. Register faces

```bash
python register_face.py
```

Capture 10 to 20 photos per person in different lighting and angles for reliable recognition.

### 6. Run

```bash
python recognize_visitor.py
```

Press **Q** to quit.

## Configuration

Settings at the top of `recognize_visitor.py`:

| Setting | Default | Meaning |
|---|---|---|
| `THRESHOLD` | 0.8 | Maximum embedding distance for a match |
| `AUTO_UNLOCK_KNOWN` | True | Set to False to make known people use Telegram approval too |
| `KNOWN_FRAMES_REQUIRED` | 5 | Consecutive known frames before opening |
| `UNLOCK_COOLDOWN` | 10 | Seconds between automatic unlocks |

In `notifications/notification.py`: `DECISION_TIMEOUT` (60 s) is the time the owner has to answer.

On the ESP32: `OPEN_TIME_MS` (5000) is how long the door stays unlocked.

In our tests, registered faces measured about 0.5 and strangers about 1.1 to 1.5, so 0.8 separates them well. Tune the threshold for your own camera and lighting.

## Safety and security

- The door **starts locked** and **relocks automatically**.
- Rejection, no reply, an error or a network failure all result in a **locked** door.
- Telegram decisions are accepted only from the owner's chat ID, and each request has its own ID.
- Secrets live in `.env`, which is excluded from Git.

## Known limitations

- **No liveness detection.** A printed photo or a phone screen may fool the face recognition. Production use would need liveness checks or a second factor.
- **Plain HTTP on the local network.** A real deployment should use HTTPS or encrypted communication.
- **Prototype lock.** A servo demonstrates the mechanism, and a real door needs a proper electric lock with a mechanical backup.
- **Needs internet** for Telegram approval of unknown visitors.
- **No door sensor** in this version.

## Future improvements

- Liveness detection and anti-spoofing
- IR or magnetic door sensor
- HTTPS and stronger authentication for the ESP32
- Push notifications through a custom mobile app
- Access logs and history dashboard

## Team

| Name | Role |
|---|---|
| [Name 1] | Face recognition |
| [Name 2] | Hardware (ESP32 and servo) |
| [Name 3] | Integration and notifications |
| [Name 4] | Testing and documentation |

## License

Add your license here, for example MIT.
