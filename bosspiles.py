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
        self.players = self.parse_bosspile(bosspile_text)

    def win(self, p1):
        """p1 has won the game. p1 is climbing. p2 stops climbing.
        The list of messages sent as a result of winning are saved in the messages list."""
        p1_pos = -1
        for i in range(len(self.players)):
            player = self.players[i]
            if player.username == p1:
                p1_pos = i
        if p1_pos == -1:
            return [f"`{p1}` is not a valid player name. You may need to quote."]
        # If you are climbing, then you move and you played the person above.
        if self.players[p1_pos].climbing:
            p2_pos = p1_pos - 1
        else:  # Otherwise you defended a challenge
            p2_pos = p1_pos + 1
        if not (self.players[p1_pos].climbing ^ self.players[p2_pos].climbing):
            return ["An invalid match was detected: 0 or 2 climbers found. No changes made."]
        messages = [self.players[p1_pos].username + " defeats " + self.players[p2_pos].username]
        self.players[p1_pos].climbing = True
        self.players[p2_pos].climbing = False
        # If user is boss and loses, move to bottom and convert 5 orange => blue
        if p2_pos == 0:
            p1_name = self.players[p1_pos].username
            p2_name = self.players[p2_pos].username
            messages += [f"{p1_name} has lost the :crown: to {p2_name}"]
            new_blue_diamonds = self.players[p2_pos].orange_diamonds // 5
            self.players[p2_pos].orange_diamonds %= 5
            self.players[p2_pos].climbing = True
            if new_blue_diamonds > 0:
                self.players[p2_pos].blue_diamonds += new_blue_diamonds
                messages += [f"{p2_name} has gained a :large_blue_diamond: and is now at the bottom."]
                self.players = self.players[1:] + [self.players[0]]  # move player to end
            else:  # Move them down how many orange diamonds they gained + 1
                num_down = self.players[p2_pos].orange_diamonds + 1
                messages += [f"{p1_name} goes down {str(num_down)} spaces."]
                self.players = self.players[1:num_down+1] + [self.players[0]] + self.players[num_down+1:]
        # If winner is higher in array (lower in ladder), players switch places
        elif p1_pos > p2_pos:
            self.players[p1_pos], self.players[p2_pos] = self.players[p2_pos], self.players[p1_pos]
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
        # regex: https://regex101.com/r/iF4cVx/3
        regex = re.compile(r"(?:^|\n)\s*(?::[a-z_]*: ?)* *(\w+(?: \w+)*) *(?::[a-z_]*:)*")
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
