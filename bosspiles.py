"""Bosspiles for use by BGA bosspiles discord server"""
import re
import shlex

import discord

from keys import TOKEN

client = discord.Client()


@client.event
async def on_ready():
    """Let the user who started the bot know that the connection succeeded."""
    print(f'{client.user.name} has connected to Discord!')


@client.event
async def on_message(message):
    """Listen to messages so that this bot can do something."""
    if message.author == client.user:
        return

    # Like $bp command
    if message.content.startswith('!bp'):
        print(f"Received message `{message.content}`")
        args = shlex.split(message.content[3:])
        if len(args) < 2:
            await send_help(message.channel)
            return
        if args[0] in ["add", "remove"] and len(args) != 2:
            await message.channel.send(f"`!bp {args[1]}` requires 3 arguments. See `!bp`.")
            return
        if args[0] in ["win", "active"] and len(args) != 3:
            await message.channel.send(f"`!bp {args[1]}` requires 4 arguments. See `!bp`.")
            return
        pins = await message.channel.pins()
        if len(pins) == 0:
            await message.channel.send("This channel has no pins (a pinned bosspile is required)")
            return
        bp_message = None
        edit_existing_bp = False
        for pin in pins:
            if ":crown:" in pin.content and ":arrow_double_up:" in pin.content:
                bp_message = pin
                # We can only edit our own messages
                edit_existing_bp = pin.author == client.user
                break
        if not bp_message:
            await message.channel.send("This channel has no bosspile! Pin a your bosspile message and try again.")
            return
        bosspile = BossPile("Can't stop", bp_message.content)
        if args[0] == "win":
            victor = args[1]
            loser = args[2]
            win_messages = bosspile.win(victor, loser)
            [await message.channel.send(m) for m in win_messages]
        elif args[0] == "add":
            player_name = args[1]
            bosspile.add(player_name)
            await message.channel.send(f"{player_name} has been added.")
        elif args[0] == "remove":
            player_name = args[1]
            bosspile.remove(player_name)
            await message.channel.send(f"{player_name} has been removed.")
        elif args[0] == "active":
            player_name = args[1]
            state = args[2].lower() == "true"
            bosspile.change_active_status(player_name, state)
            await message.channel.send(f"{player_name} is now {'in'*(not state)}active.")
        else:
            await message.channel.send(f"Unrecognized command {args[1]}. Run `!bp`.")
        new_bosspile = bosspile.generate_bosspile()
        if new_bosspile != bp_message.content:
            if edit_existing_bp:
                await bp_message.edit(content=new_bosspile)
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


async def send_help(channel):
    """Send the user a message explaining what this bot does."""
    await channel.send("""Bosspile Bot : Manage bosspiles for you automagically
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
    
`Examples`
`========`
    
    For these examples, your discord name is `Alice`.
    All of these options change the bosspile.
    
    **win**
        You won against Bob:
            `!bg win Alice Bob`
        
        Expected Output includes result, as well as all new matches:
            `Bob has lost to Alice`
            `Frank ⚔ Georgia`
            `Harriett ⚔ Ian`
    **add**
        You want to add player Charlie:
            `!bg add Charlie`
        
        Expected Output:
            `Charlie has been added.`
    
    **remove**
        You want to remove player Dan:
            `!bg remove Dan`
        
        Expected Output:
            `Dan has been removed.`

    **active**
        You want to make Eddie inactive and put a timer before his name:
            `!bg active Eddie false`
        
        Expected Output:
            `Eddie is now inactive.`
""")


class PlayerData:
    """Denotes one player"""
    def __init__(self, username: str, orange_diamonds=0, blue_diamonds=0, climbing=False, active=True):
        self.username = username
        self.orange_diamonds = orange_diamonds
        self.blue_diamonds = blue_diamonds
        self.climbing = climbing
        self.active = active


class BossPile:
    """Class to keep track of players and their rankings"""
    def __init__(self, game: str, bosspile_text: str):
        self.game = game
        self.players = self.parse_bosspile(bosspile_text)

    def win(self, p1, p2):
        """p1 has won the game. p1 is climbing. p2 stops climbing."""
        p1_pos = -1
        p2_pos = -1
        for i in range(len(self.players)):
            player = self.players[i]
            if player.username == p1:
                p1_pos = i
            if player.username == p2:
                p2_pos = i
        if p1_pos == -1:
            return [f"`{p1}` is not a valid player name. You may need to quote."]
        if p2_pos == -1:
            return [f"`{p2}` is not a valid player name. You may need to quote."]
        if not (self.players[p1_pos].climbing ^ self.players[p2_pos].climbing):
            return ["An invalid match was detected: 0 or 2 climbers found. No changes made."]
        if abs(p1_pos - p2_pos) != 1:
            return ["An invalid match was detected: Players are not adjacent. No changes made."]
        messages = []
        self.players[p1_pos].climbing = True
        self.players[p2_pos].climbing = False
        # If user is boss and loses, move to bottom and convert 5 orange => blue
        if p2_pos == 0:
            messages += [self.players[p2_pos].username + " has lost the :crown: to " + self.players[p1_pos].username]
            blue_diamonds = self.players[p2_pos].orange_diamonds // 5
            if blue_diamonds > 0:
                self.players[p2_pos].blue_diamonds += blue_diamonds
                messages += [self.players[p2_pos].username + " has gained a :large_blue_diamond: and descends"]
            self.players[p2_pos].orange_diamonds %= 5
            self.players[p2_pos].climbing = True
            self.players = self.players[1:] + [self.players[0]]  # move player to end
        # If winner is higher in array (lower in ladder), players switch places
        elif p1_pos > p2_pos:
            temp = self.players[p1_pos]
            self.players[p1_pos] = self.players[p2_pos]
            self.players[p2_pos] = temp
            messages += [self.players[p2_pos].username + " has lost to " + self.players[p1_pos].username]
        # If user is boss and wins, add an orange diamond
        if p1_pos == 0:
            messages += [self.players[p1_pos].username + " has defended the :crown: and gains :small_orange_diamond:"]
            self.players[p1_pos].orange_diamonds += 1
        new_matches = self.generate_matches()
        for match in new_matches:
            messages += [f"{self.players[match[0]].username} :crossed_swords: {self.players[match[1]].username}"]
        return messages

    def generate_matches(self):
        """Create the matches based on who is climbing."""
        matches = []
        for i in range(len(self.players)):
            if i > 0 and self.players[i].climbing and not self.players[i-1].climbing:
                matches.append((i, i-1))
        return matches

    def add(self, player_name):
        """Add a player to the very end."""
        new_player = PlayerData(player_name)
        self.players.append(new_player)
        self.players[-1].climbing = True

    def remove(self, player_name):
        """Delete a player from the leaderboard."""
        for i in range(len(self.players)):
            if player_name == self.players[i].username:
                del self.players[i]
                break

    def change_active_status(self, player_name, state):
        """Make a player active/inactive."""
        for i in range(len(self.players)):
            if player_name == self.players[i].username:
                self.players[i].active = state

    @staticmethod
    def parse_bosspile(bosspile_text: str):
        """Read the bosspile text and convert it into players"""
        # Replace emojis with discord names
        bosspile_text = bosspile_text.replace("👑", ":crown:").replace("🔸", ":small_orange_diamond:")\
            .replace("🔶", ":large_orange_diamond:").replace("🔷", ":large_blue_diamond:")\
            .replace("⏫", ":arrow_double_up:").replace("💭", ":thought_balloon:")
        # Crown is pointless because it only signifies leader
        bosspile_text = bosspile_text.replace(":crown:", "")
        player_lines = bosspile_text.strip().split('\n')
        # regex: https://regex101.com/r/iF4cVx/1
        regex = re.compile(r"(?:^|\n)\s*(?::[a-z_]*: ?)* *(\w[a-zA-Z0-9 ]+\w) *(?::[a-z_]*:)*")
        all_player_data = []
        for i in range(len(player_lines)):
            player_text = player_lines[i]
            orange_diamonds = player_text.count(":small_orange_diamond:")
            orange_diamonds += 5 * player_text.count(":large_orange_diamond:")
            blue_diamonds = player_text.count(":large_blue_diamond:")
            username = regex.findall(player_text)[0]
            climbing = ":arrow_double_up:" in player_text or ":thought_balloon:" in player_text
            active = ":timer:" not in player_text
            player = PlayerData(username, orange_diamonds, blue_diamonds, climbing, active)
            all_player_data.append(player)
        return all_player_data

    def generate_bosspile(self):
        """Generate the bosspile text from the stored configuration."""
        bosspile_text = ":crown:"
        prev_player_climbing = False
        for i in range(len(self.players)):
            player = self.players[i]
            if not player.active:  # Symbol for inactive players
                bosspile_text += ":timer:"
            bosspile_text += player.blue_diamonds * ":large_blue_diamond:"
            bosspile_text += (player.orange_diamonds//5) * ":large_orange_diamond:"
            bosspile_text += (player.orange_diamonds % 5) * ":small_orange_diamond:"
            bosspile_text += f" {player.username} "
            # :arrow_double_up: and :cloud: are both climbing
            # Use :cloud: if the player above has :arrow_double_up: or :cloud:
            is_boss = i == 0
            if not is_boss:
                if player.climbing:
                    if not prev_player_climbing:
                        bosspile_text += ":arrow_double_up:"
                    else:
                        bosspile_text += ":thought_balloon:"
                prev_player_climbing = player.climbing
            bosspile_text += '\n'
        return bosspile_text




client.run(TOKEN)
