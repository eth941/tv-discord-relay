import asyncio
import os
import re
from datetime import datetime

import discord
import yfinance as yf

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("ALERT_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# { message_id: { "ticker": "NQ1!", "yf_ticker": "NQ=F", "level": 24838.0, "direction": "bullish" } }
active_levels = {}


def tv_ticker_to_yf(ticker):
    mapping = {
        "NQ1!": "NQ=F",
        "ES1!": "ES=F",
        "MNQ1!": "MNQ=F",
        "MES1!": "MES=F",
        "GC1!": "GC=F",
        "CL1!": "CL=F",
    }
    return mapping.get(ticker, ticker)


def get_current_price(yf_ticker):
    try:
        data = yf.Ticker(yf_ticker)
        price = data.fast_info.last_price
        return float(price) if price else None
    except Exception:
        return None


def direction_from_text(text):
    t = (text or "").lower()
    if "bullish" in t:
        return "bullish"
    if "bearish" in t:
        return "bearish"
    return None


def parse_detection_text(content):
    # Format: "MOG 1H Bullish detected - NQ1! 24838"
    try:
        parts = content.split(" - ", 1)
        left = parts[0].lower()
        right = parts[1].strip().split()
        ticker = right[0].strip()
        level = float(right[1])
        direction = direction_from_text(left)
        if not direction:
            return None, None, None
        return ticker, level, direction
    except Exception:
        return None, None, None


def parse_detection_embed(title, description):
    # Title examples: "1H MOG Bullish", "15m ACOG Bearish"
    # Description example: "**NQ1!** @ 24838"
    t = (title or "").lower()
    if "macog" in t:
        return None, None, None
    if "mog" not in t and "acog" not in t:
        return None, None, None

    direction = direction_from_text(t)
    if not direction:
        return None, None, None

    d = (description or "").strip()
    m = re.search(r"\*\*([^*]+)\*\*\s*@\s*(-?\d+(?:\.\d+)?)", d)
    if not m:
        m = re.search(r"([A-Z0-9!=.\-]+)\s*@\s*(-?\d+(?:\.\d+)?)", d)
    if not m:
        return None, None, None

    ticker = m.group(1).strip()
    level = float(m.group(2))
    return ticker, level, direction


def is_detection_text(content):
    c = (content or "").lower()
    return ("detected" in c) and ("mog" in c or "acog" in c) and ("macog" not in c)


def is_invalidated(level, current_price, direction):
    if direction == "bullish":
        return current_price >= level
    if direction == "bearish":
        return current_price <= level
    return False


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(price_check_loop())


@client.event
async def on_message(message):
    if not message.author.bot:
        return
    if message.channel.id != CHANNEL_ID:
        return

    ticker = level = direction = None

    # Prefer embed parsing because relay posts embeds.
    if message.embeds:
        embed = message.embeds[0]
        title = embed.title or ""
        description = embed.description or ""
        ticker, level, direction = parse_detection_embed(title, description)

    # Fallback for raw text detections.
    if ticker is None:
        content = message.content or ""
        if not is_detection_text(content):
            return
        ticker, level, direction = parse_detection_text(content)

    if not ticker or level is None or not direction:
        return

    yf_ticker = tv_ticker_to_yf(ticker)
    active_levels[str(message.id)] = {
        "message_id": message.id,
        "ticker": ticker,
        "yf_ticker": yf_ticker,
        "level": float(level),
        "direction": direction,
        "channel_id": message.channel.id,
    }
    print(f"Tracking {direction} level {level} for {ticker} (msg {message.id})")


async def price_check_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        to_delete = []
        for key, data in list(active_levels.items()):
            price = get_current_price(data["yf_ticker"])
            if price is None:
                continue

            if is_invalidated(data["level"], price, data["direction"]):
                try:
                    channel = client.get_channel(data["channel_id"])
                    msg = await channel.fetch_message(data["message_id"])
                    await msg.delete()

                    direction_cap = data["direction"].capitalize()
                    emoji = "BULL" if data["direction"] == "bullish" else "BEAR"
                    embed = discord.Embed(
                        title=f"INVALIDATED {data['ticker']} {direction_cap} Level",
                        description=f"{emoji} Price reached **{price}** - level **{data['level']}** invalidated",
                        color=discord.Color.dark_gray(),
                        timestamp=datetime.utcnow(),
                    )
                    await channel.send(embed=embed)
                    to_delete.append(key)
                    print(f"Invalidated {data['direction']} {data['level']} for {data['ticker']}")
                except Exception as e:
                    print(f"Error deleting message: {e}")
                    to_delete.append(key)

        for key in to_delete:
            active_levels.pop(key, None)

        await asyncio.sleep(10)


client.run(TOKEN)
