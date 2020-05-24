"""Discord client."""
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
    listening_to_help = discord.Activity(type=discord.ActivityType.listening, name="!bp")
    await client.change_presence(activity=listening_to_help)


@client.event
async def on_message(message):
    """Listen to messages so that this bot can do something."""
    if message.author == client.user:
        return

    # Like $bp command
    if message.content.startswith('!bp'):
        await run_bosspiles(message)


async def parse_args(message):
    """Parse the args and tell the user if they are not valid."""
    args = shlex.split(message.content[3:])
    if len(args) == 0:  # on `!bp`
        await send_help(message.author)
    elif args[0] not in ["add", "win", "remove", "active", "print"]:
        await message.channel.send(f"`!bp {args[0]}` is not recognized subcommand. See `!bp`.")
    elif args[0] in ["add", "win", "remove"] and len(args) != 2:
        await message.channel.send(f"`!bp {args[0]}` requires 3 arguments. See `!bp`.")
    elif args[0] in ["active"] and len(args) != 3:
        await message.channel.send(f"`!bp {args[0]}` requires 4 arguments. See `!bp`.")
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


async def execute_command(message, args, bosspile):
    """Execute the !bp command the user has entered."""
    if args[0].startswith("win"):
        victor = args[1]
        win_messages = bosspile.win(victor)
        [await message.channel.send(m) for m in win_messages]
    elif args[0].startswith("add"):
        player_name = args[1]
        bosspile.add(player_name)
        await message.channel.send(f"{player_name} has been added.")
    elif args[0].startswith("remove"):
        player_name = args[1]
        if len(bosspile.players) <= 2:
            await message.channel.send("A bosspile must have at least 2 players. Skipping player deletion.")
        was_player_removed = bosspile.remove(player_name)
        if was_player_removed:
            await message.channel.send(f"{player_name} has been removed.")
        else:
            await message.channel.send(f"{player_name} does not exist in the bosspile and so was not removed.")
    elif args[0].startswith("active"):
        player_name = args[1]
        state = args[2].lower() == "true"
        bosspile.change_active_status(player_name, state)
        await message.channel.send(f"{player_name} is now {'in'*(not state)}active.")
    elif args[0].startswith("print"):
        bosspile_to_be_printed = bosspile.generate_bosspile()
        await message.channel.send(bosspile_to_be_printed)
    else:
        await message.channel.send(f"Unrecognized command {args[0]}. Run `!bp`.")


async def run_bosspiles(message):
    """Run the bosspiles program ~ main()."""
    print(f"Received message `{message.content}`")
    args = await parse_args(message)

    bp_pin = await get_pinned_bosspile(message)
    # We can only edit our own messages
    edit_existing_bp = bp_pin.author == client.user
    # We can change the board game name, but I'm not sure it matters.
    bosspile = BossPile("Can't stop", bp_pin.content)
    await execute_command(message, args, bosspile)

    new_bosspile = bosspile.generate_bosspile()
    if new_bosspile != bp_pin.content:
        if edit_existing_bp:
            await bp_pin.edit(content=new_bosspile)
        else:
            new_msg = await message.channel.send(new_bosspile)
            await new_msg.pin()
            await message.channel.send("Created new bosspile pin because this bot can only edit its own messages.")


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
    await author.send("""Bosspile Bot : Manage bosspiles for you automagically
`Available Commands`
`==================`
    
    **win** <player 1> <player 2>
        Updates the bosspile with a win by player 1 over player 2

    **add** <player>
        Add a player to the bottom of the bosspile

    **remove** <player>
        Remove a player from the bosspile

    **active** <player> <"true" or "false">
        Change the status of a player to active or inactive (timer icon)
    
    **print**
        Prints the current bosspile as a new message.
    
`Examples`
`========`
    
    For these examples, your discord name is `Alice`.
    All of these options change the bosspile.
    
    **win**
        You won against Bob. (You don't need to include his name because of ^^ emojis):
            `!bp win Alice`
        
        Expected Output includes result, as well as all new matches:
            `Alice defeats Bob`
            `Frank ⚔ Georgia`
            `Harriett ⚔ Ian`
    **add**
        You want to add player Charlie:
            `!bp add Charlie`
        
        Expected Output:
            `Charlie has been added.`
    
    **remove**
        You want to remove player Dan:
            `!bp remove Dan`
        
        Expected Output:
            `Dan has been removed.`

    **active**
        You want to make Eddie inactive and put a timer before his name:
            `!bp active Eddie false`
        
        Expected Output:
            `Eddie is now inactive.`
""")


client.run(TOKEN)
