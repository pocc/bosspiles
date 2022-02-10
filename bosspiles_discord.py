"""Discord client."""
import datetime as dt
import logging
from logging.handlers import RotatingFileHandler
import json
import re
import shlex
import traceback
import time
import datetime

import discord
from discord.ext import tasks

from bosspiles import BossPile
from keys import TOKEN

LOG_FILENAME = "errs"
logger = logging.getLogger(__name__)
logging.getLogger("discord").setLevel(logging.WARN)
# Add the log message handler to the logger
handler = RotatingFileHandler(LOG_FILENAME, maxBytes=10000000, backupCount=0)
formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
day_started = str(datetime.date.today())

# Intents are required as of discord 1.5
intents = discord.Intents(messages=True, guilds=True, members=True)
client = discord.Client(intents=intents)

VALID_COMMANDS = ["new", "win", "edit", "move", "remove", "active", "print", "pin", "unpin"]
BOSSPILE_SERVER_ID = 419535969507606529
SECONDS_PER_WEEK = 7 * 86400
STATUS_LOCK = '.statuslock'


# Schedule a weekly check of bosspiles
@tasks.loop(hours=24)
async def check_bosspiles():
    SUNDAY_DAYNUM = 6
    todays_date = str(datetime.date.today())  # don't run on the day it started
    if datetime.datetime.today().weekday() != SUNDAY_DAYNUM or todays_date == day_started:
        return
    logger.debug("Weekly status check has triggered")
    text_channel_list = []
    for server in client.guilds:
        for channel in server.channels:
            # If it's a bosspile, but not multibosspile or yucata
            isTextChannel = channel and type(channel) == discord.TextChannel
            if isTextChannel and channel.name == "bugs":
                await channel.send("Weekly status check has triggered.")
            inBGACategory = channel.category and channel.category.name.lower() == "bosspile tracking channels"
            if isTextChannel and inBGACategory:
                text_channel_list.append(channel)
    sorted_channel_names = sorted([chan.name for chan in text_channel_list])
    num_channels = len(text_channel_list)
    logger.debug(f"Running status check against {num_channels} channels: {sorted_channel_names}")
    for channel in text_channel_list:
        # Stagger messages so we don't DDOS the BGA bot
        time.sleep(60)
        pins = await channel.pins()
        valid_pin, error = await get_pinned_bosspile(pins)
        if error or not valid_pin:
            logger.error(error)
            continue
        await channel.send("__**Weekly BGA game status check**__")
        nicknames = {}
        # Get the nicknames from the guild members
        for user in channel.guild.members:
            nicknames[str(user.id)] = user
        status_checks = generate_status_checks(channel.name, nicknames, valid_pin.content)
        for status_check in status_checks:
            await channel.send(status_check)


def generate_status_checks(channel_name, nicknames, pin_content):
    game_name = re.sub(r'[^-]?bosspile', "", channel_name).replace('-', '')
    bosspile = BossPile(channel_name, nicknames, pin_content)
    matches = bosspile.generate_matches()
    status_checks = []
    for match in matches:
        player_names = []
        for player in match:
            username = re.sub(r" *\([^)]*\) *", "", player.username)
            player_names.append(username)
        player_text = '" "'.join(player_names)  # space between all players, quote player names
        status_checks.append(f'!status {game_name} "{player_text}"')
    return status_checks


class GracefulCoroutineExit(Exception):
    """Return from the child function without exiting.
    via https://stackoverflow.com/questions/60975800/return-from-parent-function-in-a-child-function"""
    pass


@client.event
async def on_ready():
    """Let the user who started the bot know that the connection succeeded."""
    logger.debug(f'{client.user.name} has connected to Discord, and is active on {len(client.guilds)} servers!')
    # Create words under bot that say "Listening to !bga"
    listening_to_help = discord.Activity(type=discord.ActivityType.listening, name="$")
    await check_bosspiles.start()
    await client.change_presence(activity=listening_to_help)


@client.event
async def on_message(message):
    """Listen to messages so that this bot can do something."""
    if message.author == client.user:
        return

    if message.content.startswith('$'):
        try:
            return_message = await run_bosspiles(message)
            await send_message_partials(message.channel, return_message)
        except Exception as e:
            await message.channel.send("Tell <@!234561564697559041> to fix his bosspiles bot.")
            logger.error(traceback.format_exc() + str(e))


async def parse_args(msg_text):
    """Parse the args and tell the user if they are not valid."""
    while len(msg_text) > 0 and msg_text[0] == '$':
        msg_text = msg_text[1:]
    try:
        args = shlex.split(msg_text)
    except ValueError:
        return [], "Problem parsing arguments. Try quoting or not using special characters."
    if len(args) == 0 or args[0][0] == 'h':  # on `$` or `$help`
        help_text = get_help()
        return [], help_text
    elif "pin" == args[0] and (len(args) != 2 or not args[1].isdigit()):
        return [], "`$pin` requires one argument: the message ID (number) of the message you want to pin."
    elif ("edit".startswith(args[0]) or "active".startswith(args[0])) and len(args) != 3:
        return [], f"`${args[0]}` requires 2 arguments. See `$`."
    elif not any([cmd.startswith(args[0]) for cmd in VALID_COMMANDS]):
        return [], f"`${args[0]}` is not a recognized subcommand. See `$`."
    else:
        return args, ""


def is_valid_bosspile(pin_text):
    if '\n' not in pin_text:
        return False
    first_line = pin_text.lower().split('\n')[0]
    has_crown = "\n:crown:" in pin_text or "\n👑" in pin_text
    has_title = 'bosspile' in first_line or 'ladder' in first_line
    has_winners = ":small_orange_diamond:" in pin_text or "🔸" in pin_text
    has_climbers = "arrow_double_up" in pin_text or "⏫" in pin_text
    return has_crown and has_title and (has_winners or has_climbers)


async def get_pinned_bosspile(pins):
    """Get the pinned messages if there are any."""
    if len(pins) == 0:
        return None, "This channel has no pins (a pinned bosspile is required)"
    for pin in pins:
        # First try to get pins by this bot before other messages
        if pin.author.id == client.user.id:
            return pin, ""
        # If it has the format of a bosspile, treat it like one
        elif is_valid_bosspile(pin.content):
            return pin, ""
    return None, "This channel has no bosspile pins! Pin your bosspile message and try again."


async def execute_command(args, bosspile):
    """Execute the $ command the user has entered and return a message."""
    args[0] = args[0].lower()
    if "win".startswith(args[0]):
        victor = ' '.join(args[1:])
        return bosspile.win(victor)
    elif "new".startswith(args[0]):
        player_name = ' '.join(args[1:])
        return bosspile.add(player_name)
    elif "edit".startswith(args[0]):
        old_line = args[1]
        new_line = args[2]
        return bosspile.edit(old_line, new_line)
    elif "move".startswith(args[0]):
        player = ' '.join(args[1:-1])
        relative_position = args[-1]
        return bosspile.move(player, relative_position)
    elif "remove".startswith(args[0]):
        player_name = ' '.join(args[1:])
        return bosspile.remove(player_name)
    elif "active".startswith(args[0]):
        player_name = ' '.join(args[1:-1])
        state = args[-1].lower().startswith("t")  # t for true, anything else is false
        return bosspile.change_active_status(player_name, state)
    elif "print".startswith(args[0]):
        if len(args) > 1:
            if args[1].startswith("d"):  # debug
                return "\n".join([json.dumps(p.__dict__) for p in bosspile.players])
            elif args[1].startswith("r"):  # raw
                return f"`{bosspile.generate_bosspile()}`"
        return bosspile.generate_bosspile()
    else:
        return f"Unrecognized command {args[0]}. Run `$`."


async def run_bosspiles(message):
    """Run the bosspiles program ~ main()."""
    logger.debug(f"Received message `{message.content}`")
    # if this is a discord server and the channel is a specific one
    if message.guild and message.guild.id == BOSSPILE_SERVER_ID and "mbosspile" in message.channel.name:
        return "@Coxy5 manages this bosspile, not the bosspiles bot. He is quite helpful and will get you sorted right quick."
    args, errs = await parse_args(message.content)
    if errs:
        return errs
    nicknames = {}
    # Get the nicknames from the guild members
    for user in message.guild.members:
        nicknames[str(user.id)] = user.display_name
    # We can change the board game name, but I'm not sure it matters.
    channel_pins = await message.channel.pins()
    if args[0] == "unpin":
        # Unpin requires a reason
        if len(args) < 2:
            await message.author.send("You need to provide a reason for the unpin (1+ words).")
        elif message.author.id == 234561564697559041 or message.author.guild_permissions.administrator:
            await unpin_bot_pins(args, message)
        else:
            await message.author.send("You don't have permissions to unpin.")
        return ""
    elif args[0] == "pin":
        for pin in channel_pins:
            if pin.author.id == client.user.id:
                return "`$pin` can be used when this bot has no pins on the channel. There is already a bosspile pinned by this bot."
        msg_to_pin = await message.channel.fetch_message(args[1])
        if is_valid_bosspile(msg_to_pin.content):
            new_bp_pin = await message.channel.send(msg_to_pin.content)
            await new_bp_pin.pin()
            return f"Pinned {args[1]} successfully!"
        else:
            return f"Message with ID {args[1]} is not a valid bosspile. Make sure it has a\
                    \n* :crown:\
                    \n* 'ladder' or 'bosspile' in the first line\
                    \n* At least one :arrow_double_up:."
    bp_pin, errs = await get_pinned_bosspile(channel_pins)
    if errs:
        return errs
    # We can only edit our own messages
    edit_existing_bp = bp_pin.author == client.user
    bosspile = BossPile(message.channel.name, nicknames, bp_pin.content)
    return_message = await execute_command(args, bosspile)
    new_bosspile = bosspile.generate_bosspile()
    contributors_line, day_expires = generate_contrib_line()

    is_win = args[0].startswith("w")
    # Bosspile Standings or Ladder Standings in title
    is_bosspile_msg = ("standings" in return_message.lower() or "bosspile" in return_message.lower())
    is_bosspile_server = message.guild.id == BOSSPILE_SERVER_ID
    is_within_3weeks = (day_expires - dt.datetime.now()).days < 20
    if is_win and is_bosspile_msg and is_bosspile_server and is_within_3weeks:
        return_message += contributors_line
        new_bosspile += contributors_line
    if new_bosspile != bp_pin.content:
        if edit_existing_bp:
            await bp_pin.edit(content=new_bosspile)
        else:
            new_msg = await message.channel.send(new_bosspile)
            await new_msg.pin()
            await message.channel.send("Created new bosspile pin because this bot can only edit its own messages.")
    return return_message


def generate_contrib_line():
    contributions = {
        "Coxy5": 15,
        "Corwin007": 38.42,  # 10+22.82+5.6
        "tarpshack": 25
    }
    total_contrib = sum(list(contributions.values()))
    MONTHLY_HOSTING_COST = 5.2
    days_bought = total_contrib / MONTHLY_HOSTING_COST * 30
    day_expires = (dt.datetime(2020, 8, 1, 0, 0, 0, 0) + dt.timedelta(days=days_bought))
    isodate_expires = day_expires.date().isoformat()
    contributor_line = ""
    for i in contributions:
        num_months = round(contributions[i] / MONTHLY_HOSTING_COST, 1)
        contributor_line += f" {i} ({num_months} mo) "
    return f"\n_Hosting paid for until {isodate_expires} thanks to [{contributor_line}]._", day_expires


async def unpin_bot_pins(args, message):
    """Unpin all of the bot's pins."""
    bot_pins = await message.channel.pins()
    for pin in bot_pins:
        if pin.author == client.user:  # If this bot created it
            await message.channel.send("Bosspile being unpinned:")
            await message.channel.send(pin.content)
            await pin.unpin(reason=' '.join(args[1:]))
    return "Bosspile unpinned successfully!"


async def send_table_embed(message, game, active_players, inactive_players):
    """Create a discord embed to send the message about table creation."""
    retmsg = discord.Embed(
        title=game,
        color=3447003,
    )
    retmsg.add_field(name="Active", value=active_players, inline=False)
    retmsg.add_field(name="Inactive", value=inactive_players, inline=False)
    retmsg.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
    await message.channel.send(embed=retmsg)


def get_help():
    with open("help_text.md") as f:
        help_msg = f.read()
    truncated_help_msg = help_msg.replace(4 * " ", "\t")  # 2000 chars adds up quick
    return truncated_help_msg


async def send_message_partials(destination, remainder):
    # Loop over text and send message parts from the remainder until remainder is no more
    while len(remainder) > 0:
        chars_per_msg = 2000
        if len(remainder) < chars_per_msg:
            chars_per_msg = len(remainder)
        msg_part = remainder[:chars_per_msg]
        remainder = remainder[chars_per_msg:]
        # Only break on newline
        if len(remainder) > 0:
            while remainder[0] != "\n":
                remainder = msg_part[-1] + remainder
                msg_part = msg_part[:-1]
            # Discord will delete whitespace before a message
            # so preserve that whitespace by inserting a character
            while remainder[0] == "\n":
                remainder = remainder[1:]
            if remainder[0] == "\t":
                remainder = ".   " + remainder[1:]
        await destination.send(msg_part)


client.run(TOKEN)
