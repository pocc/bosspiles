"""Discord client."""
import json
import shlex

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
        except GracefulCoroutineExit:
            pass


async def parse_args(message):
    """Parse the args and tell the user if they are not valid."""
    args = shlex.split(message.content[2:])
    if len(args) == 0:  # on `$$`
        await send_help(message.author)
    # only first letter has to match
    elif args[0][0] not in [w[0] for w in ["new", "win", "edit", "remove", "active", "print"]]:
        await message.channel.send(f"`$$ {args[0]}` is not a recognized subcommand. See `$$`.")
    elif args[0][0] in [w[0] for w in ["new", "edit", "win", "remove"]] and len(args) != 2:
        await message.channel.send(f"`$$ {args[0]}` requires 3 arguments. See `$$`.")
    elif args[0][0] in [w[0] for w in ["active"]] and len(args) != 3:
        await message.channel.send(f"`$$ {args[0]}` requires 4 arguments. See `$$`.")
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
                and (":arrow_double_up:" in pin.content or "⏫" in pin.content):
            return pin
    await message.channel.send("This channel has no bosspile! Pin your bosspile message and try again.")
    raise GracefulCoroutineExit("Channel has pins but no bosspile!")


async def execute_command(args, bosspile):
    """Execute the $$ command the user has entered and return a message."""
    args[0] = args[0].lower()
    if args[0].startswith("w"):  # win
        victor = args[1]
        return bosspile.win(victor)
    elif args[0].startswith("n"):  # new
        player_name = args[1]
        return bosspile.add(player_name)
    elif args[0].startswith("e"):  # edit
        new_line = args[1]
        return bosspile.edit(new_line)
    elif args[0].startswith("r"):  # remove
        player_name = args[1]
        return bosspile.remove(player_name)
    elif args[0].startswith("a"):  # active
        player_name = args[1]
        state = args[2].lower().startswith("t")  # t for true, anything else is false
        return bosspile.change_active_status(player_name, state)
    elif args[0].startswith("p"):  # print
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

    bp_pin = await get_pinned_bosspile(message)
    # We can only edit our own messages
    edit_existing_bp = bp_pin.author == client.user
    # We can change the board game name, but I'm not sure it matters.
    bosspile = BossPile("Can't stop", bp_pin.content)
    return_message = await execute_command(args, bosspile)

    new_bosspile = bosspile.generate_bosspile()
    if new_bosspile != bp_pin.content:
        if edit_existing_bp:
            await bp_pin.edit(content=new_bosspile)
        else:
            new_msg = await message.channel.send(new_bosspile)
            await new_msg.pin()
            await message.channel.send("Created new bosspile pin because this bot can only edit its own messages.")
    return return_message


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
    help_msg = """Bosspile Bot: Manage your bosspiles like a wizard

This bot needs to manage its own pinned message. If it finds a pinned bosspile,
it will repin it as its own message. A pinned bosspile must have a crown and climber.
Reset this bot's bosspile by deleting its pinned message, ensuring there is a bosspile
pinned by a person and then run `$$p`.


__**Available Commands**__

    Shorten a command to the first letter like `$$w` for `$$ win`.

    **win**: Updates the bosspile with a win by player 1 over player 2
            `win <player 1>`
    **new**: Add a player to the bottom of the bosspile
            `new <player>`
    **edit**: Change the line for a player to the new one.
            `edit "<new player line>"`
    **remove**: Remove a player from the bosspile
            `remove <player>`
    **active**: Change the status of a player to active or inactive (timer icon)
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
            `$$ edit "🔷Bob⏫"`
        Expected Output:
            `Bob ➡️ 🔷Bob⏫`

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
    await author.send(truncated_help_msg)


client.run(TOKEN)
