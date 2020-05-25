import unittest
import random

from bosspiles import BossPile
from examples import example_bosspile, expected_bosspile_1000
import emoji


class TestClass(unittest.TestCase):
    def setUp(self):
        """Setup the function."""
        print("Starting...")

    def test_bosspiles(self):
        """main test"""
        bosspile = BossPile("Can't Stop", example_bosspile)
        messages = []
        messages += [bosspile.add("nobody")]
        messages += [bosspile.remove("imay")]
        messages += [bosspile.edit(":large_blue_diamond: kingneal")]
        print(messages)
        # 1000 random numbers, but generated the same way
        random.seed(0)
        random_player_numbers = [random.randint(0, 9) for _ in range(1000)]
        print("starting bosspile")
        print_emojified_bosspile(bosspile)
        # Get valid matches and then randomly have someone win.
        for i in random_player_numbers:
            matches = bosspile.generate_matches()
            players = []
            for m in matches:
                players += list(m)
            victor_pos = players[i % len(players)]
            victor = bosspile.players[victor_pos].username
            print(victor, "wins!")
            print(bosspile.win(victor))
            print_emojified_bosspile(bosspile)
        self.assertEqual(expected_bosspile_1000, bosspile.generate_bosspile())


def print_emojified_bosspile(bosspile):
    """Print the bosspile, but with emojis."""
    print(emoji.emojize(bosspile.generate_bosspile()).replace(":arrow_double_up:", "⏫"))
