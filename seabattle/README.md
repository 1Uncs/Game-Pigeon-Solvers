# Sea Battle  
<img src="/images/Sea%20Battle/sampleSeaBattleBoard.png" alt = "sample board" width="30%" align = "right">  

### The Basics  
Sea Battle is essentially "Battleship" with a few rule changes. Each 
player has ships varying from lengths 1 to 4, and they can be placed on 
the board vertically or horizontally. Ships cannot be within 1 
tile of one another. Each player picks a tile to attack. If they miss, 
their turn is over, but if they hit a ship, they keep going until they 
miss. The game is over once one player destroys all the other 
player's ships.  
### How to use
First, download this project. You can invoke the tool by running  
```
> python3 ai_runner.py --game=seabattle
```
You will be presented with the intro screen with some instructions:  

<img src="/images/Sea%20Battle/starting_prompts.png" alt = "starting instructions" width="65%"><br/>  
   
You will be asked which dimension you want to make the board. Sea 
Battle has 8x8, 9x9, and 10x10 modes available. Each mode has a 
different set of ships, as seen below:  

<img src="/images/Sea%20Battle/starting_8board.png" alt = "starting 8x8 board" width="34%" align = "left">
<img src="/images/Sea%20Battle/starting_9board.png" alt = "starting 9x9 board" width="30%" align = "left">
<img src="/images/Sea%20Battle/starting_10board.png" alt = "starting 10x10 board" width="32%"><br/>  

| Board | Fleet (ship length × count) | Total ships | Total cells |
|---|---|---|---|
| 8×8 (Classic) | 5×1, 4×1, 3×2, 2×2 (Battleship, Cruiser, 2 Destroyers, 2 Patrol Boats) | 6 | 19 |
| 9×9 | 3×8 (8 Destroyers) | 8 | 24 |
| 10×10 (Large) | 5×1, 4×1, 3×2, 2×2, 1×4 (Carrier, Cruiser, 2 Destroyers, 2 Patrol Boats, 4 Submarines) | 10 | 23 |

Before each turn, the best moves will be shown on the board in blue. 
To see the scores that the A.I. has calculated for each location on 
the board, you can type `d` to show the space densities table. The 
number corresponds to the relative probability that a ship occupies 
that cell, factoring in the number of ways ships could still be 
placed, how many future configurations a shot there would eliminate, 
and (when the smallest ship is size ≥ 2) a checkerboard / parity 
filter that ignores cells of the wrong parity. While only the optimal 
move(s) will be shown on the board display, the densities table uses 
a color gradient so that you can easily see the good locations on the 
board if you do not wish to play in one of the optimal spaces. At the 
beginning of a 10x10 game, the game board and density table will look 
like this:  

<img src="/images/Sea%20Battle/starting_bestmoves.png" alt = "starting 10x10 board best moves" width="40%" align = "left">
<img src="/images/Sea%20Battle/starting_densities.png" alt = "starting 10x10 space densities" width="45%"><br/>    
   
As the game progresses, ships will be destroyed and removed from the 
ship counter. This will also affect how the densities are computed. 
A 10x10 match in mid-game is shown below, as well as the corresponding 
space densities table. The white `-` represent open spaces (available 
moves), the red `^` represent misses, the yellow `H` represent hits, 
and the green `D` represent destroyed ships.  

<img src="/images/Sea%20Battle/midgame_board.png" alt = "mid-game 10x10 board" width="40%" align = "left">
<img src="/images/Sea%20Battle/midgame_densities.png" alt = "mid-game space densitites" width="45%"><br/>    

After the player selects a move, they will be asked whether the move 
resulted in a miss, hit, or sink. It will then update the board and 
space densities accordingly. If the player chooses a space that is 
not in the optimal move set, the player will be asked to confirm that 
they meant to choose that location. This is to prevent accidental 
incorrect input.  

If at any point you would like to save the game to come back later, 
you can type `s` at a move selection prompt.

### 🧠 How the AI works

The strategy module (`seabattle/sea_battle_strategy.py`) is split into
two modes:

**Hunt mode (no hits on the board).** For each ship length, the AI
enumerates every legal placement that does not overlap a known miss
and is not adjacent to a known hit (the Game Pigeon no-touch rule).
For each cell, it counts the number of valid placements covering that
cell, weighted by the number of remaining ships of that length, to
produce a *placement probability* grid. It then builds an *information
gain* grid by summing the placement probabilities of the cell's
8 neighbors — the value of a miss here is high if it would eliminate
many possibilities elsewhere. The two are combined (0.7 placement +
0.3 info gain) and, when the smallest alive ship is size ≥ 2, the
result is masked by a parity filter that zeros out cells of the
mathematically impossible parity and slightly boosts the valid one.

**Target mode (≥ 1 hit on the board).** Connected hit segments are
found. For each segment, the AI computes candidate extensions (the
cardinal neighbors at the segment's endpoints, or all four
cardinal neighbors of a singleton hit). Each candidate is scored by
the number of remaining ship sizes that would fit an extended ship
through it, with 1.0 weight for completing a ship in one more hit
and 0.5 for extending. The combined score is the union of hunt and
target grids (target dominates when both are present).

### ✨ New in Version 2.0
* New hunt/target algorithm based on full fleet-placement enumeration
  and information gain, replacing the sliding-window density
  heuristic. Cells that cannot legally hold any remaining ship are
  scored at zero.
* Proper parity filter that zeros impossible cells when min ship size ≥ 2.
* Target mode now considers all remaining ship sizes (not just the
  largest) when scoring segment extensions.
* Code split into `sea_battle_strategy.py` (pure logic, fully unit
  tested) and `sea_battle_client.py` (terminal I/O and save/load).
* `__pycache__` no longer mixes old and new code; module import paths
  are unchanged for the `ai_runner.py` entry point.

#### Older Changelog
* v1.3 — Save state support (`s` at the move prompt).
* v1.2 — Space densities table replaces the board, displayed via `d`;
  board redisplay via `b`.
* v1.1 — Single-board in-place rendering (toggle with `-e`).
