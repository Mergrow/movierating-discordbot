import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from cogs.db import DB_PATH
from cogs.variables import *

class Rank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rank", description="Liste os filmes classificados com base no argumento (rating, date ou name).")
    @app_commands.describe(order_by="Argumento para ordenar os filmes (rating, date ou name)")
    async def rank(self, interaction: discord.Interaction, order_by: str):
        """Comando para listar filmes classificados de acordo com o argumento (rating, date ou name)."""
        valid_order = ['rating', 'date', 'name']
        if order_by not in valid_order:
            await interaction.response.send_message(f"❌ Argumento inválido! Os argumentos válidos são: {', '.join(valid_order)}", ephemeral=True)
            return

        # Conectar ao banco de dados e recuperar as classificações
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        if order_by == 'rating':
            c.execute("""
                SELECT movie, host, participants, average, date FROM ratings
                ORDER BY average ASC
            """)
        elif order_by == 'date':
            c.execute("""
                SELECT movie, host, participants, average, date FROM ratings
                ORDER BY date DESC
            """)
        elif order_by == 'name':
            c.execute("""
                SELECT movie, host, participants, average, date FROM ratings
                ORDER BY movie ASC
            """)

        # Recuperando os resultados
        rows = c.fetchall()
        conn.close()

        # Se não houver filmes registrados
        if not rows:
            await interaction.response.send_message("❌ Nenhum filme encontrado no banco de dados.", ephemeral=True)
            return

        # Função para dividir os filmes em páginas
        def paginate(items, page, per_page=5):
            start = (page - 1) * per_page
            end = start + per_page
            return items[start:end]

        # Dividir filmes em páginas
        page = 1
        total_pages = (len(rows) + 4) // 5  # Arredonda para cima

        # Mostrar os filmes da primeira página
        def create_embed(page):
            current_page_items = paginate(rows, page)
            embed = discord.Embed(title="🎬 Ranking de Filmes", color=discord.Color.blue())
            for idx, (movie, host, participants_str, average, date) in enumerate(current_page_items, start=(page - 1) * 5 + 1):
                # Preparar lista de participantes
                participants = participants_str.split("; ")
                participants_display = "\n".join(participants)

                embed.add_field(
                    name=f"{idx}. {movie}",
                    value=f"**Host:** {host}\n**Média:** {average:.2f}\n**Data:** {date}\n**Participantes:**\n{participants_display}",
                    inline=False
                )
            embed.set_footer(text=f"Página {page}/{total_pages}")
            return embed

        # Enviar a mensagem inicial com botões
        embed = create_embed(page)
        buttons = [
            discord.ui.Button(label="◀️ Anterior", style=discord.ButtonStyle.primary, custom_id="previous_page"),
            discord.ui.Button(label="▶️ Próxima", style=discord.ButtonStyle.primary, custom_id="next_page")
        ]
        view = discord.ui.View()
        for button in buttons:
            view.add_item(button)

        # Enviar a mensagem e manter referência nela
        message = await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("Gerando a lista com o ranking.", ephemeral=True)
        # Função para gerenciar o clique nos botões
        async def button_callback(interaction: discord.Interaction):
            nonlocal page

            if interaction.data["custom_id"] == "next_page" and page < total_pages:
                page += 1
            elif interaction.data["custom_id"] == "previous_page" and page > 1:
                page -= 1

            # Atualizar a embed com os filmes da página selecionada
            embed = create_embed(page)
            await message.edit(embed=embed)  # Editando a mensagem correta
            await interaction.response.defer()

        # Adiciona os callbacks aos botões
        for button in view.children:
            button.callback = button_callback

    @commands.Cog.listener()
    async def on_ready(self):
        print("Rank cog loaded successfully.")

async def setup(bot):
    cog = Rank(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.rank, guild=discord.Object(id=DEV_GUILD))
