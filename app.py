import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View
import asyncio
import os

TOKEN = os.getenv("TOKEN")

TICKET_CATEGORY_ID = 1517602245842046996
STAFF_ROLE_ID = 1517602381888749689

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= CLOSE BUTTON =================

class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)

        if staff_role not in interaction.user.roles:
            return await interaction.response.send_message(
                "Only staff can close tickets.",
                ephemeral=True
            )

        await interaction.response.send_message("Closing ticket...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

# ================= TICKET PANEL =================

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Create Ticket", style=discord.ButtonStyle.green)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)

        if category is None:
            return await interaction.followup.send("Ticket category not set.", ephemeral=True)

        # prevent duplicates
        existing = discord.utils.get(
            interaction.guild.channels,
            name=f"ticket-{interaction.user.id}"
        )

        if existing:
            return await interaction.followup.send(
                f"You already have a ticket: {existing.mention}",
                ephemeral=True
            )

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            category=category,
            overwrites=overwrites
        )

        # THIS is the ONLY place close button is added
        await channel.send(
            f"{interaction.user.mention} your ticket has been created.",
            view=CloseView()
        )

        await interaction.followup.send(
            f"Ticket created: {channel.mention}",
            ephemeral=True
        )

# ================= PANEL COMMAND =================

@bot.tree.command(name="ticketpanel")
@app_commands.checks.has_permissions(administrator=True)
async def panel(interaction: discord.Interaction):

    await interaction.channel.send(
        "🎫 Click below to create a ticket",
        view=TicketView()
    )

    await interaction.response.send_message("Panel sent.", ephemeral=True)

# ================= START =================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
