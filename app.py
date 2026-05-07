from flask import Flask, request
import requests
import os
from datetime import datetime

app = Flask(__name__)

DISCORD_WEBHOOK   = os.environ.get("DISCORD_WEBHOOK")    # Webhook 1 — MOG / ACOG
DISCORD_WEBHOOK_2 = os.environ.get("DISCORD_WEBHOOK_2")  # Webhook 2 — Prime Zone
DISCORD_WEBHOOK_3 = os.environ.get("DISCORD_WEBHOOK_3")  # Webhook 3 — MOAB

GREEN  = 3066993
RED    = 15158332
BLUE   = 3447003


def post_embed(webhook_url, title, description, color):
    embed = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    response = requests.post(webhook_url, json=embed)
    print(f"[{title}] STATUS: {response.status_code} | BODY: {response.text}", flush=True)


def get_ticker(message):
    """For format: 'LABEL - TICKER PRICE'"""
    try:
        return message.split(" - ")[1].split(" ")[0]
    except Exception:
        return "N/A"


def get_price(message):
    """For format: 'LABEL - TICKER PRICE'"""
    try:
        return message.split(" - ")[1].split(" ")[1]
    except Exception:
        return ""


@app.route("/webhook", methods=["POST"])
def webhook():
    message = request.get_data(as_text=True).strip()
    if not message:
        return "No message", 400

    msg_lower = message.lower()
    print(f"Received: {message}", flush=True)

    # ── Webhook 1 — MOG 1H / ACOG 15m ────────────────────────────────────────
    if "mog 1h bullish detected" in msg_lower:
        ticker = get_ticker(message)
        price  = get_price(message)
        post_embed(DISCORD_WEBHOOK, "📈 MOG 1H Bullish", f"**{ticker}** @ {price}", GREEN)

    elif "mog 1h bearish detected" in msg_lower:
        ticker = get_ticker(message)
        price  = get_price(message)
        post_embed(DISCORD_WEBHOOK, "📉 MOG 1H Bearish", f"**{ticker}** @ {price}", RED)

    elif "acog 15m bullish detected" in msg_lower:
        ticker = get_ticker(message)
        price  = get_price(message)
        post_embed(DISCORD_WEBHOOK, "📈 ACOG 15m Bullish", f"**{ticker}** @ {price}", GREEN)

    elif "acog 15m bearish detected" in msg_lower:
        ticker = get_ticker(message)
        price  = get_price(message)
        post_embed(DISCORD_WEBHOOK, "📉 ACOG 15m Bearish", f"**{ticker}** @ {price}", RED)

    # ── Webhook 2 — Prime Zone ────────────────────────────────────────────────
    elif "prime zone starting with active gap" in msg_lower:
        post_embed(DISCORD_WEBHOOK_2, "🟢 Prime Zone — Active Gap", message, GREEN)

    elif "prime zone starting no active gap" in msg_lower:
        post_embed(DISCORD_WEBHOOK_2, "🔴 Prime Zone — No Active Gap", message, RED)

    # ── Webhook 3 — MOAB ──────────────────────────────────────────────────────
    elif "moab: bullish 1h fvg tap" in msg_lower:
    ticker = get_ticker(message)
    price  = get_price(message)
    post_embed(DISCORD_WEBHOOK_3, "📈 MOAB Bullish 1H FVG Tap", f"**{ticker}** @ {price}", GREEN)

elif "moab: bearish 1h fvg tap" in msg_lower:
    ticker = get_ticker(message)
    price  = get_price(message)
    post_embed(DISCORD_WEBHOOK_3, "📉 MOAB Bearish 1H FVG Tap", f"**{ticker}** @ {price}", RED)

    # ── Fallback ──────────────────────────────────────────────────────────────
    else:
        post_embed(DISCORD_WEBHOOK, "Alert", message, BLUE)

    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
