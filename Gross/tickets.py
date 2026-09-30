import os
import io
import asyncio
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord import app_commands


# =========================================================
# 🐉🩷 MASGA GROSS / PINK DRAGON BOT
# =========================================================

TOKEN = os.environ.get("DISCORD_TOKEN")

PREFIX = "!"

STAFF_ROLE_ID = 1553781646124130536
TRANSCRIPT_CHANNEL_ID = 1551230773896421496
AUTO_ROLE_ID = 0


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.reactions = True


bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)

PINK = discord.Color.from_rgb(255, 105, 180)

warnings = {}


# =========================================================
# TICKET TYPES
# =========================================================

TICKET_TYPES = {
    "help": {
        "label": "Need Help",
        "emoji": "🆘",
        "description": "General questions or server assistance.",
        "category": "Need Help"
    },
    "buying": {
        "label": "Buying Bots",
        "emoji": "🤖",
        "description": "Questions about purchasing or ordering a bot.",
        "category": "Buying Bots"
    },
    "support": {
        "label": "Bot Support",
        "emoji": "🛠️",
        "description": "Help with an existing bot or bot problems.",
        "category": "Bot Support"
    },
    "technical": {
        "label": "Technical Support",
        "emoji": "💻",
        "description": "Technical issues and troubleshooting.",
        "category": "Technical Support"
    },
    "partnership": {
        "label": "Partnership",
        "emoji": "🤝",
        "description": "Partnership and collaboration requests.",
        "category": "Partnership"
    },
    "staff": {
        "label": "Staff Application",
        "emoji": "📋",
        "description": "Apply to join the staff team.",
        "category": "Staff Applications"
    },
    "other": {
        "label": "Other",
        "emoji": "📩",
        "description": "Anything that does not fit the options above.",
        "category": "Other"
    }
}


# =========================================================
# EMBED
# =========================================================

def dragon_embed(title, description=""):
    return discord.Embed(
        title=f"🐉🩷 {title}",
        description=description,
        color=PINK,
        timestamp=discord.utils.utcnow()
    )


# =========================================================
# STAFF CHECK
# =========================================================

def is_staff(member):

    if member.guild_permissions.administrator:
        return True

    if member.guild_permissions.manage_guild:
        return True

    if STAFF_ROLE_ID:
        role = member.guild.get_role(STAFF_ROLE_ID)

        if role and role in member.roles:
            return True

    return False


# =========================================================
# TICKET PANEL
# =========================================================

def ticket_panel_embed():

    return discord.Embed(
        title="🐉🩷 Pink Dragon Support",
        description=(
            "Welcome to **Pink Dragon Support**!\n\n"
            "Need help? Select the purpose of your ticket below.\n\n"

            "🆘 **Need Help**\n"
            "General questions or server assistance.\n\n"

            "🤖 **Buying Bots**\n"
            "Questions about purchasing or ordering a bot.\n\n"

            "🛠️ **Bot Support**\n"
            "Help with an existing bot or bot problems.\n\n"

            "💻 **Technical Support**\n"
            "Technical issues and troubleshooting.\n\n"

            "🤝 **Partnership**\n"
            "Partnership and collaboration requests.\n\n"

            "📋 **Staff Application**\n"
            "Apply to join the staff team.\n\n"

            "📩 **Other**\n"
            "Anything else.\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n"
            "🩷 **Select a purpose below to open a ticket.**"
        ),
        color=PINK
    )


# =========================================================
# TRANSCRIPT
# =========================================================

async def create_transcript(channel):

    lines = [
        "========================================",
        "🐉🩷 PINK DRAGON TICKET TRANSCRIPT",
        "========================================",
        f"Channel: {channel.name}",
        f"Channel ID: {channel.id}",
        f"Created: {channel.created_at}",
        "========================================",
        ""
    ]

    async for message in channel.history(
        limit=None,
        oldest_first=True
    ):

        timestamp = message.created_at.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        content = message.content

        if not content:
            content = "[No text / Embed / Attachment]"

        lines.append(
            f"[{timestamp}] {message.author} ({message.author.id}):"
        )

        lines.append(content)

        for attachment in message.attachments:
            lines.append(f"Attachment: {attachment.url}")

        lines.append("")

    transcript = "\n".join(lines)

    return discord.File(
        io.BytesIO(transcript.encode("utf-8")),
        filename=f"{channel.name}-transcript.txt"
    )


# =========================================================
# TICKET SELECT
# =========================================================

class TicketSelect(discord.ui.Select):

    def __init__(self):

        options = []

        for key, info in TICKET_TYPES.items():

            options.append(
                discord.SelectOption(
                    label=info["label"],
                    emoji=info["emoji"],
                    description=info["description"],
                    value=key
                )
            )

        super().__init__(
            placeholder="🎫 Select a ticket purpose...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="masga_ticket_select"
        )

    async def callback(self, interaction: discord.Interaction):

        ticket_type = self.values[0]
        info = TICKET_TYPES[ticket_type]

        guild = interaction.guild
        member = interaction.user

        existing_ticket = discord.utils.get(
            guild.text_channels,
            name=f"ticket-{member.id}"
        )

        if existing_ticket:

            await interaction.response.send_message(
                f"🩷 You already have a ticket: {existing_ticket.mention}",
                ephemeral=True
            )
            return

        category = discord.utils.get(
            guild.categories,
            name=info["category"]
        )

        if category is None:
            category = await guild.create_category(
                info["category"]
            )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),

            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),

            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True,
                attach_files=True
            )
        }

        if STAFF_ROLE_ID:

            staff_role = guild.get_role(STAFF_ROLE_ID)

            if staff_role:

                overwrites[staff_role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True
                )

        channel = await guild.create_text_channel(
            name=f"ticket-{member.id}",
            category=category,
            overwrites=overwrites,
            topic=f"{info['label']} • Opened by {member}"
        )

        embed = dragon_embed(
            f"{info['emoji']} {info['label']}",
            (
                f"Welcome {member.mention}! 🐉🩷\n\n"
                f"**Ticket Purpose:**\n"
                f"{info['label']}\n\n"
                "Please explain your request below.\n"
                "A staff member will assist you as soon as possible.\n\n"
                "When your issue is solved, use the button below "
                "to close this ticket.\n\n"
                "📄 A transcript will automatically be created "
                "when this ticket is closed."
            )
        )

        embed.set_footer(
            text="Masga Gross • Pink Dragon Support"
        )

        await channel.send(
            content=member.mention,
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"🐉🩷 Your ticket has been created!\n{channel.mention}",
            ephemeral=True
        )


# =========================================================
# TICKET PANEL VIEW
# =========================================================

class TicketPanelView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# =========================================================
# CLOSE TICKET
# =========================================================

class CloseTicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="masga_close_ticket"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        channel = interaction.channel

        if not channel.name.startswith("ticket-"):

            await interaction.response.send_message(
                "❌ This isn't a ticket channel.",
                ephemeral=True
            )
            return

        if not is_staff(interaction.user):

            owner_id = channel.name.replace(
                "ticket-",
                ""
            )

            if str(interaction.user.id) != owner_id:

                await interaction.response.send_message(
                    "❌ Only the ticket owner or staff can close this ticket.",
                    ephemeral=True
                )
                return

        await interaction.response.send_message(
            "📄 Creating transcript...\n"
            "🔒 Ticket will close in **5 seconds**."
        )

        try:

            transcript = await create_transcript(channel)

            transcript_channel = interaction.guild.get_channel(
                TRANSCRIPT_CHANNEL_ID
            )

            if transcript_channel:

                embed = discord.Embed(
                    title="📄 Ticket Transcript",
                    description=(
                        f"**Ticket:** `{channel.name}`\n"
                        f"**Closed by:** {interaction.user.mention}\n"
                        f"**Category:** "
                        f"{channel.category.name if channel.category else 'Unknown'}"
                    ),
                    color=PINK,
                    timestamp=discord.utils.utcnow()
                )

                await transcript_channel.send(
                    embed=embed,
                    file=transcript
                )

            await asyncio.sleep(5)

            await channel.delete(
                reason=f"Ticket closed by {interaction.user}"
            )

        except discord.Forbidden:

            try:
                await channel.send(
                    "❌ I don't have permission to close this ticket."
                )
            except:
                pass

        except discord.HTTPException as error:

            print(f"Ticket close error: {error}")


# =========================================================
# SLASH COMMANDS
# =========================================================

@bot.tree.command(
    name="ticketpanel",
    description="Create the Masga Gross ticket panel"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def ticketpanel(interaction: discord.Interaction):

    await interaction.channel.send(
        embed=ticket_panel_embed(),
        view=TicketPanelView()
    )

    await interaction.response.send_message(
        "🐉🩷 Ticket panel created!",
        ephemeral=True
    )


@bot.tree.command(
    name="tickethelp",
    description="Show information about the ticket system"
)
async def tickethelp(interaction: discord.Interaction):

    embed = dragon_embed(
        "Ticket System",
        (
            "**How it works:**\n\n"
            "1️⃣ Run `/ticketpanel`\n"
            "2️⃣ Members select a purpose.\n"
            "3️⃣ Masga Gross creates a private ticket.\n"
            "4️⃣ The member and staff can talk inside it.\n"
            "5️⃣ Click 🔒 to close the ticket.\n"
            "6️⃣ A `.txt` transcript is saved automatically."
        )
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


@bot.tree.command(
    name="help",
    description="Show Masga Gross commands"
)
async def slash_help(interaction: discord.Interaction):

    embed = dragon_embed(
        "Masga Gross Help",
        (
            "**Tickets**\n"
            "`/ticketpanel`\n"
            "`/tickethelp`\n\n"
            "**Prefix Commands**\n"
            "Use `!help` to see the full command list."
        )
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# =========================================================
# PREFIX TICKET COMMANDS
# =========================================================

@bot.command(name="ticket")
@commands.has_permissions(manage_guild=True)
async def ticket_command(ctx):

    await ctx.send(
        embed=ticket_panel_embed(),
        view=TicketPanelView()
    )


@bot.command(name="close")
async def close_command(ctx):

    channel = ctx.channel

    if not channel.name.startswith("ticket-"):

        await ctx.send(
            "❌ This command only works inside tickets."
        )
        return

    if not is_staff(ctx.author):

        owner_id = channel.name.replace(
            "ticket-",
            ""
        )

        if str(ctx.author.id) != owner_id:

            await ctx.send(
                "❌ You cannot close this ticket."
            )
            return

    await ctx.send(
        "📄 Creating transcript...\n"
        "🔒 Closing ticket in **5 seconds**."
    )

    try:

        transcript = await create_transcript(channel)

        transcript_channel = ctx.guild.get_channel(
            TRANSCRIPT_CHANNEL_ID
        )

        if transcript_channel:

            embed = discord.Embed(
                title="📄 Ticket Transcript",
                description=(
                    f"**Ticket:** `{channel.name}`\n"
                    f"**Closed by:** {ctx.author.mention}"
                ),
                color=PINK,
                timestamp=discord.utils.utcnow()
            )

            await transcript_channel.send(
                embed=embed,
                file=transcript
            )

        await asyncio.sleep(5)

        await channel.delete(
            reason=f"Ticket closed by {ctx.author}"
        )

    except Exception as error:

        print(f"Close command error: {error}")


@bot.command(name="add")
async def add_user(ctx, member: discord.Member):

    if not ctx.channel.name.startswith("ticket-"):
        await ctx.send("❌ This command only works inside tickets.")
        return

    if not is_staff(ctx.author):
        await ctx.send("❌ Staff only.")
        return

    await ctx.channel.set_permissions(
        member,
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        attach_files=True
    )

    await ctx.send(
        f"➕ Added {member.mention} to this ticket."
    )


@bot.command(name="remove")
async def remove_user(ctx, member: discord.Member):

    if not ctx.channel.name.startswith("ticket-"):
        await ctx.send("❌ This command only works inside tickets.")
        return

    if not is_staff(ctx.author):
        await ctx.send("❌ Staff only.")
        return

    await ctx.channel.set_permissions(
        member,
        view_channel=False
    )

    await ctx.send(
        f"➖ Removed {member.mention} from this ticket."
    )


# =========================================================
# MODERATION
# =========================================================

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):

    if member == ctx.author:
        await ctx.send("❌ You cannot kick yourself.")
        return

    await member.kick(reason=reason)

    await ctx.send(
        embed=dragon_embed(
            "Member Kicked",
            (
                f"👢 **Member:** {member.mention}\n"
                f"🛡️ **Moderator:** {ctx.author.mention}\n"
                f"📝 **Reason:** {reason}"
            )
        )
    )


@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):

    if member == ctx.author:
        await ctx.send("❌ You cannot ban yourself.")
        return

    await member.ban(reason=reason)

    await ctx.send(
        embed=dragon_embed(
            "Member Banned",
            (
                f"🔨 **Member:** {member.mention}\n"
                f"🛡️ **Moderator:** {ctx.author.mention}\n"
                f"📝 **Reason:** {reason}"
            )
        )
    )


@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):

    try:

        user = await bot.fetch_user(user_id)

        await ctx.guild.unban(user)

        await ctx.send(
            f"🔓 Unbanned **{user}**."
        )

    except discord.NotFound:

        await ctx.send(
            "❌ That user is not banned."
        )


@bot.command(name="timeout")
@commands.has_permissions(moderate_members=True)
async def timeout_member(
    ctx,
    member: discord.Member,
    minutes: int = 10,
    *,
    reason="No reason provided"
):

    if minutes < 1:
        await ctx.send("❌ Time must be at least 1 minute.")
        return

    if minutes > 40320:
        await ctx.send("❌ Timeout cannot exceed 28 days.")
        return

    until = discord.utils.utcnow() + timedelta(
        minutes=minutes
    )

    await member.timeout(
        until,
        reason=reason
    )

    await ctx.send(
        f"⏳ {member.mention} has been timed out for "
        f"**{minutes} minutes**."
    )


@bot.command(name="untimeout")
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):

    await member.timeout(
        None,
        reason=f"Timeout removed by {ctx.author}"
    )

    await ctx.send(
        f"🔓 Removed timeout from {member.mention}."
    )


@bot.command(name="warn")
@commands.has_permissions(moderate_members=True)
async def warn(
    ctx,
    member: discord.Member,
    *,
    reason="No reason provided"
):

    guild_id = ctx.guild.id

    warnings.setdefault(guild_id, {})
    warnings[guild_id].setdefault(member.id, [])

    warnings[guild_id][member.id].append({
        "reason": reason,
        "moderator": str(ctx.author),
        "time": discord.utils.utcnow()
    })

    count = len(
        warnings[guild_id][member.id]
    )

    await ctx.send(
        f"⚠️ {member.mention} has been warned.\n"
        f"**Reason:** {reason}\n"
        f"**Warnings:** {count}"
    )


@bot.command(name="warnings")
async def warning_list(ctx, member: discord.Member):

    guild_data = warnings.get(
        ctx.guild.id,
        {}
    )

    member_warnings = guild_data.get(
        member.id,
        []
    )

    if not member_warnings:

        await ctx.send(
            f"✅ {member.mention} has no warnings."
        )
        return

    embed = dragon_embed(
        f"Warnings — {member}"
    )

    for number, warning in enumerate(
        member_warnings,
        start=1
    ):

        embed.add_field(
            name=f"Warning #{number}",
            value=(
                f"**Reason:** {warning['reason']}\n"
                f"**Moderator:** {warning['moderator']}\n"
                f"**Date:** "
                f"{warning['time'].strftime('%Y-%m-%d %H:%M')}"
            ),
            inline=False
        )

    await ctx.send(embed=embed)


@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):

    if amount < 1:
        await ctx.send("❌ Amount must be at least 1.")
        return

    deleted = await ctx.channel.purge(
        limit=amount + 1
    )

    message = await ctx.send(
        f"🧹 Deleted **{len(deleted) - 1}** messages."
    )

    await asyncio.sleep(3)

    try:
        await message.delete()
    except:
        pass


@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock(ctx):

    overwrite = ctx.channel.overwrites_for(
        ctx.guild.default_role
    )

    overwrite.send_messages = False

    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite
    )

    await ctx.send(
        "🔒 This channel has been locked."
    )


@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):

    overwrite = ctx.channel.overwrites_for(
        ctx.guild.default_role
    )

    overwrite.send_messages = None

    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite
    )

    await ctx.send(
        "🔓 This channel has been unlocked."
    )


# =========================================================
# SERVER TOOLS
# =========================================================

@bot.command(name="say")
async def say(ctx, *, message):

    if not is_staff(ctx.author):
        await ctx.send(
            "❌ Staff only.",
            delete_after=5
        )
        return

    try:
        await ctx.message.delete()
    except:
        pass

    await ctx.send(message)


@bot.command(name="embed")
async def embed_command(ctx, *, message):

    if not is_staff(ctx.author):
        await ctx.send(
            "❌ Staff only.",
            delete_after=5
        )
        return

    try:
        await ctx.message.delete()
    except:
        pass

    await ctx.send(
        embed=discord.Embed(
            description=message,
            color=PINK
        )
    )


@bot.command(name="announce")
async def announce(ctx, *, message):

    if not is_staff(ctx.author):
        await ctx.send(
            "❌ Staff only.",
            delete_after=5
        )
        return

    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=PINK,
        timestamp=discord.utils.utcnow()
    )

    embed.set_footer(
        text=f"Posted by {ctx.author}"
    )

    await ctx.send(
        "@everyone",
        embed=embed
    )


@bot.command(name="userinfo")
async def userinfo(
    ctx,
    member: discord.Member = None
):

    member = member or ctx.author

    embed = discord.Embed(
        title=f"👤 User Info — {member}",
        color=PINK
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.add_field(
        name="Username",
        value=str(member),
        inline=True
    )

    embed.add_field(
        name="ID",
        value=str(member.id),
        inline=True
    )

    embed.add_field(
        name="Bot",
        value="Yes" if member.bot else "No",
        inline=True
    )

    embed.add_field(
        name="Joined Server",
        value=discord.utils.format_dt(
            member.joined_at,
            style="F"
        ) if member.joined_at else "Unknown",
        inline=False
    )

    roles = [
        role.mention
        for role in member.roles
        if role != ctx.guild.default_role
    ]

    embed.add_field(
        name="Roles",
        value=" ".join(roles) if roles else "None",
        inline=False
    )

    await ctx.send(embed=embed)


@bot.command(name="serverinfo")
async def serverinfo(ctx):

    guild = ctx.guild

    embed = discord.Embed(
        title=f"🏠 {guild.name}",
        color=PINK
    )

    if guild.icon:
        embed.set_thumbnail(
            url=guild.icon.url
        )

    embed.add_field(
        name="Owner",
        value=f"<@{guild.owner_id}>",
        inline=True
    )

    embed.add_field(
        name="Members",
        value=str(guild.member_count),
        inline=True
    )

    embed.add_field(
        name="Channels",
        value=str(len(guild.channels)),
        inline=True
    )

    embed.add_field(
        name="Roles",
        value=str(len(guild.roles)),
        inline=True
    )

    embed.add_field(
        name="Server ID",
        value=str(guild.id),
        inline=True
    )

    await ctx.send(embed=embed)


@bot.command(name="avatar")
async def avatar(
    ctx,
    member: discord.Member = None
):

    member = member or ctx.author

    embed = discord.Embed(
        title=f"🖼️ {member}'s Avatar",
        color=PINK
    )

    embed.set_image(
        url=member.display_avatar.url
    )

    await ctx.send(embed=embed)


@bot.command(name="roleinfo")
async def roleinfo(ctx, role: discord.Role):

    embed = discord.Embed(
        title=f"🎭 Role Info — {role.name}",
        color=role.color
    )

    embed.add_field(
        name="Role ID",
        value=str(role.id),
        inline=True
    )

    embed.add_field(
        name="Members",
        value=str(len(role.members)),
        inline=True
    )

    embed.add_field(
        name="Position",
        value=str(role.position),
        inline=True
    )

    embed.add_field(
        name="Mentionable",
        value=str(role.mentionable),
        inline=True
    )

    await ctx.send(embed=embed)


@bot.command(name="giverole")
@commands.has_permissions(manage_roles=True)
async def giverole(
    ctx,
    member: discord.Member,
    role: discord.Role
):

    await member.add_roles(
        role,
        reason=f"Role given by {ctx.author}"
    )

    await ctx.send(
        f"🎭 Added {role.mention} to {member.mention}."
    )


@bot.command(name="removerole")
@commands.has_permissions(manage_roles=True)
async def removerole(
    ctx,
    member: discord.Member,
    role: discord.Role
):

    await member.remove_roles(
        role,
        reason=f"Role removed by {ctx.author}"
    )

    await ctx.send(
        f"🎭 Removed {role.mention} from {member.mention}."
    )


# =========================================================
# AUTOROLE
# =========================================================

@bot.command(name="autorole")
async def autorole(ctx):

    if not is_staff(ctx.author):
        await ctx.send("❌ Staff only.")
        return

    if AUTO_ROLE_ID == 0:
        await ctx.send(
            "❌ AUTO_ROLE_ID has not been configured."
        )
        return

    role = ctx.guild.get_role(AUTO_ROLE_ID)

    if role is None:
        await ctx.send(
            "❌ Auto role was not found."
        )
        return

    await ctx.send(
        f"🤖 Auto-role is configured as {role.mention}."
    )


# =========================================================
# STAFF PANEL
# =========================================================

@bot.command(name="staffpanel")
async def staffpanel(ctx):

    if not is_staff(ctx.author):
        await ctx.send("❌ Staff only.")
        return

    embed = dragon_embed(
        "Staff Panel",
        (
            "🛡️ **Moderation**\n"
            "`!kick @user reason`\n"
            "`!ban @user reason`\n"
            "`!unban ID`\n"
            "`!timeout @user minutes reason`\n"
            "`!untimeout @user`\n"
            "`!warn @user reason`\n"
            "`!warnings @user`\n"
            "`!clear amount`\n"
            "`!lock`\n"
            "`!unlock`\n\n"

            "🎫 **Tickets**\n"
            "`!ticket`\n"
            "`!close`\n"
            "`!add @user`\n"
            "`!remove @user`\n\n"

            "⚙️ **Server Tools**\n"
            "`!say message`\n"
            "`!embed message`\n"
            "`!announce message`\n"
            "`!userinfo @user`\n"
            "`!serverinfo`\n"
            "`!avatar @user`\n"
            "`!roleinfo @role`\n"
            "`!giverole @user @role`\n"
            "`!removerole @user @role`"
        )
    )

    await ctx.send(embed=embed)


# =========================================================
# HELP
# =========================================================

@bot.command(name="help")
async def help_command(ctx):

    embed = dragon_embed(
        "Masga Gross Help",
        "Here are the available commands."
    )

    embed.add_field(
        name="🎫 Tickets",
        value=(
            "`!ticket`\n"
            "`!close`\n"
            "`!add @user`\n"
            "`!remove @user`"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Moderation",
        value=(
            "`!kick`\n"
            "`!ban`\n"
            "`!unban`\n"
            "`!timeout`\n"
            "`!untimeout`\n"
            "`!warn`\n"
            "`!warnings`\n"
            "`!clear`\n"
            "`!lock`\n"
            "`!unlock`"
        ),
        inline=False
    )

    embed.add_field(
        name="⚙️ Server",
        value=(
            "`!say`\n"
            "`!embed`\n"
            "`!announce`\n"
            "`!userinfo`\n"
            "`!serverinfo`\n"
            "`!avatar`\n"
            "`!roleinfo`"
        ),
        inline=False
    )

    embed.add_field(
        name="🎭 Roles",
        value=(
            "`!giverole`\n"
            "`!removerole`\n"
            "`!autorole`"
        ),
        inline=False
    )

    embed.add_field(
        name="🛠️ Staff",
        value="`!staffpanel`",
        inline=False
    )

    await ctx.send(embed=embed)


# =========================================================
# WELCOME + AUTOROLE
# =========================================================

@bot.event
async def on_member_join(member):

    if AUTO_ROLE_ID:

        role = member.guild.get_role(
            AUTO_ROLE_ID
        )

        if role:

            try:

                await member.add_roles(
                    role,
                    reason="Masga Gross Auto Role"
                )

            except discord.Forbidden:

                print(
                    "❌ Cannot give auto role."
                )

    welcome_channel = discord.utils.find(
        lambda channel:
            channel.name.lower() in [
                "welcome",
                "welcome-chat"
            ],
        member.guild.text_channels
    )

    if welcome_channel:

        embed = dragon_embed(
            "Welcome!",
            (
                f"Welcome {member.mention} to "
                f"**{member.guild.name}**! 🐉🩷\n\n"
                "Enjoy your stay!"
            )
        )

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        await welcome_channel.send(
            embed=embed
        )


# =========================================================
# MESSAGE FILTER
# =========================================================

BLOCKED_WORDS = {
    "badword1",
    "badword2"
}


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    content = message.content.lower()

    for word in BLOCKED_WORDS:

        if word in content:

            try:

                await message.delete()

                warning = await message.channel.send(
                    f"{message.author.mention}, please watch your language."
                )

                await asyncio.sleep(5)

                await warning.delete()

            except discord.Forbidden:
                pass

            break

    await bot.process_commands(message)


# =========================================================
# ERROR HANDLER
# =========================================================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingPermissions):

        await ctx.send(
            "❌ You don't have permission to use this command.",
            delete_after=5
        )
        return

    if isinstance(error, commands.MissingRequiredArgument):

        await ctx.send(
            "❌ You're missing a required argument.",
            delete_after=5
        )
        return

    if isinstance(error, commands.MemberNotFound):

        await ctx.send(
            "❌ I couldn't find that member.",
            delete_after=5
        )
        return

    if isinstance(error, commands.RoleNotFound):

        await ctx.send(
            "❌ I couldn't find that role.",
            delete_after=5
        )
        return

    if isinstance(error, commands.BadArgument):

        await ctx.send(
            "❌ Invalid argument.",
            delete_after=5
        )
        return

    print(
        f"Command error: {error}"
    )


# =========================================================
# READY
# =========================================================

@bot.event
async def on_ready():

    try:

        synced = await bot.tree.sync()

        print(
            f"🐉 Synced {len(synced)} slash commands."
        )

    except Exception as error:

        print(
            f"❌ Slash command sync error: {error}"
        )

    bot.add_view(
        TicketPanelView()
    )

    bot.add_view(
        CloseTicketView()
    )

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(
            name="Masga Gross 🐉🩷"
        )
    )

    print("======================================")
    print("🐉🩷 MASGA GROSS IS ONLINE")
    print(f"Bot: {bot.user}")
    print("🎮 Playing Masga Gross 🐉🩷")
    print("📄 Ticket transcripts enabled")
    print("======================================")


# =========================================================
# START
# =========================================================

if not TOKEN:

    print("======================================")
    print("❌ DISCORD_TOKEN IS NOT SET")
    print("======================================")
    print("Add DISCORD_TOKEN to your Render environment variables.")

else:

    bot.run(TOKEN)