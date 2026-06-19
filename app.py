# Demonology Crusaders Bot
# Fill in the IDs and TOKEN below before running.

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from datetime import timedelta
import json
import asyncio
import os

import os
TOKEN = os.getenv("TOKEN")

CARRY_CHANNEL_ID = 1517601489722282054
GRIND_CHANNEL_ID = 1517601555002691754
MAJOR_CARRY_CHANNEL_ID = 1517601583645593620
LOG_CHANNEL_ID = 1517601418901586141

CARRY_ROLE_ID = 1517602581071790280
GRIND_ROLE_ID = 1517602603666772049
MAJOR_CARRY_ROLE_ID = 1517602552819093614

TICKET_CATEGORY_ID = 1517602245842046996
STAFF_ROLE_ID = 1517602381888749689

WARNINGS_FILE = "warnings.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def load_warnings():
    if os.path.exists(WARNINGS_FILE):
        with open(WARNINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_warnings(data):
    with open(WARNINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

warnings_db = load_warnings()

def has_role(member, role_id):
    return role_id and any(r.id == role_id for r in member.roles)

async def log_action(msg):
    ch = bot.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(msg)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
@discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green)
async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild

    if TICKET_CATEGORY_ID == 0:
        return await interaction.followup.send(
            "Ticket system not configured (missing category ID).",
            ephemeral=True
        )

    category = guild.get_channel(TICKET_CATEGORY_ID)

    if category is None:
        return await interaction.followup.send(
            "Ticket system not set up correctly (invalid category ID).",
            ephemeral=True
        )

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
    }

    channel = await guild.create_text_channel(
        name=f"ticket-{interaction.user.id}",
        category=category,
        overwrites=overwrites
    )

    await interaction.followup.send(
        f"Ticket created: {channel.mention}",
        ephemeral=True
    )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        if STAFF_ROLE_ID != 0:
            role = guild.get_role(STAFF_ROLE_ID)
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            category=category,
            overwrites=overwrites
        )

        await interaction.response.send_message(
            f"Ticket created: {channel.mention}",
            ephemeral=True
        )

    except Exception as e:
        print(e)
        await interaction.response.send_message(
            "Error creating ticket. Check bot permissions or IDs.",
            ephemeral=True
        )
        existing = discord.utils.get(guild.channels, name=f"ticket-{interaction.user.id}")
        if existing:
            await interaction.response.send_message(f"You already have a ticket: {existing.mention}", ephemeral=True)
            return

        category = guild.get_channel(TICKET_CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            category=category,
            overwrites=overwrites
        )

        close_view = CloseTicketView()
        await channel.send(
            f"{interaction.user.mention} Welcome to Demonology Crusaders Ticket Section.",
            view=close_view
        )

        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)
        await log_action(f"🎫 Ticket created by {interaction.user}")

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Closing ticket in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Sync error: {e}")

    print(f"Logged in as {bot.user}")

@bot.tree.command(name="ticketpanel")
@app_commands.checks.has_permissions(administrator=True)
async def ticketpanel(interaction: discord.Interaction):
    await interaction.channel.send("🎫 Demonology Crusaders Support", view=TicketView())
    await interaction.response.send_message("Panel created.", ephemeral=True)

@bot.tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str="No reason"):
    await member.kick(reason=reason)
    await interaction.response.send_message("Member kicked.")
    await log_action(f"Kick: {member} by {interaction.user}")

@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str="No reason"):
    await member.ban(reason=reason)
    await interaction.response.send_message("Member banned.")
    await log_action(f"Ban: {member} by {interaction.user}")

@bot.tree.command(name="unban")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"Unbanned {user}")

@bot.tree.command(name="timeout")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int):
    await member.timeout(timedelta(minutes=minutes))
    await interaction.response.send_message("Timeout applied.")

@bot.tree.command(name="purge")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send("Messages deleted.", ephemeral=True)

@bot.tree.command(name="warn")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    uid = str(member.id)
    warnings_db.setdefault(uid, []).append(reason)
    save_warnings(warnings_db)
    await interaction.response.send_message("User warned.")

@bot.tree.command(name="warnings")
async def warnings(interaction: discord.Interaction, member: discord.Member):
    data = warnings_db.get(str(member.id), [])
    await interaction.response.send_message("\\n".join(data) if data else "No warnings.")

@bot.tree.command(name="say")
@app_commands.checks.has_permissions(administrator=True)
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message("Sent.", ephemeral=True)
    await interaction.channel.send(message)

@bot.tree.command(name="carry")
async def carry(interaction: discord.Interaction):
    if not has_role(interaction.user, CARRY_ROLE_ID):
        return await interaction.response.send_message("No permission.", ephemeral=True)
    ch = bot.get_channel(CARRY_CHANNEL_ID)
    if ch: await ch.send(f"<@&{1517604341387759656}> Carry requested by {interaction.user.mention} Please join the link that will be sent in a moment...")
    await interaction.response.send_message("Sent.", ephemeral=True)

@bot.tree.command(name="grind")
async def grind(interaction: discord.Interaction):
    if not has_role(interaction.user, GRIND_ROLE_ID):
        return await interaction.response.send_message("No permission.", ephemeral=True)
    ch = bot.get_channel(GRIND_CHANNEL_ID)
    if ch: await ch.send(f"<@&{1517604391371276489}> Grind requested by {interaction.user.mention} Please join the link that will be sent in a moment...")
    await interaction.response.send_message("Sent.", ephemeral=True)

@bot.tree.command(name="majorcarry")
async def majorcarry(interaction: discord.Interaction):
    if not has_role(interaction.user, MAJOR_CARRY_ROLE_ID):
        return await interaction.response.send_message("No permission.", ephemeral=True)
    ch = bot.get_channel(MAJOR_CARRY_CHANNEL_ID)
    if ch: await ch.send(f"@everyone Major Carry/Grind requested by {interaction.user.mention} Please join the link that will be sent in a moment...")
    await interaction.response.send_message("Sent.", ephemeral=True)

bot.run(TOKEN)
