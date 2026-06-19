import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View
from datetime import timedelta
import json
import asyncio
import os

# ================= CONFIG =================

TOKEN = os.getenv("TOKEN")

TICKET_CATEGORY_ID = 1517602245842046996
STAFF_ROLE_ID = 1517602381888749689

CARRY_CHANNEL_ID = 1517601489722282054
GRIND_CHANNEL_ID = 1517601555002691754
MAJOR_CARRY_CHANNEL_ID = 1517601583645593620
LOG_CHANNEL_ID = 1517601418901586141

CARRY_ROLE_ID = 1517602581071790280
GRIND_ROLE_ID = 1517602603666772049
MAJOR_CARRY_ROLE_ID = 1517602552819093614

WARNINGS_FILE = "warnings.json"

# ================= BOT =================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= WARN SYSTEM =================

def load_warnings():
    if os.path.exists(WARNINGS_FILE):
        with open(WARNINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_warnings(data):
    with open(WARNINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

warnings_db = load_warnings()

# ================= HELPERS =================

def has_role(member, role_id):
    return role_id and any(r.id == role_id for r in member.roles)

# ================= CLOSE VIEW =================

class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)

        if staff_role not in interaction.user.roles:
            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        await interaction.response.send_message("Closing ticket...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

# ================= TICKET SYSTEM =================

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Create Ticket", style=discord.ButtonStyle.green)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild

        category = guild.get_channel(TICKET_CATEGORY_ID)
        if not category:
            return await interaction.followup.send("Ticket category missing.", ephemeral=True)

        existing = discord.utils.get(guild.channels, name=f"ticket-{interaction.user.id}")
        if existing:
            return await interaction.followup.send(f"You already have a ticket: {existing.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        staff_role = guild.get_role(STAFF_ROLE_ID)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            category=category,
            overwrites=overwrites
        )

        await channel.send(
            f"{interaction.user.mention} ticket created.",
            view=CloseView()
        )

        await interaction.followup.send(f"Ticket created: {channel.mention}", ephemeral=True)

# ================= PANEL =================

@bot.tree.command(name="ticketpanel")
@app_commands.checks.has_permissions(administrator=True)
async def panel(interaction: discord.Interaction):

    await interaction.channel.send(
        "🎫 Click below to create a ticket",
        view=TicketView()
    )

    await interaction.response.send_message("Panel sent.", ephemeral=True)

# ================= MODERATION =================

@bot.tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    await member.kick(reason=reason)
    await interaction.response.send_message("Kicked.")

@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    await member.ban(reason=reason)
    await interaction.response.send_message("Banned.")

@bot.tree.command(name="timeout")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int):
    await member.timeout(timedelta(minutes=minutes))
    await interaction.response.send_message("Timed out.")

@bot.tree.command(name="purge")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send("Deleted messages.", ephemeral=True)

# ================= WARN =================

@bot.tree.command(name="warn")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    uid = str(member.id)
    warnings_db.setdefault(uid, []).append(reason)
    save_warnings(warnings_db)
    await interaction.response.send_message("Warned.")

@bot.tree.command(name="warnings")
async def warnings(interaction: discord.Interaction, member: discord.Member):
    data = warnings_db.get(str(member.id), [])
    await interaction.response.send_message("\n".join(data) if data else "No warnings.")

# ================= CARRY SYSTEM =================

@bot.tree.command(name="carry")
async def carry(interaction: discord.Interaction):
    if not has_role(interaction.user, CARRY_ROLE_ID):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    ch = bot.get_channel(CARRY_CHANNEL_ID)
    if ch:
        await ch.send(f"<@&{CARRY_ROLE_ID}> Carry requested by {interaction.user.mention}")

    await interaction.response.send_message("Sent.", ephemeral=True)

@bot.tree.command(name="grind")
async def grind(interaction: discord.Interaction):
    if not has_role(interaction.user, GRIND_ROLE_ID):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    ch = bot.get_channel(GRIND_CHANNEL_ID)
    if ch:
        await ch.send(f"<@&{GRIND_ROLE_ID}> Grind requested by {interaction.user.mention}")

    await interaction.response.send_message("Sent.", ephemeral=True)

@bot.tree.command(name="majorcarry")
async def majorcarry(interaction: discord.Interaction):
    if not has_role(interaction.user, MAJOR_CARRY_ROLE_ID):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    ch = bot.get_channel(MAJOR_CARRY_CHANNEL_ID)
    if ch:
        await ch.send(f"<@&{MAJOR_CARRY_ROLE_ID}> Major Carry requested by {interaction.user.mention}")

    await interaction.response.send_message("Sent.", ephemeral=True)

# ================= START =================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
