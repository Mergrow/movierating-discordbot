import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import asyncio
from cogs.db import DB_PATH
from cogs.variables import *

class Rank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rank", description="Liste os filmes classificados com base no argumento (rating, date ou name).")
    @app_commands.describe(order_by="Argumento para ordenar os filmes (rating, date ou name)")
    async def rank(self, interaction: discord.Interaction, order_by: str):
        valid_order = ['rating', 'date', 'name']
        if order_by not in valid_order:
            await interaction.response.send_message(f"❌ Argumento inválido! Os argumentos válidos são: {', '.join(valid_order)}", ephemeral=True)
            return

        # Conectar ao banco de dados
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        if order_by == 'rating':
            c.execute("SELECT movie, host, participants, average, date FROM ratings ORDER BY average ASC")
        elif order_by == 'date':
            c.execute("SELECT movie, host, participants, average, date FROM ratings ORDER BY date DESC")
        elif order_by == 'name':
            c.execute("SELECT movie, host, participants, average, date FROM ratings ORDER BY movie ASC")

        rows = c.fetchall()
        conn.close()

        if not rows:
            await interaction.response.send_message("❌ Nenhum filme encontrado no banco de dados.", ephemeral=True)
            return

        def paginate(items, page, per_page=5):
            start = (page - 1) * per_page
            end = start + per_page
            return items[start:end]

        page = 1
        total_pages = (len(rows) + 4) // 5

        def create_embed(page):
            current_page_items = paginate(rows, page)
            embed = discord.Embed(title="🎬 Ranking de Filmes", color=discord.Color.blue())
            for idx, (movie, host, participants_str, average, date) in enumerate(current_page_items, start=(page - 1) * 5 + 1):
                participants = participants_str.split("; ")
                participants_display = "\n".join(participants)
                embed.add_field(
                    name=f"{idx}. {movie}",
                    value=f"**Host:** {host}\n**Média:** {average:.2f}\n**Data:** {date}\n**Participantes:**\n{participants_display}",
                    inline=False
                )
            embed.set_footer(text=f"Página {page}/{total_pages}")
            return embed

        class RankView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                self.message = None

            @discord.ui.button(label="◀️ Anterior", style=discord.ButtonStyle.primary, custom_id="previous_page")
            async def previous(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                nonlocal page
                if page > 1:
                    page -= 1
                    await self.message.edit(embed=create_embed(page))
                await interaction_button.response.defer()

            @discord.ui.button(label="▶️ Próxima", style=discord.ButtonStyle.primary, custom_id="next_page")
            async def next(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                nonlocal page
                if page < total_pages:
                    page += 1
                    await self.message.edit(embed=create_embed(page))
                await interaction_button.response.defer()

        view = RankView()
        embed = create_embed(page)
        message = await interaction.channel.send(embed=embed, view=view)
        view.message = message

        await interaction.response.send_message("📄 Ranking gerado.", ephemeral=True)

        async def delete_later():
            await asyncio.sleep(120)
            try:
                await message.delete()
            except discord.NotFound:
                pass

        self.bot.loop.create_task(delete_later())

    @commands.Cog.listener()
    async def on_ready(self):
        print("Rank cog loaded successfully.")

async def setup(bot):
    cog = Rank(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.rank, guild=discord.Object(id=DEV_GUILD))
