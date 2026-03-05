import discord
import os
import asyncio
import yfinance as yf
from datetime import datetime

TOKEN      = os.environ.get("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("ALERT_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# { message_id: { "ticker": "NQ=F", "level": 24838.0, "direction": "bullish" } }
active_levels = {}

def tv_ticker_to_yf(ticker):
    # Convert TradingView tickers to Yahoo Finance format
    mapping = {
        "NQ1!":  "NQ=F",
        "ES1!":  "ES=F",
        "MNQ1!": "MNQ=F",
        "MES1!": "MES=F",
        "GC1!":  "GC=F",
        "CL1!":  "CL=F",
    }
    return mapping.get(ticker, ticker)

def get_current_price(yf_ticker):
    try:
        data = yf.Ticker(yf_ticker)
        price = data.fast_info.last_price
        return float(price) if price else None
    except:
        return None

def parse_detection(content):
    # Format: "MOG 1H Bullish detected - NQ1! 24838"
    try:
        parts     = content.split(" - ")
        left      = parts[0].lower()
        right     = parts[1].split(" ")
        ticker    = right[0]
        level     = float(right[1])
        direction = "bullish" if "bullish" in left else "bearish" if "bearish" in left else None
        return ticker, level, direction
    except:
        return None, None, None

def is_detection(content):
    c = content.lower()
    return ("detected" in c) and ("mog" in c or "acog" in c) and ("macog" not in c)

def is_invalidated(level, current_price, direction):
    if direction == "bullish":
        return current_price >= level
    elif direction == "bearish":
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

    content = message.content

    # Handle embed messages (from relay)
    if message.embeds:
        embed = message.embeds[0]
        # Reconstruct content from embed title + description
        title       = embed.title or ""
        description = embed.description or ""
        content     = title + " - " + description

    if not is_detection(content):
        return

    ticker, level, direction = parse_detection(content)
    if not ticker or not level or not direction:
        return

    yf_ticker = tv_ticker_to_yf(ticker)
    active_levels[str(message.id)] = {
        "message_id": message.id,
        "ticker":     ticker,
        "yf_ticker":  yf_ticker,
        "level":      level,
        "direction":  direction,
        "channel_id": message.channel.id
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
                    msg     = await channel.fetch_message(data["message_id"])
                    await msg.delete()
                    direction_cap = data["direction"].capitalize()
                    emoji = "📈" if data["direction"] == "bullish" else "📉"
                    embed = discord.Embed(
                        title       = f"❌ {data['ticker']} {direction_cap} Level Invalidated",
                        description = f"{emoji} Price reached **{price}** — level **{data['level']}** invalidated",
                        color       = discord.Color.dark_gray(),
                        timestamp   = datetime.utcnow()
                    )
                    await channel.send(embed=embed)
                    to_delete.append(key)
                    print(f"Invalidated {data['direction']} {data['level']} for {data['ticker']}")
                except Exception as e:
                    print(f"Error deleting message: {e}")
                    to_delete.append(key)

        for key in to_delete:
            active_levels.pop(key, None)

        await asyncio.sleep(10)  # check every 10 seconds

client.run(TOKEN)
