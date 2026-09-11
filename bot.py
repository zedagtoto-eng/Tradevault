# ============================================================
# IMPORTS
# ============================================================

import os
import json
import re
import io
import asyncio
import datetime
import discord
from discord.ext import commands


# ============================================================
# TOKEN
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set")


# ============================================================
# BOT
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="$",
    intents=intents
)


# ============================================================
# FILES
# ============================================================

VOUCH_FILE = "vouches.json"
TEMP_FILE = "temp_roles.json"
BACKUP_FILE = "server_backup.json"


# ============================================================
# TICKET SETTINGS
# ============================================================

TICKET_CATEGORY_ID = 1547452777427632249
TRANSCRIPT_CHANNEL_ID = 1547487090634133524

MIDDLEMAN_ROLE_ID = 1546891552507564032

# ============================================================
# APPLICATION SETTINGS
# ============================================================

APPLICATION_ROLE_ID = 1546891150177206373
RESULT_CHANNEL_ID = 1547444944606593066

PINK = discord.Color.from_rgb(217, 232, 74)


# ============================================================
# TEMP ROLE SETTINGS
# ============================================================

TEMP_KEEP_ROLE_IDS = [
    1546891150177206373,
    1461242044306685973
]


# ============================================================
# VOUCH DATA
# ============================================================

def load_vouches():

    if not os.path.exists(VOUCH_FILE):
        return {}

    try:
        with open(VOUCH_FILE, "r") as f:
            return json.load(f)

    except (json.JSONDecodeError, OSError):
        return {}


def save_vouches(data):

    with open(VOUCH_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ============================================================
# TEMP DATA
# ============================================================

def load_temp_data():

    if not os.path.exists(TEMP_FILE):
        return {}

    try:
        with open(TEMP_FILE, "r") as f:
            return json.load(f)

    except (json.JSONDecodeError, OSError):
        return {}


def save_temp_data(data):

    with open(TEMP_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ============================================================
# MEMBER RESOLVER
# ============================================================

async def get_member(ctx, value):

    if isinstance(value, discord.Member):
        return value

    value = str(value).strip()

    match = re.fullmatch(
        r"<@!?(\d+)>",
        value
    )

    if match:

        user_id = int(match.group(1))

    elif value.isdigit():

        user_id = int(value)

    else:

        return None

    return ctx.guild.get_member(user_id)


# ============================================================
# MEMBER INPUT RESOLVER
# ============================================================

async def get_member_from_input(ctx, value):

    if isinstance(value, discord.Member):
        return value

    value = str(value).strip()

    match = re.fullmatch(
        r"<@!?(\d+)>",
        value
    )

    if match:

        user_id = int(match.group(1))

        return ctx.guild.get_member(
            user_id
        )

    if value.isdigit():

        return ctx.guild.get_member(
            int(value)
        )

    value_lower = value.lower()

    for member in ctx.guild.members:

        if str(member).lower() == value_lower:

            return member

        if member.name.lower() == value_lower:

            return member

        if member.display_name.lower() == value_lower:

            return member

    return None


# ============================================================
# APPLICATION BUTTONS
# ============================================================

class ApplicationView(discord.ui.View):

    def __init__(self, member_id):

        super().__init__(timeout=120)

        self.member_id = member_id
        self.finished = False

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if interaction.user.id != self.member_id:

            await interaction.response.send_message(
                "❌ This application is not for you.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="Accept",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="application_accept"
    )
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.finished:

            return await interaction.response.send_message(
                "❌ This application has already been decided.",
                ephemeral=True
            )

        guild = interaction.guild

        if guild is None:

            return await interaction.response.send_message(
                "❌ This can only be used inside a server.",
                ephemeral=True
            )

        member = guild.get_member(
            self.member_id
        )

        if member is None:

            try:

                member = await guild.fetch_member(
                    self.member_id
                )

            except discord.NotFound:

                return await interaction.response.send_message(
                    "❌ User is no longer in the server.",
                    ephemeral=True
                )

        role = guild.get_role(
            APPLICATION_ROLE_ID
        )

        if role is None:

            return await interaction.response.send_message(
                "❌ Application role was not found.\n"
                "Check APPLICATION_ROLE_ID.",
                ephemeral=True
            )

        if role >= guild.me.top_role:

            return await interaction.response.send_message(
                "❌ I can't give this role.\n\n"
                "Make sure my bot's highest role is ABOVE "
                "the application role.",
                ephemeral=True
            )

        try:

            await member.add_roles(
                role,
                reason="Application accepted"
            )

        except discord.Forbidden:

            return await interaction.response.send_message(
                "❌ I can't give this role.\n\n"
                "Make sure I have **Manage Roles** and "
                "my bot role is above the application role.",
                ephemeral=True
            )

        except discord.HTTPException:

            return await interaction.response.send_message(
                "❌ Discord returned an error while giving "
                "the role. Please try again.",
                ephemeral=True
            )

        self.finished = True

        # DM the accepted user
        tutorial_embed = discord.Embed(
            title="How to Flop - Quick Tutorial",
            description=(
                "**Step 1: Identify a Scam Attempt**\n"
                "Watch for fake deals, suspicious users, or people trying "
                "to pressure you into using an unofficial middleman.\n\n"

                "**Step 2: Verify the Deal**\n"
                "Never trust screenshots or claims alone. Verify the trader, "
                "middleman, and transaction details before proceeding.\n\n"

                "**Step 3: Create an Official Ticket**\n"
                "Use the server's official MM/request channel and keep the "
                "entire trade inside the server.\n\n"

                "**Step 4: Wait for Staff**\n"
                "Wait for an official Middleman or staff member to handle "
                "the process. Never follow instructions from random DMs.\n\n"

                "**Splits**\n"
                "Always confirm the agreed split with the official Middleman "
                "before completing the trade."
            ),
            color=discord.Color.from_rgb(217, 232, 74)
        )

        try:
            await member.send(embed=tutorial_embed)
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

        for child in self.children:
            child.disabled = True

        application_embed = discord.Embed(
            title="Application Accepted",
            description=(
                f"✅ {member.mention} has been accepted "
                f"and received {role.mention}."
            ),
            color=0x6A0DAD
        )

        application_embed.set_footer(
            text="TradeVault • Application System"
        )

        await interaction.response.edit_message(
            embed=application_embed,
            view=self
        )

        result_channel = guild.get_channel(
            RESULT_CHANNEL_ID
        )

        if result_channel is None:

            print(
                "❌ RESULT_CHANNEL_ID is incorrect "
                "or the bot cannot see that channel."
            )

            return

        welcome_embed = discord.Embed(
            title="🎉 New Flopper!",
            description=(
                f"Congratulations {member.mention}, "
                "you're now a flopper!\n\n"

                "• To learn about flopping or how to get rich "
                "join the main-guide channel\n\n"

                "• To hangout with other floppers "
                "talk in the staff-chat channel\n\n"

                "• Lastly to get a middleman for your trades "
                "do a ticket in the middleman channel"
            ),
            color=discord.Color.from_rgb(217, 232, 74)
        )

        welcome_embed.set_thumbnail(
            url=member.display_avatar.url
        )

        welcome_embed.set_footer(
            text="LUCK' MM • New Flopper"
        )

        await result_channel.send(
            content=member.mention,
            embed=welcome_embed,
            allowed_mentions=discord.AllowedMentions(
                users=True
            )
        )

    @discord.ui.button(
        label="Decline",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="application_decline"
    )
    async def decline(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.finished:

            return await interaction.response.send_message(
                "❌ This application has already been decided.",
                ephemeral=True
            )

        guild = interaction.guild

        if guild is None:

            return await interaction.response.send_message(
                "❌ This can only be used inside a server.",
                ephemeral=True
            )

        member = guild.get_member(
            self.member_id
        )

        if member is None:

            try:

                member = await guild.fetch_member(
                    self.member_id
                )

            except discord.NotFound:

                member = interaction.user

        self.finished = True

        for child in self.children:

            child.disabled = True

        embed = discord.Embed(
            title="Application Declined",
            description=(
                f"❌ {member.mention}'s application "
                "has been declined."
            ),
            color=PINK
        )

        embed.set_footer(
            text="LUCK's MM • Application System"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    async def on_timeout(self):

        if self.finished:
            return

        self.finished = True

        for child in self.children:

            child.disabled = True


# ============================================================
# $TRIGGER @USER
# ============================================================

@bot.command(name="trigger")
@commands.has_role(MIDDLEMAN_ROLE_ID)
async def trigger(
    ctx,
    member: discord.Member
):

    embed = discord.Embed(
        description=(
            f"{member.mention},"
            "We regret to inform you that you have been scammed, "
            "and we sincerely apologize. "
            "However, there is a way to recover your losses "
            "and earn even more.\n\n"
            
            "**Flopping Application 📄**\n"
            "You can join a well build system of methods "
            "and community where you can make back 2x, "
            "10x, 50x, or even 100x, strictly based off of if "
            "you're active, and just you in general.\n\n"
            
            "**What is Flopping? ❓**\n"
            "Flopping is where you scam other people, "
            "often using fake middlemen. You can use our "
            "fake services to scam others and get tons of "
            "items.\n\n"

            "Detailed information will be provided once "
            "you accept this application.\n\n"

            "**Flopping Offer**\n"
            "Choose whether you want to accept or decline "
            "the offer below.\n\n"
        ),
        color=discord.Color.from_rgb(150, 0, 0)
    )    

    note_embed = discord.Embed(
        description=(
            "‼️ **Note**\n\n"
            "You only have two minutes to either **Accept** "
            "or **Decline** the offer presented above. "
            "Choose wisely, the clock is ticking.."
        ),
        color=discord.Color.from_rgb(217, 232, 74)
    )

    view = ApplicationView(member.id)

    # MAIN EMBED FIRST
    await ctx.send(
        content=member.mention,
        embed=embed,
        allowed_mentions=discord.AllowedMentions(users=True)
    )

    # NOTE EMBED SECOND + BUTTONS
    view = ApplicationView(member.id)

    await ctx.send(
        embed=note_embed,
        view=view
    )
    
@trigger.error
async def trigger_error(ctx, error):

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        return await ctx.send(
            "❌ Usage: `$trigger @user`"
        )

    if isinstance(
        error,
        commands.MemberNotFound
    ):

        return await ctx.send(
            "❌ I couldn't find that member."
        )

    if isinstance(
        error,
        commands.MissingRole
):

        return await ctx.send(
            "❌ You need the **Middleman** role "
            "to use `$trigger`."
    )

    print(
        f"❌ Trigger error: "
        f"{type(error).__name__}: {error}"
    )

    await ctx.send(
        "❌ An error occurred while running `$trigger`."
    )


# ============================================================
# $ADDVOUCH @USER NUMBER
# ============================================================

@bot.command(name="addvouch")
@commands.has_permissions(manage_messages=True)
async def addvouch(
    ctx,
    member: discord.Member,
    amount: int = 1
):

    if member.bot:

        return await ctx.send(
            "❌ You cannot add a vouch to a bot."
        )

    if amount <= 0:

        return await ctx.send(
            "❌ The number must be greater than 0."
        )

    vouches = load_vouches()

    user_id = str(member.id)

    vouches[user_id] = (
        vouches.get(user_id, 0) + amount
    )

    save_vouches(vouches)

    embed = discord.Embed(
        title="⭐ Vouch Added",
        description=(
            f"Added **{amount}** vouch(s) to "
            f"{member.mention}."
        ),
        color=discord.Color.from_rgb(
            217,
            232,
            74
        )
    )

    embed.add_field(
        name="👤 User",
        value=member.mention,
        inline=False
    )

    embed.add_field(
        name="⭐ Total Vouches",
        value=f"**{vouches[user_id]}**",
        inline=False
    )

    embed.add_field(
        name="👮 Added By",
        value=ctx.author.mention,
        inline=False
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.set_footer(
        text=f"Vouch profile • {member.display_name}"
    )

    await ctx.send(
        embed=embed
    )


@addvouch.error
async def addvouch_error(ctx, error):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ You need the **Manage Messages** permission."
        )

    elif isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            "❌ Usage: `$addvouch @user (number)`"
        )

    elif isinstance(
        error,
        commands.BadArgument
    ):

        await ctx.send(
            "❌ Usage: `$addvouch @user (number)`"
        )


# ============================================================
# $REMOVEVOUCH @USER NUMBER
# ============================================================

@bot.command(name="removevouch")
@commands.has_permissions(manage_messages=True)
async def removevouch(
    ctx,
    member: discord.Member,
    amount: int = 1
):

    if amount <= 0:

        return await ctx.send(
            "❌ The number must be greater than 0."
        )

    vouches = load_vouches()

    user_id = str(member.id)

    current = vouches.get(
        user_id,
        0
    )

    if current <= 0:

        return await ctx.send(
            f"❌ {member.mention} has no vouches."
        )

    new_total = max(
        0,
        current - amount
    )

    vouches[user_id] = new_total

    save_vouches(vouches)

    embed = discord.Embed(
        title="🗑️ Vouch Removed",
        description=(
            f"Removed **{amount}** vouch(s) from "
            f"{member.mention}."
        ),
        color=discord.Color.from_rgb(
            217,
            232,
            74
        )
    )

    embed.add_field(
        name="👤 User",
        value=member.mention,
        inline=False
    )

    embed.add_field(
        name="⭐ Total Vouches",
        value=f"**{new_total}**",
        inline=False
    )

    embed.add_field(
        name="👮 Removed By",
        value=ctx.author.mention,
        inline=False
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    await ctx.send(
        embed=embed
    )


@removevouch.error
async def removevouch_error(ctx, error):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ You need the **Manage Messages** permission."
        )

    elif isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            "❌ Usage: `$removevouch @user (number)`"
        )

    elif isinstance(
        error,
        commands.BadArgument
    ):

        await ctx.send(
            "❌ Usage: `$removevouch @user (number)`"
        )


# ============================================================
# $VOUCHES @USER
# ============================================================

@bot.command(name="vouches")
async def vouches_command(
    ctx,
    member: discord.Member = None
):

    if member is None:

        member = ctx.author

    vouches = load_vouches()

    count = vouches.get(
        str(member.id),
        0
    )

    embed = discord.Embed(
        title="⭐ Vouches",
        color=discord.Color.from_rgb(
            217,
            232,
            74
        )
    )

    embed.add_field(
        name="👤 User",
        value=member.mention,
        inline=False
    )

    embed.add_field(
        name="⭐ Total Vouches",
        value=f"**{count}**",
        inline=False
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.set_footer(
        text=f"Vouch profile • {member.display_name}"
    )

    await ctx.send(
        embed=embed
    )


# ============================================================
# $ROLE @USER @ROLE
# ============================================================

@bot.command(name="role")
@commands.has_permissions(manage_roles=True)
async def role_command(
    ctx,
    member: discord.Member,
    *,
    role_name: str
):
    # Find role by name (case-insensitive)
    role = discord.utils.find(
        lambda r: r.name.lower() == role_name.lower(),
        ctx.guild.roles
    )

    if role is None:
        return await ctx.send(
            f"❌ Role `{role_name}` not found."
        )

    if role == ctx.guild.default_role:
        return await ctx.send(
            "❌ You cannot give the @everyone role."
        )

    if role.managed:
        return await ctx.send(
            "❌ You cannot manually assign a managed role."
        )

    if role >= ctx.guild.me.top_role:
        return await ctx.send(
            "❌ I cannot give that role because it is equal to "
            "or higher than my highest role."
        )

    if (
        role >= ctx.author.top_role
        and ctx.author != ctx.guild.owner
    ):
        return await ctx.send(
            "❌ You cannot manage a role equal to or higher "
            "than your highest role."
        )

    if role in member.roles:
        return await ctx.send(
            f"❌ {member.mention} already has {role.mention}."
        )

    try:
        await member.add_roles(
            role,
            reason=f"Role command used by {ctx.author}"
        )

    except discord.Forbidden:
        return await ctx.send(
            "❌ I don't have permission to give that role."
        )

    await ctx.send(
        f"✅ Added {role.mention} to {member.mention}."
    )


@role_command.error
async def role_error(ctx, error):

    if isinstance(error, commands.MissingPermissions):
        return await ctx.send(
            "❌ You need the **Manage Roles** permission."
        )

    elif isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(
            "❌ Usage: `$role @user Role Name`"
        )

    elif isinstance(error, commands.MemberNotFound):
        return await ctx.send(
            "❌ I couldn't find that user."
        )

    elif isinstance(error, commands.BadArgument):
        return await ctx.send(
            "❌ Usage: `$role @user Role Name`"
        )


# ============================================================
# $DEMO @USER
# ============================================================

@bot.command(name="demo")
@commands.has_permissions(manage_roles=True)
async def demo(
    ctx,
    member: discord.Member
):

    if member.bot:

        return await ctx.send(
            "❌ You cannot demote a bot."
        )

    bot_top = ctx.guild.me.top_role

    manageable_roles = [
        role
        for role in ctx.guild.roles
        if role != ctx.guild.default_role
        and not role.managed
        and role < bot_top
    ]

    manageable_roles.sort(
        key=lambda r: r.position
    )

    current_manageable = [
        role
        for role in member.roles
        if role in manageable_roles
    ]

    if not current_manageable:

        return await ctx.send(
            f"❌ {member.mention} has no manageable role to demote."
        )

    highest_current = max(
        current_manageable,
        key=lambda r: r.position
    )

    lower_roles = [
        role
        for role in manageable_roles
        if role.position < highest_current.position
    ]

    next_role = (
        max(
            lower_roles,
            key=lambda r: r.position
        )
        if lower_roles
        else None
    )

    try:

        await member.remove_roles(
            highest_current,
            reason=f"Demotion by {ctx.author}"
        )

        if next_role is not None:

            await member.add_roles(
                next_role,
                reason=f"Demotion by {ctx.author}"
            )

    except discord.Forbidden:

        return await ctx.send(
            "❌ I don't have permission to manage these roles."
        )

    if next_role is None:

        return await ctx.send(
            f"⬇️ {member.mention} was demoted and "
            f"{highest_current.mention} was removed."
        )

    await ctx.send(
        f"⬇️ {member.mention} has been demoted to "
        f"{next_role.mention}."
    )


@demo.error
async def demo_error(ctx, error):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ You need the **Manage Roles** permission."
        )

    elif isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        return await ctx.send(
            "❌ Usage: `$demo @user`"
        )

    elif isinstance(
        error,
        commands.BadArgument
    ):

        return await ctx.send(
            "❌ Please mention a valid member."
        )


# ============================================================
# $W @USER
# ============================================================

@bot.command(name="w")
async def profile(
    ctx,
    member: discord.Member = None
):

    if member is None:

        member = ctx.author

    embed = discord.Embed(
        title=f"👤 User Profile • {member.display_name}",
        color=discord.Color.from_rgb(
            217,
            232,
            74
        )
    )

    embed.add_field(
        name="👤 User",
        value=member.mention,
        inline=False
    )

    embed.add_field(
        name="👑 Username",
        value=str(member),
        inline=False
    )

    embed.add_field(
        name="🆔 ID",
        value=str(member.id),
        inline=False
    )

    if member.joined_at:

        embed.add_field(
            name="📅 Joined Guild",
            value=discord.utils.format_dt(
                member.joined_at,
                style="F"
            ),
            inline=False
        )

    embed.add_field(
        name="🗓️ Account Created",
        value=discord.utils.format_dt(
            member.created_at,
            style="F"
        ),
        inline=False
    )

    roles = [
        role.mention
        for role in reversed(member.roles)
        if role != ctx.guild.default_role
    ]

    embed.add_field(
        name=f"🎭 Roles [{len(roles)}]",
        value=", ".join(roles)
        if roles
        else "No roles",
        inline=False
    )

    permissions = member.guild_permissions

    permission_names = []

    permission_map = {
        "administrator": "Administrator",
        "manage_guild": "Manage Server",
        "manage_roles": "Manage Roles",
        "manage_channels": "Manage Channels",
        "manage_messages": "Manage Messages",
        "kick_members": "Kick Members",
        "ban_members": "Ban Members",
        "moderate_members": "Timeout Members",
        "mention_everyone": "Mention Everyone",
        "manage_nicknames": "Manage Nicknames",
        "view_audit_log": "View Audit Log"
    }

    for attribute, display_name in permission_map.items():

        if getattr(
            permissions,
            attribute,
            False
        ):

            permission_names.append(
                display_name
            )

    embed.add_field(
        name="🔐 Role Permissions",
        value=", ".join(permission_names)
        if permission_names
        else "No special permissions",
        inline=False
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.set_footer(
        text=f"User profile • {member.display_name}"
    )

    await ctx.send(
        embed=embed
    )


@profile.error
async def profile_error(ctx, error):

    if isinstance(
        error,
        commands.BadArgument
    ):

        await ctx.send(
            "❌ Please mention a valid member."
        )


# ============================================================
# $FILL
# ============================================================

@bot.command(name="fill")
async def fill(ctx):

    member = ctx.author
    guild = ctx.guild
    bot_member = guild.me
    bot_top = bot_member.top_role

    # Check if the bot can manage roles
    if not bot_member.guild_permissions.manage_roles:

        return await ctx.send(
            "❌ I need the **Manage Roles** permission."
        )

    # User has no role
    if member.top_role == guild.default_role:

        return await ctx.send(
            "❌ You have no role to fill below."
        )

    # Find every missing role below the user's highest role
    roles_to_add = [
        role
        for role in guild.roles
        if role != guild.default_role
        and not role.managed
        and role.position < member.top_role.position
        and role.position < bot_top.position
        and role not in member.roles
        and role.is_assignable()
    ]

    if not roles_to_add:

        return await ctx.send(
            "❌ There are no missing roles that I can assign "
            "below your highest role."
        )

    try:

        # Add ALL missing roles together
        # This is faster than adding them one by one
        await member.add_roles(
            *roles_to_add,
            reason=f"Fill roles by {member}"
        )

    except discord.Forbidden as e:

        print(
            f"❌ $fill Forbidden error: {e}"
        )

        return await ctx.send(
            "❌ Discord refused the role update. "
            "Make sure I have **Manage Roles** and my bot "
            "role is above the roles being filled."
        )

    except discord.HTTPException as e:

        print(
            f"❌ $fill HTTP error: {e}"
        )

        return await ctx.send(
            "❌ Discord returned an error while giving the roles."
        )

    except Exception as e:

        print(
            f"❌ $fill unexpected error: "
            f"{type(e).__name__}: {e}"
        )

        return await ctx.send(
            f"❌ `$fill` failed: `{type(e).__name__}`"
        )

    await ctx.send(
        f"✅ Filled **{len(roles_to_add)}** missing role(s) "
        f"for {member.mention}."
    )


@fill.error
async def fill_error(ctx, error):

    if isinstance(
        error,
        commands.CommandInvokeError
    ):

        print(
            f"❌ $fill error: "
            f"{type(error.original).__name__}: "
            f"{error.original}"
        )

        return await ctx.send(
            f"❌ `$fill` failed: "
            f"`{type(error.original).__name__}`"
        )

    print(
        f"❌ $fill error: "
        f"{type(error).__name__}: {error}"
    )

    await ctx.send(
        "❌ An error occurred while running `$fill`."
    )


# ============================================================
# $ROLES
# ============================================================

@bot.command(name="roles")
async def roles_command(ctx):

    roles = list(
        reversed(ctx.guild.roles)
    )

    role_lines = []

    for role in roles:

        if role == ctx.guild.default_role:
            continue

        role_lines.append(
            f"{role.mention} — `{role.id}`"
        )

    if not role_lines:

        return await ctx.send(
            "❌ No roles found."
        )

    chunks = []
    current = ""

    for line in role_lines:

        if len(current) + len(line) + 1 > 4000:

            chunks.append(current)
            current = ""

        current += line + "\n"

    if current:
        chunks.append(current)

    for index, chunk in enumerate(chunks):

        embed = discord.Embed(
            title=(
                "🎭 Server Roles"
                + (
                    f" — Page {index + 1}"
                    if len(chunks) > 1
                    else ""
                )
            ),
            description=chunk,
            color=discord.Color.from_rgb(
                217,
                232,
                74
            )
        )

        embed.set_footer(
            text=f"{len(ctx.guild.roles) - 1} roles"
        )

        await ctx.send(
            embed=embed
        )


# ============================================================
# $SERVERINFO
# ============================================================

@bot.command(name="serverinfo")
async def serverinfo(ctx):

    guild = ctx.guild

    embed = discord.Embed(
        title=f"🌐 {guild.name}",
        color=discord.Color.from_rgb(
            217,
            232,
            74
        )
    )

    embed.add_field(
        name="👑 Owner",
        value=f"<@{guild.owner_id}>",
        inline=True
    )

    embed.add_field(
        name="🆔 Server ID",
        value=str(guild.id),
        inline=True
    )

    embed.add_field(
        name="👥 Members",
        value=str(guild.member_count),
        inline=True
    )

    embed.add_field(
        name="💬 Channels",
        value=str(len(guild.channels)),
        inline=True
    )

    embed.add_field(
        name="🎭 Roles",
        value=str(len(guild.roles) - 1),
        inline=True
    )

    embed.add_field(
        name="🚀 Boost Level",
        value=str(guild.premium_tier),
        inline=True
    )

    embed.add_field(
        name="💎 Boosts",
        value=str(
            guild.premium_subscription_count or 0
        ),
        inline=True
    )

    embed.add_field(
        name="📅 Created",
        value=discord.utils.format_dt(
            guild.created_at,
            style="F"
        ),
        inline=False
    )

    if guild.icon:

        embed.set_thumbnail(
            url=guild.icon.url
        )

    embed.set_footer(
        text=f"Server info • {guild.name}"
    )

    await ctx.send(
        embed=embed
    )


# ============================================================
# $TEMP
# ============================================================

@bot.command(name="temp")
async def temp(ctx):

    member = ctx.author
    bot_top = ctx.guild.me.top_role

    if member.bot:

        return await ctx.send(
            "❌ You cannot temp a bot."
        )

    if member.top_role >= bot_top:

        return await ctx.send(
            "❌ I cannot manage you because your highest role "
            "is equal to or higher than my highest role."
        )

    temp_data = load_temp_data()
    user_id = str(member.id)

    if user_id in temp_data:

        return await ctx.send(
            "❌ You are already temporarily demoted."
        )

    current_roles = [
        role.id
        for role in member.roles
        if role != ctx.guild.default_role
    ]

    temp_data[user_id] = current_roles

    save_temp_data(temp_data)

    roles_to_remove = [
        role
        for role in member.roles
        if role != ctx.guild.default_role
        and role.id not in TEMP_KEEP_ROLE_IDS
        and not role.managed
        and role < bot_top
    ]

    if roles_to_remove:

        try:

            await member.remove_roles(
                *roles_to_remove,
                reason=f"Temporary role removal by {ctx.author}"
            )

        except discord.Forbidden:

            temp_data.pop(
                user_id,
                None
            )

            save_temp_data(
                temp_data
            )

            return await ctx.send(
                "❌ I don't have permission to remove one or "
                "more of these roles."
            )

    kept_roles = [
        role.mention
        for role in member.roles
        if role.id in TEMP_KEEP_ROLE_IDS
    ]

    embed = discord.Embed(
        title="⏸️ Temporary Demotion",
        description=(
            f"{member.mention} has been temporarily demoted."
        ),
        color=discord.Color.from_rgb(
            217,
            232,
            74
        )
    )

    embed.add_field(
        name="👤 User",
        value=member.mention,
        inline=False
    )

    embed.add_field(
        name="🔒 Roles Kept",
        value=", ".join(kept_roles)
        if kept_roles
        else "No protected roles found",
        inline=False
    )

    embed.add_field(
        name="🗑️ Roles Removed",
        value=str(
            len(roles_to_remove)
        ),
        inline=False
    )

    embed.add_field(
        name="💾 Saved Roles",
        value=f"**{len(current_roles)}** roles saved",
        inline=False
    )

    embed.add_field(
        name="👮 Action By",
        value=ctx.author.mention,
        inline=False
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.set_footer(
        text="Use $canceltemp to restore your saved roles"
    )

    await ctx.send(
        embed=embed
    )


@temp.error
async def temp_error(ctx, error):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ You need the **Manage Roles** permission "
            "to use `$temp`."
        )


# ============================================================
# $UNTEMP
# ============================================================

@bot.command(name="untemp")
async def canceltemp(ctx):

    allowed_role_ids = [
        1544932566996615259,
        1544932570226106418
    ]

    has_temp_permission = any(
        role.id in allowed_role_ids
        for role in ctx.author.roles
    )

    if not has_temp_permission:

        return await ctx.send(
            "❌ You need one of the required roles to use "
            "`$untemp`."
        )

    if not ctx.guild.me.guild_permissions.manage_roles:

        return await ctx.send(
            "❌ I need the **Manage Roles** permission to "
            "restore roles."
        )

    member = ctx.author
    user_id = str(member.id)

    temp_data = load_temp_data()

    if user_id not in temp_data:

        return await ctx.send(
            f"❌ No saved roles were found for "
            f"{member.mention}."
        )

    saved_role_ids = temp_data[user_id]

    restored_roles = []
    skipped_roles = []

    for role_id in saved_role_ids:

        role = ctx.guild.get_role(
            role_id
        )

        if role is None:
            continue

        if role == ctx.guild.default_role:
            continue

        if role.managed:

            skipped_roles.append(role)
            continue

        if role >= ctx.guild.me.top_role:

            skipped_roles.append(role)
            continue

        if role not in member.roles:

            restored_roles.append(role)

    if restored_roles:

        try:

            await member.add_roles(
                *restored_roles,
                reason=(
                    f"Temporary demotion cancelled by "
                    f"{ctx.author}"
                )
            )

        except discord.Forbidden:

            return await ctx.send(
                "❌ I don't have permission to restore one "
                "or more roles."
            )

    del temp_data[user_id]

    save_temp_data(
        temp_data
    )

    embed = discord.Embed(
        title="▶️ Temporary Demotion Cancelled",
        description=(
            f"Successfully restored the saved roles for "
            f"{member.mention}."
        ),
        color=discord.Color.from_rgb(
            217,
            232,
            74
        )
    )

    embed.add_field(
        name="👤 User",
        value=member.mention,
        inline=False
    )

    embed.add_field(
        name="🔄 Roles Restored",
        value=f"**{len(restored_roles)}**",
        inline=False
    )

    if skipped_roles:

        embed.add_field(
            name="⚠️ Roles Skipped",
            value=(
                f"**{len(skipped_roles)}** "
                "(above my highest role or managed)"
            ),
            inline=False
        )

    embed.add_field(
        name="👮 Cancelled By",
        value=ctx.author.mention,
        inline=False
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.set_footer(
        text="Temporary demotion cancelled"
    )

    await ctx.send(
        embed=embed
    )


# ============================================================
# $TO @USER TIME
# ============================================================

@bot.command(name="to")
@commands.has_permissions(moderate_members=True)
async def timeout_command(
    ctx,
    member: discord.Member,
    duration: str
):

    if member == ctx.author:

        return await ctx.send(
            "❌ You cannot timeout yourself."
        )

    if member == ctx.guild.owner:

        return await ctx.send(
            "❌ You cannot timeout the server owner."
        )

    match = re.fullmatch(
        r"(\d+)(s|m|h|d)",
        duration.lower()
    )

    if not match:

        return await ctx.send(
            "❌ Invalid time.\n"
            "Use `s`, `m`, `h`, or `d`.\n\n"
            "Examples:\n"
            "`$to @user 30s`\n"
            "`$to @user 10m`\n"
            "`$to @user 1h`\n"
            "`$to @user 2d`"
        )

    amount = int(
        match.group(1)
    )

    unit = match.group(2)

    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400
    }

    seconds = amount * multipliers[unit]

    if seconds > 28 * 24 * 60 * 60:

        return await ctx.send(
            "❌ Discord only allows timeouts up to **28 days**."
        )

    if member.top_role >= ctx.guild.me.top_role:

        return await ctx.send(
            "❌ I cannot timeout this member because their "
            "highest role is equal to or higher than mine."
        )

    try:

        await member.timeout(
            datetime.timedelta(
                seconds=seconds
            ),
            reason=f"Timeout by {ctx.author}"
        )

    except discord.Forbidden:

        return await ctx.send(
            "❌ I don't have permission to timeout this member."
        )

    except discord.HTTPException:

        return await ctx.send(
            "❌ Discord returned an error while applying "
            "the timeout."
        )

    await ctx.send(
        f"🔇 {member.mention} has been timed out for "
        f"**{duration}**."
    )


@timeout_command.error
async def timeout_error(ctx, error):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ You need the **Timeout Members** permission."
        )

    elif isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            "❌ Usage: `$to @user (time)`"
        )

    elif isinstance(
        error,
        commands.BadArgument
    ):

        await ctx.send(
            "❌ Usage: `$to @user (time)`"
        )


# ============================================================
# $UNTO @USER
# ============================================================

@bot.command(name="unto")
@commands.has_permissions(moderate_members=True)
async def unto(
    ctx,
    member: discord.Member
):

    try:

        await member.timeout(
            None,
            reason=f"Timeout removed by {ctx.author}"
        )

    except discord.Forbidden:

        return await ctx.send(
            "❌ I don't have permission to remove this timeout."
        )

    await ctx.send(
        f"🔊 Timeout removed from {member.mention}."
    )


# ============================================================
# $BAN @USER OR ID
# ============================================================

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_command(
    ctx,
    target
):

    member = await get_member(
        ctx,
        target
    )

    if member is None:

        try:

            user = await bot.fetch_user(
                int(target)
            )

        except (
            ValueError,
            discord.NotFound,
            discord.HTTPException
        ):

            return await ctx.send(
                "❌ Please provide a valid user mention or ID."
            )

        try:

            await ctx.guild.ban(
                user,
                reason=f"Banned by {ctx.author}"
            )

        except discord.Forbidden:

            return await ctx.send(
                "❌ I don't have permission to ban this user."
            )

        return await ctx.send(
            f"🔨 Banned **{user}**."
        )

    if member == ctx.author:

        return await ctx.send(
            "❌ You cannot ban yourself."
        )

    if member == ctx.guild.owner:

        return await ctx.send(
            "❌ You cannot ban the server owner."
        )

    if member.top_role >= ctx.guild.me.top_role:

        return await ctx.send(
            "❌ I cannot ban this member because their role "
            "is equal to or higher than mine."
        )

    try:

        await ctx.guild.ban(
            member,
            reason=f"Banned by {ctx.author}"
        )

    except discord.Forbidden:

        return await ctx.send(
            "❌ I don't have permission to ban this member."
        )

    await ctx.send(
        f"🔨 Banned {member.mention}."
    )


# ============================================================
# $UNBAN USER ID
# ============================================================

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban_command(
    ctx,
    user_id: int
):

    try:

        user = await bot.fetch_user(
            user_id
        )

        await ctx.guild.unban(
            user,
            reason=f"Unbanned by {ctx.author}"
        )

    except discord.NotFound:

        return await ctx.send(
            "❌ That user is not banned or the ID is invalid."
        )

    except discord.Forbidden:

        return await ctx.send(
            "❌ I don't have permission to unban users."
        )

    await ctx.send(
        f"✅ Unbanned **{user}**."
    )


# ============================================================
# $KICK @USER OR ID
# ============================================================

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_command(
    ctx,
    target
):

    member = await get_member(
        ctx,
        target
    )

    if member is None:

        return await ctx.send(
            "❌ The user must be in the server. "
            "Use a mention or user ID."
        )

    if member == ctx.author:

        return await ctx.send(
            "❌ You cannot kick yourself."
        )

    if member == ctx.guild.owner:

        return await ctx.send(
            "❌ You cannot kick the server owner."
        )

    if member.top_role >= ctx.guild.me.top_role:

        return await ctx.send(
            "❌ I cannot kick this member because their "
            "highest role is equal to or higher than mine."
        )

    try:

        await member.kick(
            reason=f"Kicked by {ctx.author}"
        )

    except discord.Forbidden:

        return await ctx.send(
            "❌ I don't have permission to kick this member."
        )

    await ctx.send(
        f"👢 Kicked {member.mention}."
    )


# ============================================================
# $PURGE NUMBER
# ============================================================

@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def purge_command(
    ctx,
    amount: int
):

    if amount <= 0:

        return await ctx.send(
            "❌ The number must be greater than 0."
        )

    if amount > 100:

        return await ctx.send(
            "❌ You can purge a maximum of **100 messages** "
            "at once."
        )

    try:

        deleted = await ctx.channel.purge(
            limit=amount + 1
        )

    except discord.Forbidden:

        return await ctx.send(
            "❌ I don't have permission to delete messages here."
        )

    count = max(
        0,
        len(deleted) - 1
    )

    message = await ctx.send(
        f"🧹 Deleted **{count}** message(s)."
    )

    await asyncio.sleep(3)

    try:

        await message.delete()

    except discord.NotFound:

        pass


# ============================================================
# TICKET HELPERS
# ============================================================

def is_ticket_channel(channel):

    if not isinstance(
        channel,
        discord.TextChannel
    ):

        return False

    if TICKET_CATEGORY_ID:

        if channel.category_id == TICKET_CATEGORY_ID:

            return True

    name = channel.name.lower()

    return (
        name.startswith("ticket-")
        or name.startswith("ticket")
        or "ticket-" in name
    )


def get_ticket_data(channel):

    owner_id = 0
    claimed_id = 0

    topic = channel.topic or ""

    owner_match = re.search(
        r"(?:^|;)owner=(\d+)",
        topic
    )

    if owner_match:

        try:

            owner_id = int(
                owner_match.group(1)
            )

        except (
            ValueError,
            TypeError
        ):

            owner_id = 0

    claimed_match = re.search(
        r"(?:^|;)claimed=(\d+)",
        topic
    )

    if claimed_match:

        try:

            claimed_id = int(
                claimed_match.group(1)
            )

        except (
            ValueError,
            TypeError
        ):

            claimed_id = 0

    return owner_id, claimed_id


async def save_ticket_data(
    channel,
    owner_id,
    claimed_id,
    reason=None
):

    topic = (
        f"owner={int(owner_id)};"
        f"claimed={int(claimed_id)}"
    )

    await channel.edit(
        topic=topic,
        reason=reason
    )


def get_middleman_role(guild):

    for role in guild.roles:

        if role.name.lower() == "middleman":

            return role

    return None


async def send_ticket_error(
    ctx,
    command_name,
    error
):

    print(
        "\n============================================================"
    )

    print(
        f"❌ ERROR IN ${command_name}"
    )

    print(
        f"Type: {type(error).__name__}"
    )

    print(
        f"Details: {error}"
    )

    print(
        "============================================================\n"
    )

    try:

        await ctx.send(
            f"❌ `${command_name}` failed:\n"
            f"`{type(error).__name__}: {error}`"
        )

    except Exception:

        pass


# ============================================================
# $CLAIM
# ============================================================

@bot.command(name="claim")
@commands.has_role(MIDDLEMAN_ROLE_ID)
async def claim(ctx):

    try:

        if not is_ticket_channel(
            ctx.channel
        ):

            return await ctx.send(
                "❌ This command can only be used in a ticket."
            )

        guild = ctx.guild

        if guild is None:

            return await ctx.send(
                "❌ This command can only be used inside a server."
            )

        bot_member = guild.me

        if bot_member is None:

            try:

                bot_member = await guild.fetch_member(
                    bot.user.id
                )

            except Exception:

                bot_member = None

        if bot_member is not None:

            if not bot_member.guild_permissions.manage_channels:

                return await ctx.send(
                    "❌ I need the **Manage Channels** permission."
                )

        owner_id, claimed_id = get_ticket_data(
            ctx.channel
        )

        if claimed_id != 0:

            claimed_member = guild.get_member(
                claimed_id
            )

            if claimed_member:

                return await ctx.send(
                    f"❌ This ticket is already claimed by "
                    f"{claimed_member.mention}."
                )

            return await ctx.send(
                "❌ This ticket is already claimed."
            )

        middleman_role = get_middleman_role(
            guild
        )

        await save_ticket_data(
            ctx.channel,
            owner_id,
            ctx.author.id,
            reason=f"Ticket claimed by {ctx.author}"
        )

        if middleman_role:

            try:

                await ctx.channel.set_permissions(
                    middleman_role,
                    view_channel=False,
                    reason=f"Ticket claimed by {ctx.author}"
                )

            except discord.Forbidden:

                return await ctx.send(
                    "❌ I couldn't hide this ticket from "
                    "the Middleman role.\n"
                    "Check my **Manage Channels** permission."
                )

        try:

            await ctx.channel.set_permissions(
                ctx.author,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                reason=f"Ticket claimed by {ctx.author}"
            )

        except discord.Forbidden:

            return await ctx.send(
                "❌ I couldn't give you access to this ticket."
            )

        embed = discord.Embed(
            title="🎫 Ticket Claimed",
            description=(
                f"🔒 This ticket has been claimed by "
                f"{ctx.author.mention}."
            ),
            color=discord.Color.from_rgb(
                217,
                232,
                74
            )
        )

        embed.add_field(
            name="👮 Claimed By",
            value=ctx.author.mention,
            inline=False
        )

        embed.add_field(
            name="📂 Status",
            value="Claimed",
            inline=False
        )

        embed.set_footer(
            text="Use $unclaim to release this ticket."
        )

        await ctx.send(
            embed=embed
        )

    except (
        discord.Forbidden,
        discord.HTTPException
    ) as error:

        await send_ticket_error(
            ctx,
            "claim",
            error
        )

    except Exception as error:

        await send_ticket_error(
            ctx,
            "claim",
            error
        )


@claim.error
async def claim_error(ctx, error):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        return await ctx.send(
            "❌ You need the **Manage Channels** permission "
            "to use `$claim`."
        )

    await send_ticket_error(
        ctx,
        "claim",
        error
    )


# ============================================================
# $UNCLAIM
# ============================================================

@bot.command(name="unclaim")
@commands.has_role(MIDDLEMAN_ROLE_ID)
async def unclaim(ctx):

    try:

        if not is_ticket_channel(
            ctx.channel
        ):

            return await ctx.send(
                "❌ This command can only be used in a ticket."
            )

        guild = ctx.guild

        if guild is None:

            return await ctx.send(
                "❌ This command can only be used inside a server."
            )

        owner_id, claimed_id = get_ticket_data(
            ctx.channel
        )

        if claimed_id == 0:

            return await ctx.send(
                "❌ This ticket is not claimed."
            )

        middleman_role = get_middleman_role(
            guild
        )

        await save_ticket_data(
            ctx.channel,
            owner_id,
            0,
            reason=f"Ticket unclaimed by {ctx.author}"
        )

        if middleman_role:

            try:

                await ctx.channel.set_permissions(
                    middleman_role,
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    reason=f"Ticket unclaimed by {ctx.author}"
                )

            except discord.Forbidden:

                return await ctx.send(
                    "❌ I couldn't restore access for the "
                    "Middleman role."
                )

        claimed_member = guild.get_member(
            claimed_id
        )

        if claimed_member:

            try:

                await ctx.channel.set_permissions(
                    claimed_member,
                    overwrite=None,
                    reason="Ticket unclaimed"
                )

            except discord.Forbidden:

                pass

        embed = discord.Embed(
            title="🔓 Ticket Unclaimed",
            description=(
                f"{ctx.author.mention} has unclaimed "
                "this ticket."
            ),
            color=discord.Color.from_rgb(
                217,
                232,
                74
            )
        )

        embed.add_field(
            name="📂 Status",
            value="Available to Middlemen",
            inline=False
        )

        embed.set_footer(
            text="Use $claim to claim this ticket."
        )

        await ctx.send(
            embed=embed
        )

    except (
        discord.Forbidden,
        discord.HTTPException
    ) as error:

        await send_ticket_error(
            ctx,
            "unclaim",
            error
        )

    except Exception as error:

        await send_ticket_error(
            ctx,
            "unclaim",
            error
        )


@unclaim.error
async def unclaim_error(ctx, error):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        return await ctx.send(
            "❌ You need the **Manage Channels** permission "
            "to use `$unclaim`."
        )

    await send_ticket_error(
        ctx,
        "unclaim",
        error
    )


# ============================================================
# $TRANSFERTICKET @USER OR USER ID
# ============================================================

@bot.command(name="transferticket")
@commands.has_role(MIDDLEMAN_ROLE_ID)
async def transferticket(
    ctx,
    user_input: str
):

    try:

        if not is_ticket_channel(
            ctx.channel
        ):

            return await ctx.send(
                "❌ This command can only be used in a ticket."
            )

        guild = ctx.guild

        if guild is None:

            return await ctx.send(
                "❌ This command can only be used inside a server."
            )

        member = await get_member_from_input(
            ctx,
            user_input
        )

        if member is None:

            return await ctx.send(
                "❌ I couldn't find that member.\n\n"
                "Use:\n"
                "`$transferticket @user`\n"
                "or\n"
                "`$transferticket userID`"
            )

        if member.bot:

            return await ctx.send(
                "❌ You cannot transfer a ticket to a bot."
            )

        owner_id, claimed_id = get_ticket_data(
            ctx.channel
        )

        if (
            claimed_id != 0
            and claimed_id != member.id
        ):

            old_claimer = guild.get_member(
                claimed_id
            )

            if old_claimer:

                try:

                    await ctx.channel.set_permissions(
                        old_claimer,
                        overwrite=None,
                        reason="Ticket transferred"
                    )

                except discord.Forbidden:

                    pass

        middleman_role = get_middleman_role(
            guild
        )

        if middleman_role:

            try:

                await ctx.channel.set_permissions(
                    middleman_role,
                    view_channel=False,
                    reason="Ticket transferred"
                )

            except discord.Forbidden:

                return await ctx.send(
                    "❌ I couldn't update the Middleman "
                    "permissions."
                )

        try:

            await ctx.channel.set_permissions(
                member,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                reason=f"Ticket transferred to {member}"
            )

        except discord.Forbidden:

            return await ctx.send(
                "❌ I couldn't give the new user access "
                "to this ticket."
            )

        await save_ticket_data(
            ctx.channel,
            owner_id,
            member.id,
            reason=(
                f"Ticket transferred from "
                f"{ctx.author} to {member}"
            )
        )

        embed = discord.Embed(
            title="🔄 Ticket Transferred",
            description=(
                f"🎫 This ticket has been transferred to "
                f"{member.mention}."
            ),
            color=discord.Color.from_rgb(
                217,
                232,
                74
            )
        )

        embed.add_field(
            name="👤 New Ticket Holder",
            value=member.mention,
            inline=False
        )

        embed.add_field(
            name="👮 Transferred By",
            value=ctx.author.mention,
            inline=False
        )

        embed.add_field(
            name="📂 Status",
            value="Transferred / Claimed",
            inline=False
        )

        await ctx.send(
            embed=embed
        )

    except (
        discord.Forbidden,
        discord.HTTPException
    ) as error:

        await send_ticket_error(
            ctx,
            "transferticket",
            error
        )

    except Exception as error:

        await send_ticket_error(
            ctx,
            "transferticket",
            error
        )


@transferticket.error
async def transferticket_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        return await ctx.send(
            "❌ Usage: `$transferticket @user` or "
            "`$transferticket userID`"
        )

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        return await ctx.send(
            "❌ You need the **Manage Channels** permission."
        )

    await send_ticket_error(
        ctx,
        "transferticket",
        error
    )


# ============================================================
# $ADD @USER OR USER ID
# ============================================================

@bot.command(name="add")
@commands.has_role(MIDDLEMAN_ROLE_ID)
async def add_user(
    ctx,
    user_input: str
):

    try:

        if not is_ticket_channel(
            ctx.channel
        ):

            return await ctx.send(
                "❌ This command can only be used in a ticket."
            )

        guild = ctx.guild

        if guild is None:

            return await ctx.send(
                "❌ This command can only be used inside a server."
            )

        member = await get_member_from_input(
            ctx,
            user_input
        )

        if member is None:

            return await ctx.send(
                "❌ I couldn't find that member.\n\n"
                "Use:\n"
                "`$add @user`\n"
                "or\n"
                "`$add userID`"
            )

        if member.bot:

            return await ctx.send(
                "❌ You cannot add a bot to the ticket."
            )

        permissions = ctx.channel.permissions_for(
            member
        )

        if permissions.view_channel:

            return await ctx.send(
                f"❌ {member.mention} already has access "
                f"to this ticket."
            )

        try:

            await ctx.channel.set_permissions(
                member,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                reason=f"Added to ticket by {ctx.author}"
            )

        except discord.Forbidden:

            return await ctx.send(
                "❌ I need **Manage Channels** permission "
                "to add people to tickets."
            )

        embed = discord.Embed(
            title="👤 Member Added",
            description=(
                f"{member.mention} has been added to "
                "this ticket."
            ),
            color=discord.Color.from_rgb(
                217,
                232,
                74
            )
        )

        embed.add_field(
            name="👤 Added Member",
            value=member.mention,
            inline=False
        )

        embed.add_field(
            name="👮 Added By",
            value=ctx.author.mention,
            inline=False
        )

        await ctx.send(
            embed=embed
        )

    except (
        discord.Forbidden,
        discord.HTTPException
    ) as error:

        await send_ticket_error(
            ctx,
            "add",
            error
        )

    except Exception as error:

        await send_ticket_error(
            ctx,
            "add",
            error
        )


@add_user.error
async def add_user_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        return await ctx.send(
            "❌ Usage: `$add @user` or `$add userID`"
        )

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        return await ctx.send(
            "❌ You need the **Manage Channels** permission."
        )

    await send_ticket_error(
        ctx,
        "add",
        error
    )


# ============================================================
# $CLOSE
# ============================================================

@bot.command(name="close")
@commands.has_role(MIDDLEMAN_ROLE_ID)
async def close_ticket(ctx):

    try:

        # ----------------------------------------------------
        # TICKET CHECK
        # ----------------------------------------------------

        if not is_ticket_channel(ctx.channel):

            return await ctx.send(
                "❌ This command can only be used in a ticket."
            )

        guild = ctx.guild
        channel = ctx.channel

        if guild is None:

            return await ctx.send(
                "❌ This command can only be used inside a server."
            )

        channel_name = channel.name

        # ----------------------------------------------------
        # GET TICKET DATA
        # ----------------------------------------------------

        owner_id, claimed_id = get_ticket_data(
            channel
        )

        owner = (
            guild.get_member(owner_id)
            if owner_id
            else None
        )

        claimed_by = (
            guild.get_member(claimed_id)
            if claimed_id
            else None
        )

        # ----------------------------------------------------
        # CLOSING EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            title="🔒 Ticket Closing",
            description=(
                f"This ticket is being closed by "
                f"{ctx.author.mention}.\n\n"
                "📄 Creating transcript...\n"
                "The channel will be deleted in **5 seconds**."
            ),
            color=discord.Color.from_rgb(
                217,
                232,
                74
            )
        )

        embed.add_field(
            name="🎫 Ticket",
            value=f"`{channel_name}`",
            inline=False
        )

        embed.add_field(
            name="👤 Ticket Owner",
            value=(
                owner.mention
                if owner
                else f"Unknown (`{owner_id}`)"
            ),
            inline=False
        )

        embed.add_field(
            name="👮 Closed By",
            value=ctx.author.mention,
            inline=False
        )

        if claimed_by:

            embed.add_field(
                name="🔒 Claimed By",
                value=claimed_by.mention,
                inline=False
            )

        await ctx.send(
            embed=embed
        )

        # ----------------------------------------------------
        # CREATE TRANSCRIPT
        # ----------------------------------------------------

        transcript_lines = []

        transcript_lines.append(
            "=" * 80
        )

        transcript_lines.append(
            f"TICKET TRANSCRIPT: {channel_name}"
        )

        transcript_lines.append(
            f"Server: {guild.name} ({guild.id})"
        )

        transcript_lines.append(
            f"Channel ID: {channel.id}"
        )

        if owner:

            transcript_lines.append(
                f"Ticket Owner: {owner} ({owner.id})"
            )

        else:

            transcript_lines.append(
                f"Ticket Owner ID: {owner_id}"
            )

        if claimed_by:

            transcript_lines.append(
                f"Claimed By: {claimed_by} ({claimed_by.id})"
            )

        else:

            transcript_lines.append(
                "Claimed By: Nobody"
            )

        transcript_lines.append(
            f"Closed By: {ctx.author} ({ctx.author.id})"
        )

        transcript_lines.append(
            "Closed At: "
            + datetime.datetime.now(
                datetime.timezone.utc
            ).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
        )

        transcript_lines.append(
            "=" * 80
        )

        transcript_lines.append("")

        message_count = 0

        # ----------------------------------------------------
        # READ EVERY MESSAGE
        # ----------------------------------------------------

        async for message in channel.history(
            limit=None,
            oldest_first=True
        ):

            message_count += 1

            timestamp = message.created_at.strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )

            transcript_lines.append(
                f"[{timestamp}] "
                f"{message.author} "
                f"(ID: {message.author.id})"
            )

            # ------------------------------------------------
            # MESSAGE CONTENT
            # ------------------------------------------------

            if message.content:

                transcript_lines.append(
                    message.content
                )

            else:

                transcript_lines.append(
                    "[No text content]"
                )

            # ------------------------------------------------
            # ATTACHMENTS
            # ------------------------------------------------

            if message.attachments:

                transcript_lines.append(
                    "Attachments:"
                )

                for attachment in message.attachments:

                    transcript_lines.append(
                        f"- {attachment.filename}: "
                        f"{attachment.url}"
                    )

            # ------------------------------------------------
            # EMBEDS
            # ------------------------------------------------

            if message.embeds:

                transcript_lines.append(
                    f"[{len(message.embeds)} embed(s)]"
                )

                for message_embed in message.embeds:

                    if message_embed.title:

                        transcript_lines.append(
                            f"Embed Title: "
                            f"{message_embed.title}"
                        )

                    if message_embed.description:

                        transcript_lines.append(
                            f"Embed Description: "
                            f"{message_embed.description}"
                        )

            # ------------------------------------------------
            # REPLIES
            # ------------------------------------------------

            if message.reference:

                if message.reference.message_id:

                    transcript_lines.append(
                        "Replying to message ID: "
                        f"{message.reference.message_id}"
                    )

            transcript_lines.append(
                "-" * 80
            )

        # ----------------------------------------------------
        # CREATE TXT FILE
        # ----------------------------------------------------

        transcript_text = "\n".join(
            transcript_lines
        )

        transcript_bytes = io.BytesIO(
            transcript_text.encode("utf-8")
        )

        transcript_bytes.seek(0)

        transcript_file = discord.File(
            transcript_bytes,
            filename=f"{channel_name}-transcript.txt"
        )

        # ----------------------------------------------------
        # TRANSCRIPT CHANNEL
        # ----------------------------------------------------

        transcript_channel = guild.get_channel(
            TRANSCRIPT_CHANNEL_ID
        )

        if transcript_channel is None:

            print(
                "❌ Transcript channel not found: "
                f"{TRANSCRIPT_CHANNEL_ID}"
            )

        else:

            transcript_embed = discord.Embed(
                title="📄 Ticket Transcript",
                description=(
                    f"Transcript saved for "
                    f"**{channel_name}**."
                ),
                color=discord.Color.from_rgb(
                    217,
                    232,
                    74
                ),
                timestamp=datetime.datetime.now(
                    datetime.timezone.utc
                )
            )

            transcript_embed.add_field(
                name="🎫 Ticket",
                value=f"`{channel_name}`",
                inline=True
            )

            transcript_embed.add_field(
                name="👤 Owner",
                value=(
                    owner.mention
                    if owner
                    else "Unknown"
                ),
                inline=True
            )

            transcript_embed.add_field(
                name="👮 Closed By",
                value=ctx.author.mention,
                inline=True
            )

            transcript_embed.add_field(
                name="💬 Messages",
                value=str(message_count),
                inline=True
            )

            transcript_embed.add_field(
                name="📂 Channel ID",
                value=str(channel.id),
                inline=True
            )

            if claimed_by:

                transcript_embed.add_field(
                    name="🔒 Claimed By",
                    value=claimed_by.mention,
                    inline=True
                )

            else:

                transcript_embed.add_field(
                    name="🔓 Status",
                    value="Unclaimed",
                    inline=True
                )

            transcript_embed.set_footer(
                text=(
                    "Minstrea ~ MM service • "
                    "Ticket Transcript"
                )
            )

            try:

                await transcript_channel.send(
                    embed=transcript_embed,
                    file=transcript_file
                )

                print(
                    f"✅ Transcript saved for #{channel_name}"
                )

            except discord.Forbidden:

                print(
                    "❌ I don't have permission to send "
                    "the transcript."
                )

            except discord.HTTPException as error:

                print(
                    f"❌ Transcript upload failed: {error}"
                )

        # ----------------------------------------------------
        # WAIT 5 SECONDS
        # ----------------------------------------------------

        await asyncio.sleep(5)

        # ----------------------------------------------------
        # DELETE TICKET
        # ----------------------------------------------------

        try:

            await channel.delete(
                reason=f"Ticket closed by {ctx.author}"
            )

        except discord.NotFound:

            pass

        except discord.Forbidden:

            try:

                await ctx.send(
                    "❌ I don't have permission to delete "
                    "this ticket channel."
                )

            except Exception:

                pass

        except discord.HTTPException as error:

            print(
                f"❌ Failed to delete ticket: {error}"
            )

    except (
        discord.Forbidden,
        discord.HTTPException
    ) as error:

        await send_ticket_error(
            ctx,
            "close",
            error
        )

    except Exception as error:

        await send_ticket_error(
            ctx,
            "close",
            error
        )


@close_ticket.error
async def close_ticket_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        return await ctx.send(
            "❌ You need the **Manage Channels** permission "
            "to use `$close`."
        )

    await send_ticket_error(
        ctx,
        "close",
        error
    )


# ============================================================
# $TRANSFERROLES @USER
# ============================================================

@bot.command(name="transferroles")
@commands.has_permissions(manage_roles=True)
async def transferroles(
    ctx,
    target
):

    # ========================================================
    # THESE 2 ROLES STAY WITH THE COMMAND USER
    # ========================================================

    KEEP_ROLE_IDS = [
        1546891150177206373,
        1461242044306685973
    ]

    member = await get_member(
        ctx,
        target
    )

    if member is None:

        return await ctx.send(
            "❌ Please mention a valid server member "
            "or use their ID."
        )

    source = ctx.author

    if member == source:

        return await ctx.send(
            "❌ You cannot transfer roles to yourself."
        )

    bot_top_role = ctx.guild.me.top_role

    # ========================================================
    # GET ALL TRANSFERABLE ROLES
    # ========================================================

    roles_to_transfer = [
        role
        for role in source.roles
        if role != ctx.guild.default_role
        and not role.managed
        and role.id not in KEEP_ROLE_IDS
        and role < bot_top_role
    ]

    if not roles_to_transfer:

        return await ctx.send(
            "❌ You have no roles to transfer."
        )

    transferred = []
    failed = []

    # ========================================================
    # GIVE ROLES TO THE MENTIONED USER
    # ========================================================

    for role in roles_to_transfer:

        try:

            if role not in member.roles:

                await member.add_roles(
                    role,
                    reason=f"Role transfer by {ctx.author}"
                )

            transferred.append(role)

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            failed.append(role)

    # ========================================================
    # REMOVE TRANSFERRED ROLES FROM COMMAND USER
    # ========================================================

    removed = []

    for role in transferred:

        try:

            if role in source.roles:

                await source.remove_roles(
                    role,
                    reason=f"Role transferred to {member}"
                )

                removed.append(role)

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            failed.append(role)

    # ========================================================
    # GET THE 2 PROTECTED ROLES
    # ========================================================

    kept_roles = [
        role
        for role in source.roles
        if role.id in KEEP_ROLE_IDS
    ]

    # ========================================================
    # RESULT EMBED
    # ========================================================

    embed = discord.Embed(
        title="🔄 Roles Transferred",
        description=(
            f"Roles have been transferred from "
            f"{source.mention} to {member.mention}."
        ),
        color=discord.Color.from_rgb(
            217,
            232,
            74
        )
    )

    embed.add_field(
        name="👤 From",
        value=source.mention,
        inline=True
    )

    embed.add_field(
        name="👤 To",
        value=member.mention,
        inline=True
    )

    embed.add_field(
        name="🔄 Transferred Roles",
        value=(
            "\n".join(
                role.mention
                for role in transferred
            )
            if transferred
            else "None"
        ),
        inline=False
    )

    embed.add_field(
        name="🔒 Roles Kept",
        value=(
            "\n".join(
                role.mention
                for role in kept_roles
            )
            if kept_roles
            else "None"
        ),
        inline=False
    )

    embed.add_field(
        name="🗑️ Roles Removed",
        value=f"**{len(removed)}**",
        inline=True
    )

    if failed:

        embed.add_field(
            name="⚠️ Failed",
            value=(
                f"**{len(failed)}** role(s) "
                "could not be transferred."
            ),
            inline=True
        )

    embed.set_thumbnail(
        url=source.display_avatar.url
    )

    embed.set_footer(
        text="LUCK's MM • Role Transfer"
    )

    await ctx.send(
        embed=embed
    )


@transferroles.error
async def transferroles_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        return await ctx.send(
            "❌ You need the **Manage Roles** permission."
        )

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        return await ctx.send(
            "❌ Usage: `$transferroles @user`"
        )

    if isinstance(
        error,
        commands.BadArgument
    ):

        return await ctx.send(
            "❌ Please mention a valid server member "
            "or use their ID."
        )

    print(
        f"❌ $transferroles error: "
        f"{type(error).__name__}: {error}"
    )

    await ctx.send(
        "❌ An error occurred while transferring roles."
    )


# ============================================================
# $BACKUP
# ============================================================

@bot.command(name="backup")
@commands.has_permissions(administrator=True)
async def backup_command(ctx):

    guild = ctx.guild

    backup = {
        "guild_name": guild.name,
        "roles": [],
        "categories": [],
        "channels": []
    }

    for role in guild.roles:

        if role == guild.default_role:

            continue

        backup["roles"].append({
            "name": role.name,
            "permissions": role.permissions.value,
            "color": role.color.value,
            "hoist": role.hoist,
            "mentionable": role.mentionable
        })

    for category in guild.categories:

        backup["categories"].append({
            "name": category.name,
            "position": category.position
        })

    for channel in guild.channels:

        if isinstance(
            channel,
            discord.CategoryChannel
        ):

            continue

        data = {
            "name": channel.name,
            "type": str(channel.type),
            "position": channel.position,
            "category": (
                channel.category.name
                if channel.category
                else None
            )
        }

        if isinstance(
            channel,
            discord.TextChannel
        ):

            data["topic"] = channel.topic
            data["slowmode_delay"] = channel.slowmode_delay
            data["nsfw"] = channel.nsfw

        elif isinstance(
            channel,
            discord.VoiceChannel
        ):

            data["bitrate"] = channel.bitrate
            data["user_limit"] = channel.user_limit

        backup["channels"].append(
            data
        )

    with open(
        BACKUP_FILE,
        "w"
    ) as f:

        json.dump(
            backup,
            f,
            indent=4
        )

    await ctx.send(
        "✅ Server backup created.\n"
        f"📁 `{BACKUP_FILE}`"
    )


# ============================================================
# $RESTORE
# ============================================================

@bot.command(name="restore")
@commands.has_permissions(administrator=True)
async def restore_command(ctx):

    if not os.path.exists(
        BACKUP_FILE
    ):

        return await ctx.send(
            "❌ No server backup was found."
        )

    try:

        with open(
            BACKUP_FILE,
            "r"
        ) as f:

            backup = json.load(f)

    except (
        json.JSONDecodeError,
        OSError
    ):

        return await ctx.send(
            "❌ The backup file is invalid."
        )

    await ctx.send(
        "⚠️ **Server restore started.**\n"
        "This will recreate missing roles and channels "
        "from the saved backup."
    )

    existing_roles = {
        role.name: role
        for role in ctx.guild.roles
    }

    created_roles = 0

    for role_data in backup.get(
        "roles",
        []
    ):

        if role_data["name"] in existing_roles:

            continue

        try:

            role = await ctx.guild.create_role(
                name=role_data["name"],
                permissions=discord.Permissions(
                    role_data["permissions"]
                ),
                colour=discord.Colour(
                    role_data["color"]
                ),
                hoist=role_data["hoist"],
                mentionable=role_data["mentionable"],
                reason="Server backup restore"
            )

            existing_roles[
                role.name
            ] = role

            created_roles += 1

        except discord.Forbidden:

            pass

    existing_categories = {
        category.name: category
        for category in ctx.guild.categories
    }

    created_categories = 0

    for category_data in backup.get(
        "categories",
        []
    ):

        if category_data["name"] in existing_categories:

            continue

        try:

            category = await ctx.guild.create_category(
                category_data["name"],
                reason="Server backup restore"
            )

            existing_categories[
                category.name
            ] = category

            created_categories += 1

        except discord.Forbidden:

            pass

    existing_channels = {
        channel.name
        for channel in ctx.guild.channels
    }

    created_channels = 0

    for channel_data in backup.get(
        "channels",
        []
    ):

        name = channel_data["name"]

        if name in existing_channels:

            continue

        category = None

        category_name = channel_data.get(
            "category"
        )

        if category_name:

            category = existing_categories.get(
                category_name
            )

        try:

            if channel_data["type"] == "text":

                await ctx.guild.create_text_channel(
                    name,
                    category=category,
                    topic=channel_data.get(
                        "topic"
                    ),
                    slowmode_delay=channel_data.get(
                        "slowmode_delay",
                        0
                    ),
                    nsfw=channel_data.get(
                        "nsfw",
                        False
                    ),
                    reason="Server backup restore"
                )

                created_channels += 1

            elif channel_data["type"] == "voice":

                await ctx.guild.create_voice_channel(
                    name,
                    category=category,
                    bitrate=channel_data.get(
                        "bitrate"
                    ),
                    user_limit=channel_data.get(
                        "user_limit",
                        0
                    ),
                    reason="Server backup restore"
                )

                created_channels += 1

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass

    await ctx.send(
        "✅ **Server restore finished.**\n\n"
        f"🎭 Roles created: **{created_roles}**\n"
        f"📁 Categories created: **{created_categories}**\n"
        f"💬 Channels created: **{created_channels}**"
    )


# ============================================================
# $DM @USER MESSAGE
# ============================================================

@bot.command(name="dm")
@commands.has_permissions(manage_messages=True)
async def dm_command(
    ctx,
    member: discord.Member,
    *,
    message: str
):

    if member.bot:

        return await ctx.send(
            "❌ You cannot DM a bot."
        )

    if not message.strip():

        return await ctx.send(
            "❌ Usage: `$dm @user message`"
        )

    embed = discord.Embed(
        title="📩 Message from the Server",
        description=message,
        color=discord.Color.from_rgb(
            217,
            232,
            74
        )
    )

    embed.set_footer(
        text=f"Sent from {ctx.guild.name}"
    )

    try:

        await member.send(
            embed=embed
        )

    except discord.Forbidden:

        return await ctx.send(
            f"❌ I couldn't DM {member.mention}. "
            "Their DMs may be closed."
        )

    except discord.HTTPException:

        return await ctx.send(
            "❌ Discord returned an error while sending "
            "the DM."
        )

    await ctx.send(
        f"✅ DM sent to {member.mention}."
    )


@dm_command.error
async def dm_command_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        return await ctx.send(
            "❌ You need the **Manage Messages** permission."
        )

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        return await ctx.send(
            "❌ Usage: `$dm @user message`"
        )

    if isinstance(
        error,
        commands.BadArgument
    ):

        return await ctx.send(
            "❌ Please mention a valid member."
        )


# ============================================================
# $MASSDM @ROLE MESSAGE
# ============================================================

@bot.command(name="massdm")
@commands.has_permissions(administrator=True)
async def massdm_command(
    ctx,
    role: discord.Role,
    *,
    message: str
):

    if role == ctx.guild.default_role:

        return await ctx.send(
            "❌ You cannot mass DM the @everyone role."
        )

    if role.managed:

        return await ctx.send(
            "❌ You cannot use a managed/integration role."
        )

    if not message.strip():

        return await ctx.send(
            "❌ Usage: `$massdm @role message`"
        )

    members = [
        member
        for member in ctx.guild.members
        if role in member.roles
        and not member.bot
    ]

    if not members:

        return await ctx.send(
            f"❌ No members with {role.mention} were found."
        )

    await ctx.send(
        f"📨 **Mass DM started.**\n"
        f"🎭 Role: {role.mention}\n"
        f"👥 Members with role: **{len(members)}**"
    )

    success = 0
    failed = 0

    for member in members:

        embed = discord.Embed(
            title="📩 Message from the Server",
            description=message,
            color=discord.Color.from_rgb(
                217,
                232,
                74
            )
        )

        embed.set_footer(
            text=f"Sent from {ctx.guild.name}"
        )

        try:

            await member.send(
                embed=embed
            )

            success += 1

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            failed += 1

        await asyncio.sleep(1)

    embed = discord.Embed(
        title="📨 Mass DM Finished",
        color=discord.Color.from_rgb(
            90,
            24,
            150
        )
    )

    embed.add_field(
        name="🎭 Role",
        value=role.mention,
        inline=False
    )

    embed.add_field(
        name="👥 Members Found",
        value=f"**{len(members)}**",
        inline=True
    )

    embed.add_field(
        name="✅ DMs Sent",
        value=f"**{success}**",
        inline=True
    )

    embed.add_field(
        name="❌ DMs Failed",
        value=f"**{failed}**",
        inline=True
    )

    embed.set_footer(
        text=f"Mass DM by {ctx.author.display_name}"
    )

    await ctx.send(
        embed=embed
    )


@massdm_command.error
async def massdm_command_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        return await ctx.send(
            "❌ You need the **Administrator** permission."
        )

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        return await ctx.send(
            "❌ Usage: `$massdm @role message`"
        )

    if isinstance(
        error,
        commands.BadArgument
    ):

        return await ctx.send(
            "❌ Please mention a valid role."
        )


# ============================================================
# $HELP
# ============================================================

bot.remove_command("help")


@bot.command(name="help")
async def help_command(ctx):

    embed = discord.Embed(
        title="📖 Bot Commands",
        description=(
            "Here are all available commands.\n"
            "Commands requiring permissions can only be used "
            "by members with the required permissions."
        ),
        color=discord.Color.from_rgb(
            217,
            232,
            74
        )
    )

    embed.add_field(
        name="📄 Application Commands",
        value=(
            "`$trigger @user` — Send a flopping application"
        ),
        inline=False
    )

    embed.add_field(
        name="⭐ Vouch Commands",
        value=(
            "`$addvouch @user (number)` — Add vouches\n"
            "`$removevouch @user (number)` — Remove vouches\n"
            "`$vouches @user` — Check vouches"
        ),
        inline=False
    )

    embed.add_field(
        name="🎭 Role Commands",
        value=(
            "`$role @user @role` — Give a role\n"
            "`$promo @user` — Promote a user\n"
            "`$demo @user` — Demote a user\n"
            "`$fill` — Fill missing roles\n"
            "`$roles` — Show server roles"
        ),
        inline=False
    )

    embed.add_field(
        name="⏸️ Temporary Role Commands",
        value=(
            "`$temp` — Temporarily remove roles\n"
            "`$untemp` — Restore saved roles"
        ),
        inline=False
    )

    embed.add_field(
        name="👤 User / Server Commands",
        value=(
            "`$w @user` — View user profile\n"
            "`$serverinfo` — View server information"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Moderation Commands",
        value=(
            "`$to @user (time)` — Timeout a member\n"
            "`$unto @user` — Remove timeout\n"
            "`$ban @user / ID` — Ban a member\n"
            "`$unban (user ID)` — Unban a member\n"
            "`$kick @user / ID` — Kick a member\n"
        ),
        inline=False
    )

    embed.add_field(
        name="🎫 Ticket Commands",
        value=(
            "`$claim` — Claim current ticket\n"
            "`$unclaim` — Unclaim current ticket\n"
            "`$transferticket @user / ID` — Transfer ticket\n"
            "`$add @user / ID` — Add member to ticket\n"
            "`$close` — Save transcript and close ticket\n"
            "`$transferroles @user` — Transfer roles\n"
            "`$mminfo` - shows how middleman works\n"
            "`$mmfee` - shows fee embed"
        ),
        inline=False
    )

    embed.add_field(
        name="📩 DM Commands",
        value=(
            "`$dm @user message` — DM one member\n"
            "`$massdm @role message` — DM everyone with a role"
        ),
        inline=False
    )

    embed.add_field(
        name="💾 Server Backup",
        value=(
            "`$backup` — Create server backup\n"
            "`$restore` — Restore server backup"
        ),
        inline=False
    )

    embed.add_field(
    name="🛠️ Manage Messages",
    value=(
        "`$snipe` — View the latest deleted message\n"
        "`$snipe <number>` — View a specific deleted message\n"
        "`$clearsnipe` — Clear deleted message history\n"
        "`$purge <number>` — Delete multiple messages"
    ),
    inline=False
)

    if ctx.guild.icon:

        embed.set_thumbnail(
            url=ctx.guild.icon.url
        )

    embed.set_footer(
        text=f"Requested by {ctx.author.display_name}"
    )

    await ctx.send(
        embed=embed
    )


# ============================================================
# GLOBAL COMMAND ERROR HANDLER
# ============================================================

@bot.event
async def on_command_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.CommandNotFound
    ):

        return

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        return await ctx.send(
            "❌ You don't have permission to use this command."
        )

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        return await ctx.send(
            "❌ Missing required argument. "
            "Use `$help` to see usage."
        )

    if isinstance(
        error,
        commands.BadArgument
    ):

        return await ctx.send(
            "❌ Invalid argument. "
            "Use `$help` to see the correct format."
        )

    if isinstance(
        error,
        commands.CommandInvokeError
    ):

        original = error.original

        print(
            "\n============================================================"
        )

        print(
            f"❌ Error in command `{ctx.command}`"
        )

        print(
            f"Type: {type(original).__name__}"
        )

        print(
            f"Details: {original}"
        )

        print(
            "============================================================\n"
        )

        return await ctx.send(
            f"❌ An error occurred while running "
            f"`{ctx.command}`:\n"
            f"`{type(original).__name__}: {original}`"
        )

    print(
        f"❌ Unhandled command error: "
        f"{type(error).__name__}: {error}"
    )


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():

    print(
        f"✅ Logged in as {bot.user}"
    )

    print(
        f"✅ Bot is running in "
        f"{len(bot.guilds)} server(s)"
    )

    print(
        "✅ $trigger application system loaded"
    )

    print(
        "✅ Accept / Decline buttons loaded"
    )

    print(
        "✅ Application role system loaded"
    )

    print(
        "✅ New Flopper system loaded"
    )

    print(
        "✅ Ticket commands loaded"
    )

    print(
        "✅ $claim loaded"
    )

    print(
        "✅ $unclaim loaded"
    )

    print(
        "✅ $transferticket loaded"
    )

    print(
        "✅ $add loaded"
    )

    print(
        "✅ $close loaded"
    )

    print(
        f"✅ Transcript channel: {TRANSCRIPT_CHANNEL_ID}"
    )


# ============================================================
# SNIPE SYSTEM
# ============================================================

MAX_SNIPE_MESSAGES = 100

# Stores deleted messages separately for each channel
snipe_messages = {}


# ============================================================
# TRACK DELETED MESSAGES
# ============================================================

@bot.event
async def on_message_delete(message):

    # Ignore bot messages
    if message.author.bot:
        return

    channel_id = message.channel.id

    if channel_id not in snipe_messages:
        snipe_messages[channel_id] = []

    deleted_message = {
        "author": message.author,
        "content": message.content,
        "attachments": [
            attachment.url
            for attachment in message.attachments
        ],
        "created_at": message.created_at
    }

    # Put newest deleted message first
    snipe_messages[channel_id].insert(
        0,
        deleted_message
    )

    # Keep maximum 100 messages
    snipe_messages[channel_id] = (
        snipe_messages[channel_id][:MAX_SNIPE_MESSAGES]
    )


# ============================================================
# $SNIPE / $SNIPE (NUMBER)
# ============================================================

@bot.command(name="snipe")
@commands.has_permissions(manage_messages=True)
async def snipe(ctx, number: int = 1):

    channel_id = ctx.channel.id

    # --------------------------------------------------------
    # NO SNIPES
    # --------------------------------------------------------

    if (
        channel_id not in snipe_messages
        or not snipe_messages[channel_id]
    ):

        await ctx.send(
            "❌ There are no deleted messages to snipe."
        )

        return

    # --------------------------------------------------------
    # INVALID NUMBER
    # --------------------------------------------------------

    if number < 1:

        await ctx.send(
            "❌ The number must be **1 or higher**."
        )

        return

    messages = snipe_messages[channel_id]

    if number > len(messages):

        await ctx.send(
            f"❌ There are only **{len(messages)}** "
            "deleted messages available."
        )

        return

    deleted = messages[number - 1]

    author = deleted["author"]
    content = deleted["content"]

    # --------------------------------------------------------
    # MESSAGE CONTENT
    # --------------------------------------------------------

    if not content:
        content = "*No text content*"

    # Discord embed field/value limit protection
    if len(content) > 4000:
        content = content[:3997] + "..."

    # --------------------------------------------------------
    # CREATE EMBED
    # --------------------------------------------------------

    embed = discord.Embed(
        description=content,
        color=discord.Color.from_rgb(
            217,
            232,
            74
        )
    )

    # --------------------------------------------------------
    # AUTHOR
    # --------------------------------------------------------

    embed.set_author(
        name=author.display_name,
        icon_url=author.display_avatar.url
    )

    # --------------------------------------------------------
    # DELETED MESSAGE TIMELINE
    # --------------------------------------------------------

    embed.add_field(
        name="Deleted Message Timeline",
        value=(
            f"Sent originally: "
            f"<t:{int(deleted['created_at'].timestamp())}:R>"
        ),
        inline=False
    )

    # --------------------------------------------------------
    # ATTACHMENT
    # --------------------------------------------------------

    if deleted["attachments"]:

        first_attachment = deleted["attachments"][0]

        # Show image as thumbnail like the Roblox Trade Helper
        if any(
            first_attachment.lower().endswith(ext)
            for ext in [
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp"
            ]
        ):

            embed.set_thumbnail(
                url=first_attachment
            )

        else:

            embed.add_field(
                name="Attachment",
                value=first_attachment[:1024],
                inline=False
            )

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    embed.set_footer(
        text=(
            f"{ctx.channel.name} • "
            f"Snipe Record {number}/{len(messages)}"
        )
    )

    # --------------------------------------------------------
    # SEND
    # --------------------------------------------------------

    await ctx.send(
        embed=embed
    )


# ============================================================
# $CLEARSNIPE
# ============================================================

@bot.command(name="clearsnipe")
@commands.has_permissions(manage_messages=True)
async def clearsnipe(ctx):

    channel_id = ctx.channel.id

    # --------------------------------------------------------
    # NOTHING TO CLEAR
    # --------------------------------------------------------

    if (
        channel_id not in snipe_messages
        or not snipe_messages[channel_id]
    ):

        await ctx.send(
            "⚠️ There are no deleted messages to clear."
        )

        return

    # --------------------------------------------------------
    # COUNT
    # --------------------------------------------------------

    cleared = len(
        snipe_messages[channel_id]
    )

    # --------------------------------------------------------
    # CLEAR
    # --------------------------------------------------------

    snipe_messages[channel_id].clear()

    # --------------------------------------------------------
    # CONFIRM
    # --------------------------------------------------------

    await ctx.send(
        f"🗑️ Cleared **{cleared}** "
        "sniped message(s) from this channel."
    )


# ============================================================
# SNIPE ERROR HANDLER
# ============================================================

@snipe.error
async def snipe_error(ctx, error):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ You need **Manage Messages** permission "
            "to use `$snipe`."
        )

    elif isinstance(
        error,
        commands.BadArgument
    ):

        await ctx.send(
            "❌ Usage: `$snipe` or `$snipe <number>`"
        )


# ============================================================
# CLEARSNIPE ERROR HANDLER
# ============================================================

@clearsnipe.error
async def clearsnipe_error(ctx, error):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ You need **Manage Messages** permission "
            "to use `$clearsnipe`."
        )
        
afk_users = {}

@bot.command(name="afk")
async def afk(ctx, *, reason: str = "AFK"):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    afk_users[ctx.author.id] = reason

    embed = discord.Embed(
        title="💗 AFK Status",
        description=(
            f"{ctx.author.mention} is now AFK\n\n"
            f"📌 **Reason**\n"
            f"{reason}\n\n"
            f"*You will be marked as AFK until you send a message.*"
        ),
        color=discord.Color.from_rgb(217, 232, 74)
    )

    embed.set_footer(text="Minstrea")

    await ctx.send(embed=embed)


@bot.listen("on_message")
async def afk_handler(message):

    if message.author.bot:
        return

    # User comes back from AFK
    if message.author.id in afk_users:
        afk_users.pop(message.author.id)

        embed = discord.Embed(
            title="💗 Welcome Back!",
            description=(
                f"Welcome back, {message.author.mention}!\n\n"
                f"You are no longer AFK."
            ),
            color=discord.Color.from_rgb(217, 232, 74)
        )

        embed.set_footer(text="LUCK's MM")

        await message.channel.send(embed=embed)

    # Someone mentions an AFK user
    for user in message.mentions:
        if user.bot:
            continue

        if user.id in afk_users:
            reason = afk_users[user.id]

            embed = discord.Embed(
                title="💤 AFK",
                description=(
                    f"{user.mention} is currently AFK.\n\n"
                    f"📌 **Reason**\n"
                    f"{reason}"
                ),
                color=discord.Color.from_rgb(90, 24, 150)
            )

            embed.set_footer(text="TradeVault")

            await message.channel.send(embed=embed)

@bot.command(name="say")
async def say(ctx, *, message: str = None):

    OWNER_ROLE_ID = 1463291530268643503  # PUT OWNER ROLE ID HERE

    if not any(role.id == OWNER_ROLE_ID for role in ctx.author.roles):
        return await ctx.send(
            "❌ You need the **Owner** role to use `$say`.",
            delete_after=5
        )

    if not message:
        return await ctx.send(
            "❌ Usage: `$say <message>`",
            delete_after=5
        )

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    await ctx.send(message)
    
# ============================================================
# $MMFEE
# ============================================================

class MMFeeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="100%",
        style=discord.ButtonStyle.success,
        custom_id="mmfee_100"
    )
    async def fee_100(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"💰 {interaction.user.mention} selected **100%**.\n"
            "They will cover the full middleman fee."
        )

    @discord.ui.button(
        label="50%",
        style=discord.ButtonStyle.secondary,
        custom_id="mmfee_50"
    )
    async def fee_50(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"💰 {interaction.user.mention} selected **50%**.\n"
            "The middleman fee will be split 50/50."
        )


@bot.command(name="mmfee")
async def mmfee(ctx):
    embed = discord.Embed(
        title="Middleman Fee",
        description=(
            "✕ : Middleman fee is required before we are permitted "
            "to start with the transaction.\n"
            "The fee covers securing the deal, verifying both sides, "
            "and ensuring a safe transfer for everyone involved.\n"
            "Once the fee is paid, we can continue immediately.\n\n"
            "✕ : Before we continue, who will be covering the "
            "**middleman fee**?\n"
            "Are you paying it fully, or would you both like to "
            "**split the fee** between each other?"
        ),
        color=discord.Color.from_rgb(217, 232, 74)
    )
    
    embed.set_image(url="https://cdn.discordapp.com/attachments/1547444944606593066/1547897741835767868/image0.gif?ex=6aa5179c&is=6aa3c61c&hm=efba347a12dfddb70d7e61adca1bc7ceec6ab0f8bb15a2fc0b0493bd9e07e0a4&")

    await ctx.send(
        embed=embed,
        view=MMFeeView()
    )

# ============================================================
# $MMINFO
# ============================================================

MMINFO_BANNER = "https://cdn.discordapp.com/attachments/1547444944606593066/1547901646124617738/7BD29FDC-5A64-44CD-8E01-8C0A3A1A0C71.png?ex=6aa51b3f&is=6aa3c9bf&hm=53a647a875bb5fe199a1132bbaea72c2d2207ee4cec65bc5c3ed8f474bffb856&"


class MMInfoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Understood",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="mminfo_understood"
    )
    async def understood(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            f"✅ {interaction.user.mention} has confirmed that they "
            "**understand how the middleman process works.**",
        )


@bot.command(name="mminfo")
async def mminfo(ctx):
    embed = discord.Embed(
        title="How does a middleman work?",
        description=(
            "✕ : **Example:** Trade is NFR Crow for Robux.\n\n"
            "The Middleman will hold the NFR Crow. After the "
            "middleman gets the NFR Crow in their inventory, "
            "they will tell the buyer and show the buyer proof "
            "they have the NFR Crow, then the buyer will pay "
            "the Robux.\n\n"
            "Once the buyer has paid and the seller has confirmed "
            "that they got it, the middleman will give the NFR "
            "Crow to the seller."
        ),
        color=discord.Color.from_rgb(217, 232, 74)
    )

    embed.set_image(url=MMINFO_BANNER)

    await ctx.send(
        embed=embed,
        view=MMInfoView()
    )
    
# ============================================================
# RUN BOT
# ============================================================

bot.run(TOKEN)
