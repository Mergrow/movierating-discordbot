import discord
from discord.ext import commands
from cogs.variables import *

class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot  # Initialize the bot instance

    # Normal command with prefix $ (text command)
    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Pong!")

    # Slash command registered for the guild
    @commands.Cog.listener()
    async def on_ready(self):
        print("misc Cog loaded successfully.")

    @discord.app_commands.command(name="test", description="Say hello!")
    async def slash_test(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Hello, {interaction.user.mention}!")


async def setup(bot):
    # Setup function to load the cog
    cog = Misc(bot)
    await bot.add_cog(cog)

    # Register slash commands for a specific guild
    bot.tree.add_command(cog.slash_test, guild=discord.Object(id=DEV_GUILD))
