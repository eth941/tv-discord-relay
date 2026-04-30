from flask import Flask, request
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)

DISCORD_WEBHOOK   = os.environ.get("DISCORD_WEBHOOK")
DISCORD_WEBHOOK_2 = os.environ.get("DISCORD_WEBHOOK_2")
DISCORD_WEBHOOK_3 = os.environ.get("DISCORD_WEBHOOK_3")

# { "MOG 1H Bullish NQ1!": "discord_message_id" }
message_ids = {}

def send_discord(message, color, title):
    embed = {
        "embeds": [{
            "title": title,
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    response = requests.post(DISCORD_WEBHOOK + "?wait=true", json=embed)
    print(f"STATUS: {response.status_code} | BODY: {response.text}", flush=True)
    if response.status_code == 200:
        return response.json().get("id")
    return None

def send_discord_2(message, color, title):
    embed = {
        "embeds": [{
            "title": title,
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    requests.post(DISCORD_WEBHOOK_2, json=embed)

def send_discord_3(message, color, title):
    embed = {
        "embeds": [{
            "title": title,
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    requests.post(DISCORD_WEBHOOK_3, json=embed)

def delete_discord_message(message_id):
    parts = DISCORD_WEBHOOK.rstrip("/").split("/")
    webhook_id    = parts[-2]
    webhook_token = parts[-1]
    url = f"https://discord.com/api/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}"
    requests.delete(url)

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

GREEN  = 3066993
RED    = 15158332
ORANGE = 15844367
BLUE   = 3447003
GRAY   = 9807270

@app.route("/webhook", methods=["POST"])
def webhook():
    message   = request.get_data(as_text=True).strip()
    if not message:
        return "No message", 400

    ticker    = get_ticker(message)
    price     = get_price(message)
    now       = datetime.utcnow()
    msg_lower = message.lower()

    # ── Invalidation — delete original message ────────────────────────────────
    if "invalidated" in msg_lower:
        if "mog 4h bullish" in msg_lower:
            key = f"MOG 4H Bullish {ticker}"
        elif "mog 4h bearish" in msg_lower:
            key = f"MOG 4H Bearish {ticker}"
        elif "mog 1h bullish" in msg_lower:
            key = f"MOG 1H Bullish {ticker}"
        elif "mog 1h bearish" in msg_lower:
            key = f"MOG 1H Bearish {ticker}"
        elif "acog 15m bullish" in msg_lower:
            key = f"ACOG 15m Bullish {ticker}"
        elif "acog 15m bearish" in msg_lower:
            key = f"ACOG 15m Bearish {ticker}"
        else:
            key = None

        if key and key in message_ids:
            delete_discord_message(message_ids.pop(key))

        return "OK", 200

    # ── Detection — send embed and store message ID ───────────────────────────
    msg_id = None

    if "mog 4h bullish" in msg_lower:
        msg_id = send_discord(f"**{ticker}** @ {price}", GREEN, "📈 4H MOG Bullish")
        key = f"MOG 4H Bullish {ticker}"
    elif "mog 4h bearish" in msg_lower:
        msg_id = send_discord(f"**{ticker}** @ {price}", RED, "📉 4H MOG Bearish")
        key = f"MOG 4H Bearish {ticker}"
    elif "mog 1h bullish" in msg_lower:
        msg_id = send_discord(f"**{ticker}** @ {price}", GREEN, "📈 1H MOG Bullish")
        key = f"MOG 1H Bullish {ticker}"
    elif "mog 1h bearish" in msg_lower:
        msg_id = send_discord(f"**{ticker}** @ {price}", RED, "📉 1H MOG Bearish")
        key = f"MOG 1H Bearish {ticker}"
    elif "acog 15m bullish" in msg_lower:
        msg_id = send_discord(f"**{ticker}** @ {price}", GREEN, "📈 15m ACOG Bullish")
        key = f"ACOG 15m Bullish {ticker}"
    elif "acog 15m bearish" in msg_lower:
        msg_id = send_discord(f"**{ticker}** @ {price}", RED, "📉 15m ACOG Bearish")
        key = f"ACOG 15m Bearish {ticker}"
    elif "prime zone starting with active gap" in msg_lower:
        send_discord_2(message, GREEN, "🟢 Prime Zone — Active Gap")
        return "OK", 200
    elif "prime zone starting no active gap" in msg_lower:
        send_discord_2(message, RED, "🔴 Prime Zone — No Active Gap")
        return "OK", 200
    elif "prime lite zone starting with active gap" in msg_lower:
        send_discord_2(message, GREEN, "🟢 Prime Lite Zone — Active Gap")
        return "OK", 200
    elif "prime lite zone starting no active gap" in msg_lower:
        send_discord_2(message, RED, "🔴 Prime Lite Zone — No Active Gap")
        return "OK", 200
    elif "moab: bullish 1h fvg tap" in msg_lower:
        send_discord_3(f"**{ticker}** @ {price}", GREEN, "📈 MOAB Bullish 1H FVG Tap")
        return "OK", 200
    elif "moab: bearish 1h fvg tap" in msg_lower:
        send_discord_3(f"**{ticker}** @ {price}", RED, "📉 MOAB Bearish 1H FVG Tap")
        return "OK", 200
    else:
        msg_id = send_discord(message, BLUE, "Alert")
        key = None

    if msg_id and key:
        message_ids[key] = msg_id

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
