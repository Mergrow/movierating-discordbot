import discord
from discord.ext import commands
from discord import app_commands
from cogs.variables import *
from cogs.db import save_rating, init_db
import asyncio
from datetime import datetime

class Rate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_users = {}
        self.votes = {}
        self.active_sessions = {}

    @app_commands.command(name="rate", description="Inicie uma votação para um filme com notas de 1 a 5.")
    @app_commands.describe(
        movie="Nome do filme para avaliar",
        participants="Mencione os usuários que poderão votar"
    )
    async def rate(self, interaction: discord.Interaction, movie: str, participants: str):
        await interaction.response.defer(ephemeral=True)

        mentioned_users = []
        not_found_users = []
        mentioned_ids = []

        # Extração dos IDs mencionados
        for part in participants.split():
            if part.startswith("<@") and part.endswith(">"):
                cleaned = part.strip("<@!>")
                if cleaned.isdigit():
                    mentioned_ids.append(int(cleaned))
                else:
                    not_found_users.append(part)
            else:
                not_found_users.append(part)

        # Verificar duplicidade, mas não considerar o host
        duplicates = [uid for uid in mentioned_ids if mentioned_ids.count(uid) > 1]
        duplicates = [uid for uid in duplicates if uid != interaction.user.id]  # Remover o host da verificação de duplicidade

        if duplicates:
            duplicate_usernames = []
            for uid in set(duplicates):
                member = interaction.guild.get_member(uid)
                if member:
                    duplicate_usernames.append(member.name)
            await interaction.followup.send(    
                f"❌ Votação não iniciada! Os seguintes usuários foram mencionados mais de uma vez:\n```{', '.join(duplicate_usernames)}```",
                ephemeral=True    
            )
            return

        # Verificar se IDs pertencem a membros
        for uid in set(mentioned_ids):
            member = interaction.guild.get_member(uid)
            if member:
                mentioned_users.append(member)
            else:
                not_found_users.append(str(uid))

        # Adicionar o host à votação apenas se ele foi mencionado
        if interaction.user.id not in mentioned_ids:
            mentioned_users.append(interaction.user)

        # Se houver usuários não encontrados
        if not_found_users:
            await interaction.followup.send(
                f"❌ Votação não iniciada! Os seguintes usuários não foram encontrados no servidor:\n```{', '.join(not_found_users)}```",
                ephemeral=True
            )
            return

        # Criar embed da votação
        embed = discord.Embed(
            title="🎬 Avaliação do Filme",
            description=f"**Filme:** {movie}\nReaja com uma nota de 1️⃣ a 5️⃣!",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Apenas usuários mencionados podem votar.")

        message = await interaction.channel.send(content=" ".join(u.mention for u in mentioned_users), embed=embed)

        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
        for emoji in emojis:
            await message.add_reaction(emoji)

        allowed_ids = [u.id for u in mentioned_users]
        self.allowed_users[message.id] = allowed_ids
        self.votes[message.id] = {}
        self.active_sessions[message.id] = {
            "movie": movie,
            "host": str(interaction.user),
            "timeout_task": self.bot.loop.create_task(self.end_by_timeout(message.id, 300)),
            "message": message
        }

        await interaction.followup.send("Mensagem de avaliação enviada!", ephemeral=True)

    async def end_by_timeout(self, message_id, timeout):
        await asyncio.sleep(timeout)
        if message_id in self.votes:
            await self.end_rating(message_id, timeout_expired=True)

    async def end_rating(self, message_id, timeout_expired=False):
        votes = self.votes.pop(message_id, {})
        session = self.active_sessions.pop(message_id, {})
        movie = session.get("movie", "Desconhecido")
        host_name = session.get("host", "Desconhecido")
        message = session.get("message")

        if not votes:
            if message:
                await message.reply("⏰ Votação encerrada por inatividade. Nenhum voto registrado.")
            return

        save_rating(movie, votes, host_name)

        average = sum(score for (_, score) in votes.values()) / len(votes)
        summary = "\n".join(f"<@{uid}> votou {score}." for uid, (_, score) in votes.items())
        result_text = (
            f"✅ Votação encerrada {'por tempo' if timeout_expired else ''}!\n\n"
            f"🎥 **Filme:** {movie}\n"
            f"👑 **Host:** {host_name}\n"
            f"📊 **Média das notas:** {average:.2f}\n\n{summary}"
        )
        if message:
            await message.reply(result_text)
            await message.delete()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        message = reaction.message
        if message.id not in self.allowed_users:
            return

        if user.id not in self.allowed_users[message.id]:
            await message.remove_reaction(reaction.emoji, user)
            return

        emoji_map = {
            '1️⃣': 1,
            '2️⃣': 2,
            '3️⃣': 3,
            '4️⃣': 4,
            '5️⃣': 5,
        }
        rating = emoji_map.get(reaction.emoji)
        if rating is None:
            await message.remove_reaction(reaction.emoji, user)
            return

        self.votes[message.id][user.id] = (str(user), rating)

        if len(self.votes[message.id]) >= len(self.allowed_users[message.id]):
            if message.id in self.active_sessions:
                task = self.active_sessions[message.id]["timeout_task"]
                task.cancel()
            await self.end_rating(message.id)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Rate cog loaded successfully.")

async def setup(bot):
    init_db()
    cog = Rate(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.rate, guild=discord.Object(id=DEV_GUILD))
