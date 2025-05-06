import discord
from discord.ext import commands
import os
import time
from cogs.variables import *


bot_token = os.environ.get('DISCORD_TOKEN')  # Get bot token from environment
intents = discord.Intents.all()
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        # Load the cogs
        await self.load_extension("cogs.misc")
        await self.load_extension("cogs.rate")
        await self.load_extension("cogs.rank")

        # Sync the commands only to the dev guild
        guild = discord.Object(id=DEV_GUILD)
        await self.tree.sync(guild=guild)
        print(f"[{time.strftime('%H:%M:%S')}] Slash commands synced to dev guild {DEV_GUILD}")

bot = MyBot(command_prefix="$", intents=intents)

@bot.event
async def on_ready():
    # Triggered when the bot is ready
    print(f"Bot logged in as {bot.user} (ID: {bot.user.id})")

bot.run(bot_token)
