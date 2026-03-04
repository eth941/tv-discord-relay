import discord
import os
from datetime import datetime

TOKEN      = os.environ.get("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("ALERT_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def get_direction(msg):
    m = msg.lower()
    if "bullish" in m:
        return "bullish"
    if "bearish" in m:
        return "bearish"
    return None

def is_1h_mog(msg):
    return "mog 1h" in msg.lower()

def is_15m_acog(msg):
    return "acog 15m" in msg.lower()

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot and message.channel.id == CHANNEL_ID:
        content   = message.content
        direction = get_direction(content)

        if not direction or not is_15m_acog(content):
            return

        # Scan back through channel history for most recent prior message
        history = [m async for m in message.channel.history(limit=20, before=message)]

        for prior in history:
            prior_content   = prior.content
            prior_direction = get_direction(prior_content)

            # Skip messages with no direction
            if not prior_direction:
                continue

            # Found most recent directional message - check if it's a 1H MOG same direction
            if is_1h_mog(prior_content) and prior_direction == direction:
                channel = client.get_channel(CHANNEL_ID)
                emoji   = "📈" if direction == "bullish" else "📉"
                color   = discord.Color.green() if direction == "bullish" else discord.Color.red()

                embed = discord.Embed(
                    title       = f"🔥 MACOG {direction.capitalize()} Setup",
                    description = f"{emoji} 1H MOG → 15m ACOG confirmed",
                    color       = color,
                    timestamp   = datetime.utcnow()
                )
                embed.add_field(name="Direction", value=direction.capitalize(), inline=True)
                embed.add_field(name="Trigger",   value=content,               inline=False)
                embed.add_field(name="1H MOG",    value=prior_content,         inline=False)

                await channel.send(embed=embed)
            break  # stop after first directional message regardless

client.run(TOKEN)
