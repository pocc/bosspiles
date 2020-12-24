# coding: utf-8
"""Limited tests."""
from bosspiles import BossPile


POTION_EXPLOSION_BOSSPILE = """__**2-3P POTION EXPLOSION VBOSSPILE**__

:crown: nmego (2P ok)
YourPetWerewolf :arrow_double_up:
montesat
kingneal (2P ok)
Sharzi (2P ok) :arrow_double_up:
myopic2000
Takorina :arrow_double_up:"""


def assert_equal(left, right):
    if left != right:
        print(f"Expecting `{left}` but got `{right}`")
    else:
        print("Test passed!")


def test_2p_bosspile_crown_win():
    """Test that a crown gets a small orange diamond in a 2p bosspile"""
    bp = BossPile("potionexplosion", [], POTION_EXPLOSION_BOSSPILE)
    bp.title_line = "__**Bosspile Standings**__"
    bp.win("nmego")
    new_bosspile = """__**Bosspile Standings**__

:crown: :small_orange_diamond: nmego (2P ok)
YourPetWerewolf
montesat
kingneal (2P ok)
Sharzi (2P ok) :arrow_double_up:
myopic2000
Takorina :arrow_double_up:
"""
    assert_equal(new_bosspile, bp.generate_bosspile())


def test_3p_bosspile_2p_win():
    """Test 2 player win in a 2-3 prefer 3 player bosspile."""
    bp = BossPile("potionexplosion", [], POTION_EXPLOSION_BOSSPILE)
    bp.win("myopic2000")
    new_bosspile = """__**2-3P POTION EXPLOSION VBOSSPILE**__

:crown: nmego (2P ok)
YourPetWerewolf :arrow_double_up:
montesat
kingneal (2P ok)
Sharzi (2P ok) :arrow_double_up:
myopic2000 :thought_balloon:
Takorina :thought_balloon:
"""
    assert_equal(new_bosspile, bp.generate_bosspile())


def test_3p_bosspile_3p_bottom_player_wins():
    """Test 3 player win in a 2-3 prefer 3 player bosspile. Sharzi wins and goes up 2."""
    bp = BossPile("potionexplosion", [], POTION_EXPLOSION_BOSSPILE)
    bp.win("sharzi")
    new_bosspile = """__**2-3P POTION EXPLOSION VBOSSPILE**__

:crown: nmego (2P ok)
YourPetWerewolf :arrow_double_up:
Sharzi (2P ok) :thought_balloon:
montesat
kingneal (2P ok)
myopic2000
Takorina :arrow_double_up:
"""
    assert_equal(new_bosspile, bp.generate_bosspile())


def test_3p_bosspile_3p_middle_player_wins():
    """kingneal wins and goes up one."""
    bp = BossPile("potionexplosion", [], POTION_EXPLOSION_BOSSPILE)
    bp.win("kingneal")
    new_bosspile = """__**2-3P POTION EXPLOSION VBOSSPILE**__

:crown: nmego (2P ok)
YourPetWerewolf :arrow_double_up:
kingneal (2P ok) :thought_balloon:
montesat
Sharzi (2P ok)
myopic2000
Takorina :arrow_double_up:
"""
    assert_equal(new_bosspile, bp.generate_bosspile())


def test_3p_bosspile_3p_top_player_wins():
    """montesat wins and stays in the same position."""
    bp = BossPile("potionexplosion", [], POTION_EXPLOSION_BOSSPILE)
    bp.win("montesat")
    new_bosspile = """__**2-3P POTION EXPLOSION VBOSSPILE**__

:crown: nmego (2P ok)
YourPetWerewolf :arrow_double_up:
montesat :thought_balloon:
kingneal (2P ok)
Sharzi (2P ok)
myopic2000
Takorina :arrow_double_up:
"""
    assert_equal(new_bosspile, bp.generate_bosspile())


def main():
    test_2p_bosspile_crown_win()
    test_3p_bosspile_2p_win()
    test_3p_bosspile_3p_bottom_player_wins()
    test_3p_bosspile_3p_middle_player_wins()
    test_3p_bosspile_3p_top_player_wins()


main()


# Catching past errors
def test_multiple_parentheses():
    weird_line = ":crown: nmego (2P ok) (:star:)"
    expected = """Unable to parse line `:crown: nmego (2P ok) (:star:)`.
Player name can only contain alphanumeric characters, `_`, `.`, and spaces.
Preferences must all be within one () and can contain alphanumeric characters, `,`, `_`, `:`, and spaces."""
    bp = BossPile("potionexplosion", [], POTION_EXPLOSION_BOSSPILE)
    result = bp.edit("nmego", weird_line)
    assert_equal(expected, result)


def inactive_players_dont_prevent_generated_matchups():
    """Previous error was that a matchup wasn't recognized as generated due to this command
    because an inactive player was in the way. Specifically, turtler7 was thought to be a loser to Hirakoba after Hirakoba's win."""
    takenoko_bosspile = """__**Bosspile Standings**__

:crown: :small_orange_diamond: :small_orange_diamond: :small_orange_diamond: nmego
:small_orange_diamond: :small_orange_diamond: :small_orange_diamond: salaozy
:small_orange_diamond: Coxy5
Lilypam
Hirakoba
~~:small_orange_diamond: :small_orange_diamond: :small_orange_diamond: :small_orange_diamond: turtler7:timer:~~
andycupid :arrow_double_up:
Pocc :arrow_double_up:
brisdaz :thought_balloon:
"""
    bp = BossPile("takenoko", [], takenoko_bosspile)
    actual_bosspile = bp.win("Hirakoba")
    expected_bosspile = """Hirakoba defeats andycupid

:crossed_swords: andycupid :vs: Pocc

:crossed_swords: Lilypam :vs: Hirakoba


__**Bosspile Standings**__

:crown: :small_orange_diamond: :small_orange_diamond: :small_orange_diamond: nmego
:small_orange_diamond: :small_orange_diamond: :small_orange_diamond: salaozy
:small_orange_diamond: Coxy5
Lilypam
Hirakoba :arrow_double_up:
~~:small_orange_diamond: :small_orange_diamond: :small_orange_diamond: :small_orange_diamond: turtler7:timer:~~
andycupid
Pocc :arrow_double_up:
brisdaz :thought_balloon:
"""
    assert_equal(expected_bosspile, actual_bosspile)


def properly_mark_matches():
    """Problem was that on Balzi win, Balzi vs xobxela isn't marked as a match"""
    lucky_numbers_bosspile = """__**Bosspile Standings**__

:crown: xobxela
Pocc
balzi :arrow_double_up:
Lotus Blossom
:small_orange_diamond:Dragomir
stopherjones
kingneal
Lagunex  :arrow_double_up:
Boardgame_Shri  :thought_balloon:
snoozefest  :thought_balloon:
Sharzi  :thought_balloon:
Justin Jake  :thought_balloon:
Takorina
andycupid  :arrow_double_up:"""
    bp = BossPile("luckynumbers", [], lucky_numbers_bosspile)
    actual_bosspile = bp.win("Balzi")
    expected_bosspile = """balzi defeats Pocc

:crossed_swords: xobxela :vs: balzi

:hourglass: Takorina :vs: andycupid
:hourglass: kingneal :vs: Lagunex

__**Bosspile Standings**__

:crown: xobxela
balzi :arrow_double_up:
Pocc
Lotus Blossom
:small_orange_diamond: Dragomir
stopherjones
kingneal
Lagunex :arrow_double_up:
Boardgame_Shri :thought_balloon:
snoozefest :thought_balloon:
Sharzi :thought_balloon:
Justin Jake :thought_balloon:
Takorina
andycupid :arrow_double_up:
"""
    assert_equal(expected_bosspile, actual_bosspile)


def match_index_out_of_range():
    """Got a list index out of range when parsing match text."""
    yokohama_bosspile = """__**Bosspile Standings**__

:crown: Corwin007
nmego :arrow_double_up:
joepunman
Pocc :arrow_double_up:
Hirakoba
xobxela :arrow_double_up:
Faust664 :thought_balloon:
"""
    bp = BossPile("yokohama", [], yokohama_bosspile)
    actual_response = bp.win('Faust664')
    expected_response = """2 climbers found (1 required) at positions 5-6. No changes made."""
    assert_equal(expected_response, actual_response)


def dont_repeat_mistakes():
    test_multiple_parentheses()
    inactive_players_dont_prevent_generated_matchups()
    properly_mark_matches()
    match_index_out_of_range()


dont_repeat_mistakes()
