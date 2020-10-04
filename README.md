# bosspiles

A discord bot for the BGA bosspiles group: https://en.boardgamearena.com/group?id=2047909. 

## What are bosspiles?

The Bosspile is a discord ladder system designed for 2 player games.

### Rules [work in progress]

* Active players will challenge an inactive player above them to a 1v1 game set with 2 moves per day timer
* This challenge is an attempt at climbing above the defending player in the pile
* The winner will be active after the game ends and the loser will be inactive (meaning they will need to win as the challenged player before they can attempt climbing higher)
* The highest player in the ladder is the boss and will win diamonds for successfully defeating a challenge
* When the boss is defeated, that player drops one extra place for each diamond they won as the boss
* After 5 :small_orange_diamond: they are changed into a :large_orange_diamond: and when losing that boss drops ALL the way to the bottom of the pile
* But the :large_orange_diamond: s do not count on future runs as the boss
The lowest player on the pile is always active
* They can challenge the next lowest player provided that player is not already active and attempting to climb
* They must wait for that match to end and can challenge the loser immediately

### Requirements for a bosspile

Each pile needs a seperate channel for different games and those will be created when 3+ players express interest in that game.

### Contact

Have fun and feel free to private message turtler7 on BGA if you have any questions or want your favorite game to have its own pile!

## Setup

Run this on a VPS with autotools:

```bash
$ make install
$ make run
```

## Test

```bash
$ make test
```

## Usage

*Content in usage and examples is the same as the help document when you type `$$`.*

This bot needs to manage its own pinned message. If it finds a pinned bosspile,
it will repin it as its own message. A pinned bosspile must have a crown and climber.
Reset this bot's bosspile by deleting its pinned message, ensuring there is a bosspile
pinned by a person and then run `$$p`.


### Available Commands

Shorten a command to the first letter like `$$w` for `$$ win`.

**win**: Updates the bosspile with a win by player 1 over player 2 

    win <player 1> <player 2>
               
**new**: Add a player to the bottom of the bosspile 

    new <player>

**edit**: Change the line for a player to the new one. 

    edit "<new player line>"

**remove**: Remove a player from the bosspile
    
    remove <player>

**active**: Change the status of a player to active or inactive (timer icon)
    
    active <player> <True|False>

**print**: Prints the current bosspile as a new message.
    
    print


## Examples

Your discord name is `Alice` in these examples, all of which change the bosspile.

### win
You won against Bob. (You don't need to include his name because of players with ⏫):
    
    $$ win Alice

Expected Output includes result, as well as all new matches:

    Alice defeats Bob
    Frank ⚔ Georgia
    Harriett ⚔ Ian

### new
You want to add player Charlie:
    
    $$ new Charlie
    
Expected Output:
    
    Charlie has been added.

### edit
You want to edit player "Bob" to add a large blue diamond and climbing

    $$ edit "🔷Bob⏫"

Expected Output:

    Bob ➡️ 🔷Bob⏫

### remove

You want to remove player Dan:
    
    $$ remove Dan
    
Expected Output:

    Dan has been removed.

### active
    
You want to make Eddie inactive and put a timer before his name:

    $$ active Eddie false

Expected Output:

    Eddie is now inactive.

## Contributing/Bugs

Make a github issue with your bug/feature, and PR as appropriate.
