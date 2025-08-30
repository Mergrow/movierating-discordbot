import discord
from discord.ext import commands
import os
import time
import logging
from datetime import datetime
from cogs.variables import *
import threading
from cogs.page import app as flask_app

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Generate log file name based on today's date
log_filename = datetime.now().strftime("logs/%Y-%m-%d.log")

# Set up logging (file + console)
logging.basicConfig(
    level=logging.INFO,
    format="[{asctime}] [{levelname}] {message}",
    datefmt="%Y-%m-%d %H:%M:%S",
    style="{",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Get bot token from environment
bot_token = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.all()
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        # Load the cogs
        await self.load_extension("cogs.misc")
        await self.load_extension("cogs.rate")
        await self.load_extension("cogs.rank")
        logging.info("Extensions loaded: misc, rate, rank")

        # Sync slash commands only to dev guild
        guild = discord.Object(id=DEV_GUILD)
        await self.tree.sync(guild=guild)
        logging.info(f"Slash commands synced to dev guild {DEV_GUILD}")
        print(f"[{time.strftime('%H:%M:%S')}] Slash commands synced to dev guild {DEV_GUILD}")

bot = MyBot(command_prefix="$", intents=intents)

def run_flask():
    flask_app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

@bot.event
async def on_ready():
    # Set activity
    activity = discord.Game(name="lasmovies.madwit.ch")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    # Log
    logging.info(f"Bot is ready - Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Bot logged in as {bot.user} (ID: {bot.user.id})")

bot.run(bot_token)
