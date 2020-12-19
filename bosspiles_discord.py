"""Discord client."""
import datetime as dt
import logging
from logging.handlers import RotatingFileHandler
import json
import shlex
import traceback

import discord

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

# Intents are required as of discord 1.5
intents = discord.Intents(messages=True, guilds=True, members=True)
client = discord.Client(intents=intents)


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
            with open('errs', 'a') as f:
                f.write(traceback.format_exc())
                f.write(str(e))


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
    # only first letter has to match
    elif args[0][0] not in [w[0] for w in ["new", "win", "edit", "move", "remove", "active", "print", "unpin"]]:
        return [], f"`$ {args[0]}` is not a recognized subcommand. See `$`."
    elif args[0][0] in [w[0] for w in ["edit"]] and len(args) != 3:
        return [], f"`$ {args[0]}` requires 2 arguments. See `$`."
    else:
        return args, ""
    return [], "Problem parsing arguments. Type $ for options."  # Returns this on any error condition


async def get_pinned_bosspile(message):
    """Get the pinned messages if there are any."""
    pins = await message.channel.pins()
    if len(pins) == 0:
        return None, "This channel has no pins (a pinned bosspile is required)"
    for pin in pins:
        # First try to get pins by this bot before other messages
        if pin.author.id == client.user.id:
            return pin, ""
        # If it has the format of a bosspile, treat it like one
        elif ("\n:crown:" in pin.content or "\n👑" in pin.content) \
                and '\n' in pin.content and 'bosspile' in pin.content.lower().split('\n')[0] \
                and (":small_orange_diamond:" in pin.content or "🔸" in pin.content or "arrow_double_up" in pin.content or "⏫" in pin.content):
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
    if "sushi-go-mbosspile" in message.channel.name:
        return "Coxy5 manages this bosspile, not the bosspiles bot. Ping him instead."
    args, errs = await parse_args(message.content)
    if errs:
        return errs
    nicknames = {}
    # Get the nicknames from the guild members
    for user in message.guild.members:
        nicknames[str(user.id)] = user.display_name
    # We can change the board game name, but I'm not sure it matters.
    if args[0] == "unpin":
        # Unpin requires a reason
        if len(args) < 2:
            await message.author.send("You need to provide a reason for the unpin (1+ words).")
        elif message.author.id == 234561564697559041 or message.author.guild_permissions.administrator:
            await unpin_bot_pins(args, message)
        else:
            await message.author.send("You don't have permissions to unpin.")
        return ""
    bp_pin, errs = await get_pinned_bosspile(message)
    if errs:
        return errs
    # We can only edit our own messages
    edit_existing_bp = bp_pin.author == client.user
    game = message.channel.name.replace('bosspile', '').replace('-', '')
    bosspile = BossPile(game, nicknames, bp_pin.content)
    return_message = await execute_command(args, bosspile)
    new_bosspile = bosspile.generate_bosspile()
    bosspile_server_id = 419535969507606529
    contributors_line, day_expires = generate_contrib_line()
    if (
        args[0].startswith("w")
        and ("standings" in return_message.lower() or "bosspile" in return_message.lower())  # Bosspile Standings or Ladder Standings in title
        and (day_expires - dt.datetime.now()).days < 20
        and message.guild.id == bosspile_server_id
    ):
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
        "Corwin007": 10,
        "tarpshack": 25
    }
    total_contrib = sum(list(contributions.values()))
    MONTHLY_HOSTING_COST = 5.2
    days_bought = total_contrib / MONTHLY_HOSTING_COST * 30
    day_expires = (dt.datetime(2020, 8, 1, 0, 0, 0, 0) + dt.timedelta(days=days_bought))
    isodate_expires = day_expires.date().isoformat()
    return f"\n_Hosting paid for until {isodate_expires} thanks to [{', '.join(list(contributions.keys()))}]._", day_expires


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
