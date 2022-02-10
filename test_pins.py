from bosspiles_discord import is_valid_bosspile, generate_status_checks

def assert_equal(left, right):
    if left != right:
        print(f"Expecting `{left}` but got `{right}`", flush=True)
    else:
        print("Test passed!", flush=True)

def check_pin():
    pin = """__**Bosspile Standings**__

:crown: Dragomir
Pocc
xobxela :arrow_double_up:
dockoala
turtler7 :arrow_double_up:
"""
    assert_equal(True, is_valid_bosspile(pin))


def verify_status_checks():
    channel_name = "splendor-bosspile"
    players = ["seyfert", "turtler7", "balzi", "joepunman", "pocc", "lagunex", "cheery dog", "mrawesome1212", "sesquiup", "jcase16", "takorina"]
    bosspile_text = """__**Bosspile Standings**__

:crown: :small_orange_diamond: :small_orange_diamond: Seyfert
turtler7
Balzi :arrow_double_up:
joepunman
Pocc
Lagunex (:star:) :arrow_double_up:
Cheery Dog
MrAwesome1212
sesquiup (:star:) :arrow_double_up:
jcase16 :thought_balloon:
Takorina :thought_balloon:
~~ligtreb:timer:~~"""
    statuses = generate_status_checks(channel_name, players, bosspile_text)
    expected_statuses = ['!status splendor "MrAwesome1212" "sesquiup"', '!status splendor "Pocc" "Lagunex"', '!status splendor "turtler7" "Balzi"']
    assert_equal(expected_statuses, statuses)

check_pin()
verify_status_checks()
