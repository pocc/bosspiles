
from bosspiles import BossPile
from examples import example_cantstop_bosspile


def test():
    """main test"""
    bosspile = BossPile("Can't Stop", example_cantstop_bosspile)
    bosspile.win("Lotus blossum", "joepunman")
    bosspile.win("joepunman", "salaozy")
    print(bosspile.generate_bosspile())


if __name__ == '__main__':
    test()
