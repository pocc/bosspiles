"""Bosspiles for use by BGA bosspiles discord server"""
import re


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
        # See regex w examples: https://regex101.com/r/iF4cVx/3 , used to parse one player line
        self.player_line_re = re.compile(r"(?:^|\n)\s*(?::[a-z_]*: ?)* *(\w+(?: \w+)*) *(?::[a-z_]*:)*")

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
                    return player_pos, f"Multiple matching players found at {player_pos} and {i}. No changes made."
                player_pos = i
        return player_pos, err

    def win(self, victor):
        """p1 has won the game. p1 is climbing. p2 stops climbing.
        The list of messages sent as a result of winning are saved in the messages list."""
        victor_pos, err_msg = self.find_player_pos(victor)
        if victor_pos == -1:
            return [f"`{victor}` is not a valid player name. You may need to quote."]
        elif len(err_msg) > 0:
            return [err_msg]
        # If you are climbing, then you move and you played the person above.
        if self.players[victor_pos].climbing:
            loser_pos = victor_pos - 1
        else:  # Otherwise you defended a challenge
            loser_pos = victor_pos + 1
        if not (self.players[victor_pos].climbing ^ self.players[loser_pos].climbing):
            return ["An invalid match was detected: 0 or 2 climbers found. No changes made."]
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
                messages += [f"{p2_name} goes down {str(num_down - 1)} spaces."]
                self.players = self.players[1:num_down+1] + [self.players[0]] + self.players[num_down+1:]
        # If winner is higher in array (lower in ladder), players switch places
        elif victor_pos > loser_pos:
            self.players[victor_pos], self.players[loser_pos] = self.players[loser_pos], self.players[victor_pos]
        # If user is boss and wins, add an orange diamond
        if victor_pos == 0:
            messages += [self.players[victor_pos].username
                         + " has defended the :crown: and gains :small_orange_diamond:"]
            self.players[victor_pos].orange_diamonds += 1
        # Last player should always be climbing.
        self.players[-1].climbing = True
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
        if self.find_player_pos(player_name):
            return f"{player_name} is already in the bosspile."
        new_player = PlayerData(player_name)
        self.players.append(new_player)
        self.players[-1].climbing = True
        return f"{player_name} has been added successfully."

    def edit(self, new_line):
        """Edit an existing player."""
        new_player = self.parse_bosspile_line(new_line)
        new_player_pos, err_msg = self.find_player_pos(new_player.username)
        if new_player_pos != -1:
            old_username = self.players[new_player_pos].username
            self.players[new_player_pos] = self.parse_bosspile_line(new_line)
            return f"{old_username} is now️ {new_line}"
        elif len(err_msg) > 0:
            return err_msg
        return f"Player not found in `{new_line}`. No line changed."

    def remove(self, player_name):
        """Delete a player from the leaderboard. Returns whether there was a successful deletion or not."""
        for i in range(len(self.players)):
            if player_name == self.players[i].username:
                del self.players[i]
                return True
        return False

    def change_active_status(self, player_name, state):
        """Make a player active/inactive."""
        for i in range(len(self.players)):
            if player_name == self.players[i].username:
                self.players[i].active = state

    def parse_bosspile(self, bosspile_text: str):
        """Read the bosspile text and convert it into players"""
        # Crown is pointless because it only signifies leader
        bosspile_text = bosspile_text.replace(":crown:", "")
        player_lines = bosspile_text.strip().split('\n')
        all_player_data = []
        for player_line in player_lines:
            player = self.parse_bosspile_line(player_line)
            all_player_data.append(player)
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
