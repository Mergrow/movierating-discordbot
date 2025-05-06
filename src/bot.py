import discord
from discord.ext import commands
import os
import time
import logging
from datetime import datetime
from cogs.variables import *

# Ensure the logs directory exists
os.makedirs("logs", exist_ok=True)

# Generate log file name based on today's date
log_filename = datetime.now().strftime("logs/%Y-%m-%d.log")

# Set up logging
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="[{asctime}] [{levelname}] {message}",
    datefmt="%Y-%m-%d %H:%M:%S",
    style="{"
)

# Get bot token from environment
bot_token = os.environ.get('DISCORD_TOKEN')  

intents = discord.Intents.all()
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        # Load the cogs
        await self.load_extension("cogs.misc")
        await self.load_extension("cogs.rate")
        await self.load_extension("cogs.rank")
        logging.info("Extensions loaded: misc, rate, rank")

        # Sync the commands only to the dev guild
        guild = discord.Object(id=DEV_GUILD)
        await self.tree.sync(guild=guild)
        logging.info(f"Slash commands synced to dev guild {DEV_GUILD}")
        print(f"[{time.strftime('%H:%M:%S')}] Slash commands synced to dev guild {DEV_GUILD}")

bot = MyBot(command_prefix="$", intents=intents)

@bot.event
async def on_ready():
    # Set activity
    activity = discord.Game(name="madwitch.net")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    # Log and print
    logging.info(f"Bot is ready - Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is Running!")
    print(f"Bot logged in as {bot.user} (ID: {bot.user.id})")

bot.run(bot_token)
