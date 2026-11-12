*This project has been created as part of the 42 curriculum by abchtaib, yoelboud.*

# Pac-Man

## Description

A Pac-Man clone written in Python with [pygame-ce]. The player moves through a procedurally generated maze, eats every dot to finish a level, and avoids four ghosts that each chase Pac-Man in their own way. The game has 10 levels, and each level is harder than the last.

**Goal of the project:** build a complete, playable game with a clean split between the game logic (engine, entities, ghost AI) and the user interface (screens and renderers), a configurable rules file, a persistent leaderboard, and a save/resume system.

**Features**

- Procedurally generated mazes, one per level, with a seed for reproducible games
- Four ghosts with different behaviors (Blinky, Pinky, Inky, Clyde), plus a frightened mode and an eaten mode
- 10 levels with growing difficulty, a level timer and a lives counter
- Main menu with Play, Resume, Highscores, Instructions and Quit
- Pause menu with Resume, Save Game and Main Menu
- Top 10 highscore table saved on disk
- Save and resume a game after closing the window
- Cheat mode (invincibility, extra life, ghost freeze, speed boost, level skip)
- Animated walls, dots and sprites, and several maze color styles
- In-game HUD (score, lives, level, time)

**Controls**

| Key | Action |
| --- | --- |
| Arrow keys or `W` `A` `S` `D` | Move Pac-Man |
| `P` or `Space` | Pause / unpause |
| `C` | Change the maze style |
| `F1` | Cheat mode on / off |
| `1` to `5` | Cheats (only while cheat mode is on) |
| Left mouse button | Click buttons |

**Cheats** (press `F1` first)

| Key | Effect |
| --- | --- |
| `1` | Invincibility on / off (Pac-Man blinks) |
| `2` | One extra life |
| `3` | Freeze / unfreeze the ghosts |
| `4` | Speed boost |
| `5` | Skip the current level |

Active cheats are listed in red in the bottom right corner of the screen.

## Instructions

### Requirements

- Python 3.10 or newer (developed with Python 3.13)
- [uv](recommended)
- Python packages: `pygame-ce` and `lark`

### Installation and execution

From the root of the repository:

```bash
uv sync            # install the dependencies
uv run pac_man.py  # start the game
```

Without `uv`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pygame-ce lark
python pac_man.py
```

Run the game **from the root of the repository**: the images are loaded with paths like `src/assets/...`.

### Playing

1. Click **Play** to start a new game. A 3 second countdown starts each level.
2. Eat all the dots to finish the level. Big dots in the corners scare the ghosts so you can eat them.
3. Touching a ghost costs one life. You lose when you have no lives left or when the level time runs out.
4. When the game ends, type your name and click **Save** to enter the highscore table.
5. Press `P` during a game to pause, and click **Save Game** if you want to continue later. Click **Resume** in the main menu to load it.

### Where files are stored

| File | Purpose | Location |
| --- | --- | --- |
| `config.json` | Game rules | Project files |
| `highscores.json` | Top 10 scores | Project files |
| `pacman_states.json` | Saved game | Linux: `~/.local/share/pacman/` (or `$XDG_DATA_HOME/pacman/`), macOS: `~/Library/Application Support/pacman/`, Windows: `%LOCALAPPDATA%\pacman\` |

## Configuration

The game rules are read from a JSON file (`config.json`). Comments are allowed in this file (`#`, `//` and `/* ... */`); they are removed before the JSON is parsed with a small [Lark] grammar.

Example with all the default values:

```json
{
  "width": 15,
  "height": 15,
  "lives": 3,
  "points_per_pacgum": 10,
  "points_per_super_pacgum": 50,
  "points_per_ghost": 200,
  "frightened_duration": 8.0,
  "ghost_speed": 3.0,
  "pacman_speed": 5.0,
  "seed": 42,
  "level_max_time": 90
}
```

| Key | Type | Default | Rule | Meaning |
| --- | --- | --- | --- | --- |
| `width` | int | 15 | >= 7 | Maze width in tiles |
| `height` | int | 15 | >= 7 | Maze height in tiles |
| `lives` | int | 3 | >= 1 | Starting lives |
| `points_per_pacgum` | int | 10 | >= 0 | Points for a normal dot |
| `points_per_super_pacgum` | int | 50 | >= 0 | Points for a big dot |
| `points_per_ghost` | int | 200 | >= 0 | Points for eating a scared ghost |
| `frightened_duration` | number | 8.0 | >= 0 | Seconds the ghosts stay scared (level 1) |
| `ghost_speed` | number | 3.0 | > 0 | Ghost speed in tiles per second (level 1) |
| `pacman_speed` | number | 5.0 | > 0 | Pac-Man speed in tiles per second |
| `seed` | int | 42 | >= 1 | Seed of the level 1 maze |
| `level_max_time` | int | 90 | >= 20 | Base level time in seconds (level 1) |

**Error handling.** If the file is missing, is not a regular `.json` file, or contains invalid JSON, the game starts with the default values and prints a warning. If a single value is missing or invalid, only that value falls back to its default, with a warning.

**Difficulty per level.** From the base values, each level N is computed like this:

| Value | Formula |
| --- | --- |
| Level time | `max(45, level_max_time - (N - 1) * 3)` seconds |
| Frightened duration | `max(2.0, frightened_duration - (N - 1) * 0.5)` seconds |
| Ghost speed | `min(4.8, ghost_speed + (N - 1) * 0.1)` |
| Maze seed | `seed` for level 1, a random seed for the other levels |

## Highscores

**How it works**

- The scores are stored in `highscores.json` as a simple JSON object: `{"NAME": score, ...}`.
- Only the **top 10** scores are kept. The table is sorted from the highest to the lowest score when it is displayed.
- When a game ends (loss or win), the player types a name and clicks **Save**. The **Highscores** button in the main menu shows the table.
- A name is valid if it is not empty, has at most 10 characters, and contains only letters, digits and spaces.
- Each name appears once. If a name already exists, the score is replaced only if the new score is higher.
- If a score is refused, the reason is shown on the game over screen and the player can type another name.

**Why this way**

- A JSON file is easy to read, easy to edit by hand, and needs no database.
- Using the name as the key guarantees one entry per player and makes the "personal best" rule simple.
- Keeping only 10 entries keeps the file tiny and the screen readable.
- All the checks are in one class (`HighscoreManager`), so the screens only show its answer and never repeat the rules.
- A missing or corrupted file never crashes the game: invalid entries are skipped and the table starts empty with a warning.
- A score is saved only when the player clicks **Save**, so quitting the game never writes a score by accident.

## Maze Generation

Each level builds a new maze with the assigned **A-Maze-ing** package. The package is not called directly by the game: it is wrapped by the `MazeAdapter` class (`maze_adapter.py`), so the rest of the code does not depend on it.

1. At startup, `Config.from_file` calls `MazeAdapter.set_maze_size((width, height))` with the size from the config file.
2. For each level, the engine asks the configuration for a `LevelConfig` (`Config.generate_level`), which contains the level number and the **seed**.
3. `MazeAdapter.generate_maze(levelconfig)` returns a grid of cells. Level 1 uses the seed from `config.json`, so it is always the same maze. The next levels use a random seed.
4. The engine fills the grid: a normal dot on every corridor cell, and a big dot in each of the four corners.
5. Pac-Man starts at the center of the maze (on the nearest corridor), and the four ghosts start in the four corners.

The grid gives the game what it needs:

- `is_wall(x, y)` to check if a move is possible
- `find_nearest_corridor(x, y)` to turn any target into a valid tile for the ghosts
- `CellType` to tell normal walls from the logo walls, which are drawn in their own color
- The consumables stored in each cell

The renderer picks the right wall sprite for each wall cell by looking at its 8 neighbors (a bit mask), so walls join smoothly.

## Implementation

**Game loop.** `PacmanApp.run` repeats this at 60 FPS: read the input (`InputHandler`), give it to the active screen, change screen if the command asks for it, update the screen with the elapsed time, draw it, and flip the display.

**Input as commands.** `InputHandler` turns pygame events into one `InputCommand` object per frame (direction, click, pause, text typed, cheat key, etc.). Screens read the command and can set flags on it (for example `play` or `show_highscores`) that the main loop turns into a screen change. Only the left mouse button counts as a click.

**Engine.** `GameEngine` is a small state machine: `RESPAWNING` (3 second countdown), `PLAYING`, `STOPPED` (paused), `GAME_OVER` and `GAME_WON`. Each tick it moves Pac-Man and the ghosts, applies the consumable effects, checks collisions, and runs the level timer.

**Movement.** Entities move continuously on a tile grid. A direction change is applied when the entity reaches the center of a tile, so turns are smooth and never cut through walls.

**Ghost AI** (`ghost_ai.py`). Each ghost has a strategy class. Paths are found with a breadth-first search (BFS).

| Ghost | Chase behavior |
| --- | --- |
| Blinky | Goes straight to Pac-Man |
| Pinky | Aims 4 tiles ahead of Pac-Man |
| Inky | Aims at a point computed from Blinky and the tile 2 steps ahead of Pac-Man |
| Clyde | Chases Pac-Man when far (more than 8 tiles), otherwise goes back to its spawn |

All ghosts run away from Pac-Man when frightened. A ghost that has been eaten goes back to its spawn (shown as eyes) before returning to normal.

**Consumables.** Dots and big dots are objects made of effects (score, frighten ghosts). A level ends when no consumable is left.

**Rendering.** `Renderer` owns the window and delegates to `RenderMaze`, `RenderConsumables`, `RenderPlayer` and `RenderGhost`. They all use sprite sheets, so there are no drawn shapes in the game itself. The tile size is computed from the maze size and the window, and the maze is placed on the left with the HUD on the right.

**Save and resume.** The engine can serialize its full state (config, level, score, timers, Pac-Man, ghosts, eaten dots, maze seed) to `pacman_states.json`. The game is saved when the player clicks **Save Game**, closes the window, or goes back to the main menu. A loaded game starts paused. The save is deleted when a game ends. Clicking **Resume** with no save shows "No game to resume".

**Cheats.** `F1` enables cheat mode, then keys `1` to `5` apply effects through the entities' effect system or the engine. The active effects are displayed on screen.

## General Software Architecture

```
pac_man.py                  PacmanApp: window, main loop, screen switching
src/
├── game_state_manager.py   GameStateManager: owns the screens, changes the active one
├── main_menu_screen.py     MainMenuScreen
├── playscreen.py           PlayScreen + PlayEngine (public view of the engine)
├── engine.py               GameEngine, EngineState, Cheat
├── entities.py             Entity, PacMan, Ghost, Direction, GhostState, Skill
├── ghost_ai.py             GhostStrategy and the four ghost strategies
├── consumables.py          PacGum, SuperPacGum and their effects
├── maze_adapter.py         MazeAdapter, CellType (wrapper of A-Maze-ing)
├── config.py               Config, LevelConfig
├── highscore.py            HighscoreManager
├── logs.py                 log(), LogType
└── ui/
    ├── screen.py           Screen (abstract base class)
    ├── inputhandler.py     InputHandler, InputCommand
    ├── renderer.py         Renderer
    ├── render_maze.py      RenderMaze
    ├── render_consumables.py  RenderConsumables
    ├── render_player.py    RenderPlayer
    ├── render_ghost.py     RenderGhost
    ├── highscore_screen.py HighscoreScreen
    └── instructions_screen.py InstructionsScreen
```

**Relationships**

```
PacmanApp
 ├── InputHandler ──► InputCommand
 ├── Renderer ──► RenderMaze, RenderConsumables, RenderPlayer, RenderGhost
 └── GameStateManager
      ├── MainMenuScreen ─┐
      ├── PlayScreen ─────┼─► Screen (abstract: handle_input, update, render)
      ├── HighscoreScreen │
      └── InstructionsScreen
           PlayScreen ──► PlayEngine (GameEngine) ──► Config / MazeAdapter
                                   │                  ├─► PacMan, Ghost (Entity) ──► GhostStrategy
                                   │                  └─► Consumables
           PlayScreen, HighscoreScreen ──► HighscoreManager
```

**Main design ideas**

- **Logic and display are separate.** The engine and entities know nothing about pygame. The screens only read the engine through public properties and call its public methods.
- **Every screen has the same three methods** (`handle_input`, `update`, `render`), so `GameStateManager` can treat them all the same way.
- **One adapter for the maze package**, so the generation library is used in a single place.
- **Rules live in one config object**, which is also saved with the game so a resumed game keeps the same rules.

For formal Mermaid UML class diagrams, state machines, and sequence diagrams, see [**UML Architecture & System Specifications**](./project_management/uml_architecture.md).

## Resources

**References**

- [pygame-ce documentation](https://pyga.me/docs/)
- [Python documentation](https://docs.python.org/3/)
- [uv documentation](https://docs.astral.sh/uv/)
- [Lark parsing library documentation](https://lark-parser.readthedocs.io/)
- [The Pac-Man Dossier, by Jamey Pittman](https://pacman.holenet.info/): how the original ghosts choose their targets
- [Breadth-first search (Wikipedia)](https://en.wikipedia.org/wiki/Breadth-first_search)
- [Python `json` module](https://docs.python.org/3/library/json.html) and [`dataclasses`](https://docs.python.org/3/library/dataclasses.html)

**Use of AI**

AI Was used to create readme file, also to understand better some concepts and parts of the project.

## Project Management

- **Team and roles:** **yoelboud** was responsible for the core game logic (simulation engine, entity state machines, BFS ghost AI, configuration parsing with comments, and persistent state serialization); **abchtaib** was responsible for the user interface and rendering (Pygame-ce display pipeline, procedural maze autotiling bitmask, sprite animations, input command handling, HUD, and interactive screens).
- **Organization:** The project applied an adapted Scrumban methodology over an 8-week delivery timeline (Sept 17 – Nov 11, 2026). Development was partitioned along strict Model-View-Controller (MVC) boundaries, communicating exclusively through typed public interfaces (`InputCommand`, `Screen`, `PlayEngine`).
- **Tools:** Git & GitHub for version control and issue tracking, `uv` for reproducible environments and dependency locking, `flake8` and strict `mypy` for quality assurance.
- **Dedicated Project Management Directory:** [`project_management/`](./project_management/)
  - [**Team Organization & Governance**](./project_management/team_organization.md): Roles, RACI matrix, communication channels, and decision-making framework.
  - [**Timeline, Gantt Chart & Kanban**](./project_management/timeline_and_gantt.md): Planned vs. actual milestones, Mermaid Gantt schedule, and Kanban board snapshots.
  - [**Actual Progress Tracking**](./project_management/progress_tracking.md): Schedule variance analysis, milestone burn-up, and Git commit anchors.
  - [**Project Analysis & Choices**](./project_management/project_analysis_and_choices.md): Technical trade-offs (MVC decoupling, BFS vs A*, 8-neighbor bitmask autotiling, Lark comment parsing, PlatformDirs).
  - [**Risk Analysis & Mitigation**](./project_management/risk_management.md): Probability-impact matrix, contingency plans, and post-mortem evaluation of materialized risks.
  - [**Acceptance Test Plan & Bug Fix Log**](./project_management/acceptance_test_plan.md): 28-point functional test suite against 42 specifications and verified defect resolution log.
  - [**Blocking Points & Conflict Resolution**](./project_management/blocking_points_and_conflicts.md): Post-mortem of technical bottlenecks (off-center tile freeze, model leaks, git merges) and mediation protocols.
  - [**UML Architecture & Design Specifications**](./project_management/uml_architecture.md): Formal Mermaid UML class diagram, component boundaries, engine/ghost state machines, and frame loop sequence diagram.
