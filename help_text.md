Bosspile Bot: Manage your discord ladders like a wizard

This bot needs to manage its own pinned message. If it finds a pinned bosspile,
it will repin it as its own message. A pinned bosspile must have a crown and climber.
Reset this bot's bosspile by deleting its pinned message, ensuring there is a bosspile
pinned by a person and then run `$p`.

__**Available Commands**__

    Shorten a command to the first letter like `$w` for `$ win`.

    **win**: Updates the bosspile with a win by player 1 over player 2
            `win <player 1>`
    **new**: Add a player to the bottom of the bosspile
            `new <player>`
    **edit**: Change the line for a player to the new one. The old line must match the beginning of the old player line (So it can be Q if there is only one player with a name starting with Q).
            `edit "<old player line>" "<new player line>"`
    **move**: Move a player/line up/down a number of spaces. Positive goes up; negative goes down.
            `move <player> <number of spaces>`
    **remove**: Remove a player from the bosspile
            `remove <player>`
    **active**: Change the status of a player to active or inactive (timer icon). If this bot sees a "player" with `**` or `__` (bold/italic markers) in their name, it treats it as an inactive heading.
            `active <player> <True|False>`
    **print**: Prints the current bosspile as a new message. Arg can be raw or debug, but is not required.
            `print <option>`


__**Examples**__

    Your discord name is `Alice` in these examples, all of which change the bosspile.

    **win**
        You won against Bob. (You don't need to include his name because of players with ⏫):
            `$ win Alice`
        Expected Output includes result, as well as all new matches:
            `Alice defeats Bob`
            `Frank ⚔ Georgia`
            `Harriett ⚔ Ian`
    **new**
        You want to add player Charlie:
            `$ new Charlie`
        Expected Output:
            `Charlie has been added.`

    **edit**
        You want to edit player "Bob" to add a large blue diamond and climbing
            `$ edit "bob" "🔷Bob⏫"`
        Expected Output:
            `Bob ➡️ 🔷Bob⏫`

    **move**
        You want to move player "Bob" up 2 spaces
            `$ move bob 2`

    **remove**
        You want to remove player Dan:
            `$ remove Dan`
        Expected Output:
            `Dan has been removed.`

    **active**
        You want to make Eddie inactive and put a timer before his name:
            `$ active Eddie false`
        Expected Output:
            `Eddie is now inactive.`