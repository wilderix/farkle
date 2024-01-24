
rules = """
## Rules
    
Farkle is a press-your-luck dice rolling game. Each player will roll 6 dice, initially. Each time they roll, they must keep some scoring dice set aside to get points on their turn. If they do not have any dice that qualify as scoring, they 'Farkle' and forfeit their turn and any score they have accumulated on their turn. At any point, the player may choose to bank their turn score and pass play to the next player.

On each player's turn, they are allowed to reroll any dice they did not set aside to try for more points, up to 3 rolls total.

## Scoring

Scoring is based on sets (or individual dice, in the case of 1's and 5's) as such:

{scoring_text}

In order to start accumulating a score, you must earn at least {scoreboard_starting_threshold} points in a single turn. Until you reach this threshold for the first time the first time, play will simply pass to the next player, and you will remain at 0 points on the scoreboard.

**Note:** You may go to the "Scoring" page in the menu on the sidebar to change the scoring rules above, but doing so will reset the game.

## Hot Dice

Hot Dice is when all 6 dice have been set aside as scoring. You may then roll all 6 dice again as if taking a new turn while still maintaining and adding to the score you have accumulated on your turn so far. However, rolling a Farkle will wipe out the entire score for the turn.

## Farkle Penalty

For every 3 farkles you get, you will lose {three_farkle_penalty} points. However, you can never go below 0 points.
"""