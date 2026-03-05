from flask import Flask, request
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
MACOG_WINDOW_HOURS = 5

h1_mog_state = {}

def send_discord(message, color, title):
    embed = {
        "embeds": [{
            "title": title,
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    requests.post(DISCORD_WEBHOOK, json=embed)

def get_ticker(message):
    try:
        return message.split(" - ")[1].split(" ")[0]
    except:
        return None

def get_price(message):
    try:
        return message.split(" - ")[1].split(" ")[1]
    except:
        return ""

def get_direction(message):
    msg = message.lower()
    if "bullish" in msg:
        return "bullish"
    if "bearish" in msg:
        return "bearish"
    return None

# Discord colors (decimal)
GREEN  = 3066993
RED    = 15158332
ORANGE = 15844367
BLUE   = 3447003

@app.route("/webhook", methods=["POST"])
def webhook():
    message = request.get_data(as_text=True).strip()
    if not message:
        return "No message", 400

    ticker    = get_ticker(message)
    direction = get_direction(message)
    price     = get_price(message)
    now       = datetime.utcnow()
    msg_lower = message.lower()

    # Route to correct embed style
    if "mog 4h bullish" in msg_lower:
        send_discord(f"**{ticker}** @ {price}", GREEN, "📈 4H MOG Bullish")
    elif "mog 4h bearish" in msg_lower:
        send_discord(f"**{ticker}** @ {price}", RED, "📉 4H MOG Bearish")
    elif "mog 1h bullish" in msg_lower:
        send_discord(f"**{ticker}** @ {price}", GREEN, "📈 1H MOG Bullish")
    elif "mog 1h bearish" in msg_lower:
        send_discord(f"**{ticker}** @ {price}", RED, "📉 1H MOG Bearish")
    elif "acog 15m bullish" in msg_lower:
        send_discord(f"**{ticker}** @ {price}", GREEN, "📈 15m ACOG Bullish")
    elif "acog 15m bearish" in msg_lower:
        send_discord(f"**{ticker}** @ {price}", RED, "📉 15m ACOG Bearish")
    else:
        send_discord(message, BLUE, "Alert")

    # MACOG logic
    if ticker and direction:
        if "mog 1h" in msg_lower:
            if ticker not in h1_mog_state:
                h1_mog_state[ticker] = {}
            h1_mog_state[ticker][direction] = now

        elif "acog 15m" in msg_lower:
            ticker_state = h1_mog_state.get(ticker, {})
            h1_time      = ticker_state.get(direction)

            if h1_time and (now - h1_time) <= timedelta(hours=MACOG_WINDOW_HOURS):
                color = GREEN if direction == "bullish" else RED
                send_discord(f"**{ticker}** @ {price}", ORANGE, f"🔥 MACOG {direction.capitalize()} Setup")

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
