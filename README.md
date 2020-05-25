# bosspiles

A discord bot for the BGA bosspiles group: https://en.boardgamearena.com/group?id=2047909. 

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

**test**: Run all of the tests
        `test`


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