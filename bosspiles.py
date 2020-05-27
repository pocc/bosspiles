"""Bosspiles for use by BGA bosspiles discord server"""
import re

MINIMUM_BOSSPILE_PLAYERS = 3


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
        # See regex w examples: https://regex101.com/r/iF4cVx/6 , used to parse one player line
        regex = r"(?:^|\n)\s*(?::[a-z_]*: ?)* *~*([\w(),]+(?: *[\w(),]+)*)~* *(?::[a-z_]*:)* *$"
        self.player_line_re = re.compile(regex)

        self.players = self.parse_bosspile(bosspile_text)

    def find_player_pos(self, player_name):
        """Find the player position in the player list or -1 and error"""
        player_pos = -1
        err = ""
        for i in range(len(self.players)):
            player = self.players[i]
            if player.username.startswith(player_name):
                # If there's ambiguity, treat it as not found.
                if player_pos != -1:
                    return player_pos, f"Multiple matching players found for `{player_name}`" \
                        f" at positions {player_pos} and {i}. No changes made."
                player_pos = i
        if player_pos == -1:
            return player_pos, f"Player {player_name} not found. No changes made."
        return player_pos, err

    def win(self, victor):
        """p1 has won the game. p1 is climbing. p2 stops climbing.
        The list of messages sent as a result of winning are saved in the messages list."""
        victor_pos, err_msg = self.find_player_pos(victor)
        victor_is_boss = victor_pos == 0
        if victor_pos == -1:
            return f"`{victor}` is not a valid player name. You may need to quote."
        elif len(err_msg) > 0:
            return err_msg
        # If you are climbing, then you move and you played the person above.
        if self.players[victor_pos].climbing and not victor_is_boss:
            loser_pos = victor_pos - 1
        else:  # Otherwise you defended a challenge
            loser_pos = victor_pos + 1
        num_climbers = self.players[victor_pos].climbing + self.players[loser_pos].climbing
        if num_climbers != 1:
            return f"{num_climbers} climbers found (1 required) at positions " \
                f"{victor_pos}/{loser_pos}. No changes made."
        messages = [self.players[victor_pos].username + " defeats " + self.players[loser_pos].username]
        self.players[victor_pos].climbing = True
        self.players[loser_pos].climbing = False
        # If user is boss and loses, move to bottom and convert 5 orange => blue
        if loser_pos == 0:
            p1_name = self.players[victor_pos].username
            p2_name = self.players[loser_pos].username
            messages += [f"{p2_name} has lost the :crown: to {p1_name}"]
            new_blue_diamonds = self.players[loser_pos].orange_diamonds // 5
            self.players[loser_pos].orange_diamonds %= 5
            if new_blue_diamonds > 0:
                self.players[loser_pos].blue_diamonds += new_blue_diamonds
                messages += [f"{p2_name} has gained a :large_blue_diamond: and is now at the bottom."]
                self.players = self.players[1:] + [self.players[0]]  # move player to end
            else:  # Move them down how many orange diamonds they gained + 1 fencepost error
                num_down = self.players[loser_pos].orange_diamonds + 1
                # Don't interrupt an existing game
                messages += [f"{p2_name} goes down {str(num_down)} spaces."]
                if num_down < len(self.players) and \
                        self.players[num_down+1].climbing and not self.players[num_down].climbing:
                    num_down += 1
                    messages += [f"{p2_name} goes down an additional space to not interrupt a game."]
                self.players = self.players[1:num_down+1] + [self.players[0]] + self.players[num_down+1:]
        # If winner is higher in array (lower in ladder), players switch places
        elif victor_pos > loser_pos:
            self.players[victor_pos], self.players[loser_pos] = self.players[loser_pos], self.players[victor_pos]
        # If user is boss and wins, add an orange diamond
        if victor_is_boss:
            messages += [self.players[victor_pos].username
                         + " has defended the :crown: and gains :small_orange_diamond:"]
            self.players[victor_pos].orange_diamonds += 1
        self.set_climbing_invariants()
        new_matches = self.generate_matches()
        for match in new_matches:
            messages += [f"{self.players[match[0]].username} :crossed_swords: {self.players[match[1]].username}"]
        paragraph_message = "\n".join(messages)
        return paragraph_message

    def set_climbing_invariants(self):
        """There are climbing invariants that need to be imposed on players.
        Last *active* player should always be climbing and king (first player) should never be."""
        lowest_active = len(self.players) - 1
        while not self.players[lowest_active].active:
            lowest_active -= 1
        self.players[lowest_active].climbing = True
        self.players[0].climbing = False

    def generate_matches(self):
        """Create the matches based on who is climbing."""
        matches = []
        active_players = [p for p in self.players if p.active]
        for i in range(len(active_players)):
            if i > 0 and active_players[i].climbing and not active_players[i-1].climbing:
                matches.append((i, i-1))
        return matches

    def add(self, player_name):
        """Add a player to the very end."""
        pos, err = self.find_player_pos(player_name)
        if pos != -1:
            return f"{player_name} is already in the bosspile. No changes made."
        new_player = PlayerData(player_name)
        self.players.append(new_player)
        self.players[-1].climbing = True  # by definition this new player is active
        return f"{player_name} has been added successfully."

    def edit(self, new_line):
        """Edit an existing player."""
        new_player = self.parse_bosspile_line(new_line)
        new_player_pos, err_msg = self.find_player_pos(new_player.username)
        if new_player_pos != -1:
            old_username = self.players[new_player_pos].username
            self.players[new_player_pos] = self.parse_bosspile_line(new_line)
            self.set_climbing_invariants()
            return f"{old_username} is now️ {new_line}"
        elif len(err_msg) > 0:
            return err_msg
        return f"Player not found in `{new_line}`. No line changed."

    def remove(self, player_name):
        """Delete a player from the leaderboard. Returns whether there was a successful deletion or not."""
        if len(self.players) <= MINIMUM_BOSSPILE_PLAYERS:
            return f"A bosspile must have at least {MINIMUM_BOSSPILE_PLAYERS} players. Skipping player deletion."
        player_pos, err = self.find_player_pos(player_name)
        if len(err) > 0:
            return err
        del self.players[player_pos]
        return f"{player_name} has been removed."

    def change_active_status(self, player_name, is_active):
        """Make a player active/inactive."""
        player_pos, err = self.find_player_pos(player_name)
        if len(err) > 0:
            return err
        self.players[player_pos].active = is_active
        username = self.players[player_pos].username
        if player_pos == 0:  # If boss is made inactive, move them down a spot
            self.players = [self.players[1], self.players[0], *self.players[2:]]
        self.set_climbing_invariants()
        return f"{username} is now {'in'*(not is_active)}active."

    def parse_bosspile(self, bosspile_text: str):
        """Read the bosspile text and convert it into players"""
        # Crown is pointless because it only signifies leader
        bosspile_text = bosspile_text.replace(":crown:", "")
        player_lines = bosspile_text.strip().split('\n')
        player_lines = list(filter(None, player_lines))  # Removes empty values
        all_player_data = []
        for player_line in player_lines:
            line_is_heading = player_line[0] == '_' or player_line[0] == '*'
            if not line_is_heading:
                player = self.parse_bosspile_line(player_line)
                all_player_data.append(player)
        # These are invariant climbing statuses for King/Pauper
        all_player_data[0].climbing = False
        all_player_data[-1].climbing = True
        return all_player_data

    @staticmethod
    def parse_emojis_as_discord_text(bosspile_text):
        """Replace emojis with discord emoji names with colons."""
        bosspile_text = bosspile_text.replace("👑", ":crown:").replace("🔸", ":small_orange_diamond:")\
            .replace("🔶", ":large_orange_diamond:").replace("🔷", ":large_blue_diamond:")\
            .replace("⏫", ":arrow_double_up:").replace("💭", ":thought_balloon:")
        return bosspile_text

    def parse_bosspile_line(self, player_line: str):
        """Parse one line of the bosspile and return a player line."""
        player_line = self.parse_emojis_as_discord_text(player_line)
        orange_diamonds = player_line.count(":small_orange_diamond:")
        orange_diamonds += 5 * player_line.count(":large_orange_diamond:")
        blue_diamonds = player_line.count(":large_blue_diamond:")
        username = self.player_line_re.findall(player_line)[0]
        climbing = ":arrow_double_up:" in player_line or ":thought_balloon:" in player_line
        active = ":timer:" not in player_line
        player = PlayerData(username, orange_diamonds, blue_diamonds, climbing, active)
        return player

    def generate_bosspile(self):
        """Generate the bosspile text from the stored configuration."""
        bosspile_text = "__**Bosspile Standings**__\n\n:crown:"
        prev_player_climbing = False
        for player in self.players:
            bosspile_text += self.generate_bosspile_line(player, prev_player_climbing)
            prev_player_climbing = player.climbing
        return bosspile_text

    @staticmethod
    def generate_bosspile_line(player, prev_player_climbing=False):
        """Generate one line of bosspile. If there are previous players, which climbing symbol
        is used depends on if the previous player has a climbing symbol."""
        bosspile_line = ""
        if not player.active:
            bosspile_line += f":timer:~~{player.username}~~:timer:"
        else:
            bosspile_line += player.blue_diamonds * ":large_blue_diamond:"
            bosspile_line += (player.orange_diamonds//5) * ":large_orange_diamond:"
            bosspile_line += (player.orange_diamonds % 5) * ":small_orange_diamond:"
            bosspile_line += f" {player.username} "
            # :arrow_double_up: and :cloud: are both climbing
            # Use :cloud: if the player above has :arrow_double_up: or :cloud:
            if player.climbing:
                if not prev_player_climbing:
                    bosspile_line += ":arrow_double_up:"
                else:
                    bosspile_line += ":thought_balloon:"
        bosspile_line += '\n'
        return bosspile_line
