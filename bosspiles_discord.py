"""Discord client."""
import datetime as dt
import json
import shlex
import traceback

import discord

from bosspiles import BossPile
from keys import TOKEN

client = discord.Client()


class GracefulCoroutineExit(Exception):
    """Return from the child function without exiting.
    via https://stackoverflow.com/questions/60975800/return-from-parent-function-in-a-child-function"""
    pass


@client.event
async def on_ready():
    """Let the user who started the bot know that the connection succeeded."""
    print(f'{client.user.name} has connected to Discord!')
    # Create words under bot that say "Listening to !bga"
    listening_to_help = discord.Activity(type=discord.ActivityType.listening, name="$$")
    await client.change_presence(activity=listening_to_help)


@client.event
async def on_message(message):
    """Listen to messages so that this bot can do something."""
    if message.author == client.user:
        return

    if message.content.startswith('$$'):
        try:
            return_message = await run_bosspiles(message)
            await message.channel.send(return_message)
        except Exception as e:
            with open('errs', 'a') as f:
                f.write(traceback.format_exc())
                f.write(str(e))


async def parse_args(message):
    """Parse the args and tell the user if they are not valid."""
    args = shlex.split(message.content[2:])
    if len(args) == 0:  # on `$$`
        await send_help(message.author)
    # only first letter has to match
    elif args[0][0] not in [w[0] for w in ["new", "win", "edit", "move", "remove", "active", "print", "unpin"]]:
        await message.channel.send(f"`$$ {args[0]}` is not a recognized subcommand. See `$$`.")
    elif args[0][0] in [w[0] for w in ["new", "win", "remove"]] and len(args) != 2:
        await message.channel.send(f"`$$ {args[0]}` requires 1 argument. See `$$`.")
    elif args[0][0] in [w[0] for w in ["edit", "move", "active"]] and len(args) != 3:
        await message.channel.send(f"`$$ {args[0]}` requires 2 arguments. See `$$`.")
    else:
        return args
    raise GracefulCoroutineExit("Problem parsing arguments.")  # Returns this on any error condition


async def get_pinned_bosspile(message):
    """Get the pinned messages if there are any."""
    pins = await message.channel.pins()
    if len(pins) == 0:
        await message.channel.send("This channel has no pins (a pinned bosspile is required)")
        raise GracefulCoroutineExit("Channel has no pins!")
    for pin in pins:
        if (":crown:" in pin.content or "👑" in pin.content) \
                and (":small_orange_diamond:" in pin.content or "🔸" in pin.content
                    or ":arrow_double_up" in pin.content or "⏫" in pin.content):
            return pin
    await message.channel.send("This channel has no bosspile! Pin your bosspile message and try again.")
    raise GracefulCoroutineExit("Channel has pins but no bosspile!")


async def execute_command(args, bosspile):
    """Execute the $$ command the user has entered and return a message."""
    args[0] = args[0].lower()
    if "win".startswith(args[0]):
        victor = args[1]
        return bosspile.win(victor)
    elif "new".startswith(args[0]):  # new
        player_name = args[1]
        return bosspile.add(player_name)
    elif "edit".startswith(args[0]):  # edit
        old_line = args[1]
        new_line = args[2]
        return bosspile.edit(old_line, new_line)
    elif "move".startswith(args[0]):  # move
        player = args[1]
        relative_position = args[2]
        return bosspile.move(player, relative_position)
    elif "remove".startswith(args[0]):  # remove
        player_name = args[1]
        return bosspile.remove(player_name)
    elif "active".startswith(args[0]):  # active
        player_name = args[1]
        state = args[2].lower().startswith("t")  # t for true, anything else is false
        return bosspile.change_active_status(player_name, state)
    elif "print".startswith(args[0]):  # print
        if len(args) > 1:
            if args[1].startswith("d"):  # debug
                return "\n".join([json.dumps(p.__dict__) for p in bosspile.players])
            elif args[1].startswith("r"):  # raw
                return f"`{bosspile.generate_bosspile()}`"
        else:
            return bosspile.generate_bosspile()
    else:
        return f"Unrecognized command {args[0]}. Run `$$`."


async def run_bosspiles(message):
    """Run the bosspiles program ~ main()."""
    print(f"Received message `{message.content}`")
    args = await parse_args(message)

    nicknames = {}
    # Get the nicknames from the guild members
    for user in message.guild.members:
        nicknames[str(user.id)] = user.display_name
    # We can change the board game name, but I'm not sure it matters.
    if args[0] == "unpin":
        # Unpin requires a reason
        if len(args) < 2:
            await message.channel.send("You need to provide a reason for the unpin (1+ words).")
            return "Syntax error."
        unpin_bot_pins(args, message)
    bp_pin = await get_pinned_bosspile(message)
    # We can only edit our own messages
    edit_existing_bp = bp_pin.author == client.user
    game = message.channel.name.replace('bosspile', '').replace('-', '')
    bosspile = BossPile(game, nicknames, bp_pin.content)
    return_message = await execute_command(args, bosspile)
    contributors_line = generate_contrib_line()
    if args[0].startswith("w"):
        return_message += contributors_line

    new_bosspile = bosspile.generate_bosspile()
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
        "Coxy5": 15
    }
    total_contrib = sum(list(contributions.values()))
    MONTHLY_HOSTING_COST = 5.2
    days_bought = total_contrib/MONTHLY_HOSTING_COST*30
    day_expires = (dt.datetime(2020, 8, 1, 0, 0, 0, 0) + dt.timedelta(days=days_bought))
    isodate_expires = day_expires.date().isoformat()
    return f"\n_Hosting paid for until {isodate_expires} thanks to [{', '.join(list(contributions.keys()))}]._"

async def unpin_bot_pins(args, message):
    """Unpin all of the bot's pins."""
    bot_pins = await message.channel.pins()
    for pin in bot_pins:
        if pin.author == client.user:  # If this bot created it
            await message.channel.send("Bosspile being unpinned:")
            await message.channel.send(pin.content)
            await message.bp_pin.unpin(reason=' '.join(args[1:]))
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


async def send_help(author):
    """Send the user a message explaining what this bot does."""
    about_msg = """Bosspile Bot: Manage your bosspiles like a wizard

This bot needs to manage its own pinned message. If it finds a pinned bosspile,
it will repin it as its own message. A pinned bosspile must have a crown and climber.
Reset this bot's bosspile by deleting its pinned message, ensuring there is a bosspile
pinned by a person and then run `$$p`."""
    help_msg = """

__**Available Commands**__

    Shorten a command to the first letter like `$$w` for `$$ win`.

    **win**: Updates the bosspile with a win by player 1 over player 2
            `win <player 1>`
    **new**: Add a player to the bottom of the bosspile
            `new <player>`
    **edit**: Change the line for a player to the new one. The old line must match exactly.
            `edit "<old player line>" "<new player line>"`
    **move**: Move a player/line up/down a number of spaces. Positive goes up; negative goes down.
            `move <player> <number of spaces>`
    **remove**: Remove a player from the bosspile
            `remove <player>`
    **active**: Change the status of a player to active or inactive (timer icon). If this bot sees a "player" with `**` or `__` (bold/italic markers) in their name, it treats it as an inactive heading.
            `active <player> <True|False>`
    **print**: Prints the current bosspile as a new message. Arg can be raw or debug, but is not required.
            `print <option>`


__**Examples**__

    Your discord name is `Alice` in these examples, all of which change the bosspile.

    **win**
        You won against Bob. (You don't need to include his name because of players with ⏫):
            `$$ win Alice`
        Expected Output includes result, as well as all new matches:
            `Alice defeats Bob`
            `Frank ⚔ Georgia`
            `Harriett ⚔ Ian`
    **new**
        You want to add player Charlie:
            `$$ new Charlie`
        Expected Output:
            `Charlie has been added.`

    **edit**
        You want to edit player "Bob" to add a large blue diamond and climbing
            `$$ edit "bob" "🔷Bob⏫"`
        Expected Output:
            `Bob ➡️ 🔷Bob⏫`

    **move**
        You want to move player "Bob" up 2 spaces
            `$$ move bob 2`

    **remove**
        You want to remove player Dan:
            `$$ remove Dan`
        Expected Output:
            `Dan has been removed.`

    **active**
        You want to make Eddie inactive and put a timer before his name:
            `$$ active Eddie false`
        Expected Output:
            `Eddie is now inactive.`
"""
    truncated_help_msg = help_msg.replace(4*" ", "\t")  # 2000 chars adds up quick
    await author.send(about_msg)
    await author.send(truncated_help_msg)


client.run(TOKEN)
