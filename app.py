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

CARRY_CHANNEL_ID = 1517601489722282054
GRIND_CHANNEL_ID = 1517601555002691754
MAJOR_CARRY_CHANNEL_ID = 1517601583645593620
LOG_CHANNEL_ID = 1517601418901586141

CARRY_ROLE_ID = 1517602581071790280
GRIND_ROLE_ID = 1517602603666772049
MAJOR_CARRY_ROLE_ID = 1517602552819093614

# NEW ROLES
ALL_REQUESTS_ROLE_ID = 1517895181700173925      # carry + grind + majorcarry
CARRY_GRIND_ROLE_ID = 1517895036463874118       # carry + grind

TICKET_CATEGORY_ID = 1517602245842046996
STAFF_ROLE_ID = 1517602381888749689

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
    print(
        f"Checking {member} for role {role_id}\n"
        f"User roles: {[r.id for r in member.roles]}"
    )
    return any(r.id == role_id for r in member.roles)

async def log_action(msg):
    ch = bot.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(msg)

# ================= TICKET SYSTEM =================

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)

        if staff_role not in interaction.user.roles:
            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        await interaction.response.send_message("Closing ticket...")
        await asyncio.sleep(3)
        await interaction.channel.delete()


class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Create Ticket", style=discord.ButtonStyle.green)
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild

        category = guild.get_channel(TICKET_CATEGORY_ID)
        if not category:
            return await interaction.followup.send(
                "Ticket category missing.",
                ephemeral=True
            )

        existing = discord.utils.get(
            guild.channels,
            name=f"ticket-{interaction.user.id}"
        )

        if existing:
            return await interaction.followup.send(
                f"You already have a ticket: {existing.mention}",
                ephemeral=True
            )

        overwrites = {
            guild.default_role:
                discord.PermissionOverwrite(view_channel=False),

            interaction.user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True
                )
        }

        staff_role = guild.get_role(STAFF_ROLE_ID)

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            )

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            category=category,
            overwrites=overwrites
        )

        await channel.send(
            f"{interaction.user.mention} welcome to your ticket.",
            view=CloseTicketView()
        )

        await interaction.followup.send(
            f"Ticket created: {channel.mention}",
            ephemeral=True
        )

# ================= EVENTS =================

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print("=" * 40)
        print(f"Logged in as {bot.user}")
        print(f"Synced {len(synced)} commands")
        print("BOT UPDATED VERSION LOADED")
        print("=" * 40)
    except Exception as e:
        print("SYNC ERROR:", e)
        
# ================= ERROR HANDLER =================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):
    print("\n===== SLASH COMMAND ERROR =====")
    print(repr(error))
    print("==============================\n")

    try:
        if interaction.response.is_done():
            await interaction.followup.send(
                f"❌ Error: {error}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ Error: {error}",
                ephemeral=True
            )
    except Exception as e:
        print("Failed to send error:", e)
        
# ================= PANEL =================

@bot.tree.command(name="ticketpanel")
@app_commands.checks.has_permissions(administrator=True)
async def ticketpanel(interaction: discord.Interaction):

    await interaction.channel.send(
        "🎫 Support Ticket Panel",
        view=TicketView()
    )

    await interaction.response.send_message(
        "Panel sent.",
        ephemeral=True
    )

# ================= MODERATION =================

@bot.tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction, member: discord.Member, reason: str = "No reason"):
    await member.kick(reason=reason)
    await interaction.response.send_message("Kicked.")

@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction, member: discord.Member, reason: str = "No reason"):
    await member.ban(reason=reason)
    await interaction.response.send_message("Banned.")

@bot.tree.command(name="timeout")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction, member: discord.Member, minutes: int):
    await member.timeout(timedelta(minutes=minutes))
    await interaction.response.send_message("Timed out.")

@bot.tree.command(name="purge")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send(
        "Deleted messages.",
        ephemeral=True
    )

# ================= WARN =================

@bot.tree.command(name="warn")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction, member: discord.Member, reason: str):
    uid = str(member.id)
    warnings_db.setdefault(uid, []).append(reason)
    save_warnings(warnings_db)
    await interaction.response.send_message("Warned.")

@bot.tree.command(name="warnings")
async def warnings(interaction, member: discord.Member):
    data = warnings_db.get(str(member.id), [])
    await interaction.response.send_message(
        "\n".join(data) if data else "No warnings."
    )

# ================= CARRY =================

def can_carry(member):
    return (
        has_role(member, CARRY_ROLE_ID)
        or has_role(member, ALL_REQUESTS_ROLE_ID)
        or has_role(member, CARRY_GRIND_ROLE_ID)
    )

def can_grind(member):
    return (
        has_role(member, GRIND_ROLE_ID)
        or has_role(member, ALL_REQUESTS_ROLE_ID)
        or has_role(member, CARRY_GRIND_ROLE_ID)
    )

def can_majorcarry(member):
    return (
        has_role(member, MAJOR_CARRY_ROLE_ID)
        or has_role(member, ALL_REQUESTS_ROLE_ID)
    )


@bot.tree.command(name="carry")
async def carry(interaction: discord.Interaction):
    try:
        print("CARRY COMMAND USED")
        print("USER ROLES:", [r.id for r in interaction.user.roles])

        if not can_carry(interaction.user):
            return await interaction.response.send_message(
                f"No permission.\nYour roles: {[r.id for r in interaction.user.roles]}",
                ephemeral=True
            )

        ch = interaction.guild.get_channel(CARRY_CHANNEL_ID)

        if ch is None:
            return await interaction.response.send_message(
                "Carry channel not found.",
                ephemeral=True
            )

        await ch.send(
            f"<@&1517604341387759656> Carry requested by {interaction.user.mention}"
        )

        await interaction.response.send_message(
            "Carry request sent.",
            ephemeral=True
        )

    except Exception as e:
        print("CARRY ERROR:", repr(e))
        if not interaction.response.is_done():
            await interaction.response.send_message(
                str(e),
                ephemeral=True
            )


@bot.tree.command(name="grind")
async def grind(interaction: discord.Interaction):
    try:
        print("GRIND COMMAND USED")
        print("USER ROLES:", [r.id for r in interaction.user.roles])

        if not can_grind(interaction.user):
            return await interaction.response.send_message(
                f"No permission.\nYour roles: {[r.id for r in interaction.user.roles]}",
                ephemeral=True
            )

        ch = interaction.guild.get_channel(GRIND_CHANNEL_ID)

        if ch is None:
            return await interaction.response.send_message(
                "Grind channel not found.",
                ephemeral=True
            )

        await ch.send(
            f"<@&1517604391371276489> Grind requested by {interaction.user.mention}"
        )

        await interaction.response.send_message(
            "Grind request sent.",
            ephemeral=True
        )

    except Exception as e:
        print("GRIND ERROR:", repr(e))
        if not interaction.response.is_done():
            await interaction.response.send_message(
                str(e),
                ephemeral=True
            )


@bot.tree.command(name="majorcarry")
async def majorcarry(interaction: discord.Interaction):
    try:
        print("MAJORCARRY COMMAND USED")
        print("USER ROLES:", [r.id for r in interaction.user.roles])

        if not can_majorcarry(interaction.user):
            return await interaction.response.send_message(
                f"No permission.\nYour roles: {[r.id for r in interaction.user.roles]}",
                ephemeral=True
            )

        ch = interaction.guild.get_channel(MAJOR_CARRY_CHANNEL_ID)

        if ch is None:
            return await interaction.response.send_message(
                "Major carry channel not found.",
                ephemeral=True
            )

        await ch.send(
            f"@everyone Major Carry requested by {interaction.user.mention}"
        )

        await interaction.response.send_message(
            "Major carry request sent.",
            ephemeral=True
        )

    except Exception as e:
        print("MAJORCARRY ERROR:", repr(e))
        if not interaction.response.is_done():
            await interaction.response.send_message(
                str(e),
                ephemeral=True
            )
            
# ================= RUN =================

bot.run(TOKEN)
