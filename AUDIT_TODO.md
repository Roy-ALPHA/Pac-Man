# Pac-Man Codebase Audit & Architectural Roadmap

> **Audit Overview**: Comprehensive analysis of architecture, domain logic, design patterns, and 42 subject compliance across the codebase.
> **Note**: Items are presented as an actionable diagnostic to-do list with guiding questions and verification steps (no direct copy-paste solutions).

---

## 1. System Architecture & High-Level Design

### [ ] Task 1.1: Fix Package Structure & Root Import Boundaries
- **Component**: `src/app_pac-man.py`, `src/ui/inputhandler.py`, `src/main_menu_screen.py`
- **Symptom**:
  - Running entry points from the project root fails with `ModuleNotFoundError: No module named 'entities'` or `No module named 'ui'`.
  - File naming: `src/app_pac-man.py` contains a hyphen `-`, preventing standard Python imports (`import src.app_pac_man`).
- **Architectural Smell**: Modules inside subpackages (`src/ui/`) use root-level un-namespaced imports assuming the process runs from inside `src/`.
- **Guiding Questions for Your Refactor**:
  1. How should relative imports (`from ..entities import Direction`) or package-level absolute imports (`from src.entities import Direction`) be standardized across all files in `src/`?
  2. Why does PEP 8 advise strictly against hyphens in Python module filenames? What standard snake_case filename should replace `app_pac-man.py`?

---

### [ ] Task 1.2: Decouple `Config` from `MazeAdapter` (Eliminate Static State Mutation)
- **Component**: [`src/config.py`](file:///home/itachi/Pac-Man/src/config.py#L37-L39) and [`src/maze_adapter.py`](file:///home/itachi/Pac-Man/src/maze_adapter.py#L62-L73)
- **Symptom**:
  - `Config` imports `MazeAdapter` and mutates class-level variables (`MazeAdapter._width`, `MazeAdapter._height`) inside `Config.from_file()`.
  - If `MazeAdapter.generate_maze()` is called in isolated unit tests without calling `Config.from_file()` first, `_width` is `None`, raising a `TypeError`.
- **Architectural Smell**: Inverted dependency. Configuration data structures should be pure data holders (or dataclasses) and should never mutate behavioral engine adapters.
- **Guiding Questions for Your Refactor**:
  1. How can `MazeAdapter` receive dimensions directly when generating a maze (e.g., from `LevelConfig`) instead of reading mutable global class variables?
  2. If the subject allows per-level dimensions in the future (`levels` array), how will static class variables break per-level sizing?

---

### [ ] Task 1.3: Bridge Engine to UI via Clean Encapsulation (`get_renderables`)
- **Component**: [`src/engine.py`](file:///home/itachi/Pac-Man/src/engine.py), [`notes.txt`](file:///home/itachi/Pac-Man/notes.txt#L2-L22)
- **Symptom**:
  - Both `terminal_test.py` and `pygame_test.py` currently inspect private fields (`engine._grid`, `engine._ghosts`, `engine._pacman`).
  - As noted in your `notes.txt`, the UI should not do `isinstance(obj, PacMan)` or check `ghost.state == ...`.
- **Architectural Smell**: Leaky abstraction / high coupling between Model and View.
- **Guiding Questions for Your Refactor**:
  1. What lightweight data container (e.g., `Renderable(x, y, asset_id, frame, color)`) can `GameEngine.get_renderables()` return?
  2. How can the renderer simply iterate through a list of generic renderables without knowing any game physics or internal entity state?

---

### [ ] Task 1.4: Eliminate Module-Level File I/O Side Effects
- **Component**: [`src/engine.py`](file:///home/itachi/Pac-Man/src/engine.py#L6) (and previously `ghost_ai.py`)
- **Symptom**: `f = open("logs.txt", "w")` sits at the top level of `engine.py`.
- **Architectural Smell**: Importing a module must never mutate the host filesystem, truncate files, or leave open file handles.
- **Guiding Questions for Your Refactor**:
  1. What happens if the game is run in a read-only directory or packaged as an executable bundle?
  2. How should Python's standard `logging` module with a null handler or file handler be configured properly?

---

## 2. Game Engine & State Machine Logic

### [ ] Task 2.1: Remove Hardcoded Cheat Invincibility on Level Load
- **Component**: [`src/engine.py`](file:///home/itachi/Pac-Man/src/engine.py#L147)
- **Symptom**: `_load_level()` explicitly calls `self.activate_cheat(Cheat.INVINCIBILITY)`.
- **Problem**: Pac-Man is permanently immune to ghost attacks in regular gameplay!
- **Investigation To-Do**:
  - Verify where cheats should be activated (only through input handlers or debug test harnesses).
  - Ensure regular engine initialization starts with standard mortality.

---

### [ ] Task 2.2: Preserve Pac-Man Lives Across Level Transitions
- **Component**: [`src/engine.py`](file:///home/itachi/Pac-Man/src/engine.py#L89-L95)
- **Symptom**: When advancing from Level 1 to Level 2, `PacMan` is reconstructed using `self._config.lives`.
- **Problem**: Any lives lost in Level 1 are magically restored to full when advancing, and any bonus lives earned via cheats are wiped out.
- **Guiding Questions for Your Refactor**:
  1. How can `_load_level()` check if an active `self._pacman` already exists, and preserve its current life count?
  2. When is the only moment lives should truly reset to default?

---

### [ ] Task 2.3: Fix State Machine Amnesia During Pause/Resume
- **Component**: [`src/engine.py`](file:///home/itachi/Pac-Man/src/engine.py#L55-L59)
- **Symptom**:
  ```python
  def stop(self): self._state = EngineState.STOPPED
  def resume(self): self._state = EngineState.PLAYING
  ```
- **Problem**: If the user pauses while the game is in `EngineState.RESPAWNING` (during the 3-second ready countdown), resuming immediately skips the remaining countdown and forces `PLAYING`.
- **Guiding Questions for Your Refactor**:
  1. How can the engine remember its previous active state (`_previous_state`) before transitioning to `STOPPED`?
  2. When `resume()` is triggered, how should it restore the stored state rather than hardcoding `PLAYING`?

---

### [ ] Task 2.4: Initialize Object Attributes in `__init__` Rather Than Dynamically
- **Component**: [`src/engine.py`](file:///home/itachi/Pac-Man/src/engine.py#L25-L31)
- **Symptom**: `_pacman`, `_ghosts`, `_grid`, `_level_time`, `_skip_level`, `_is_game_over` do not exist until `_load_level()` runs inside the first `tick()`.
- **Problem**: Calling `engine.is_game_over` or `engine.activate_cheat()` right after instantiation raises `AttributeError`.
- **Investigation To-Do**:
  - Define all instance attributes in `__init__` with explicit default values (`None`, `0`, `False`).
  - Consider triggering the initial level load cleanly during initialization.

---

### [ ] Task 2.5: Remove Magic Number 10 for Game Completion
- **Component**: [`src/engine.py`](file:///home/itachi/Pac-Man/src/engine.py#L187-L189)
- **Symptom**: `is_game_won` hardcodes `self._cur_level == 10`.
- **Guiding Questions for Your Refactor**:
  1. Where should the total level count or win condition be configured (e.g. `Config.max_levels`)?
  2. How can game victory be determined dynamically based on configuration or level arrays?

---

### [ ] Task 2.6: Review Unused `_calc_spawn` & Validate Center Spawns
- **Component**: [`src/engine.py`](file:///home/itachi/Pac-Man/src/engine.py#L34-L46, L87)
- **Symptom**: `_calc_spawn` is completely dead code; Pac-Man spawns at raw `(width // 2, height // 2)`.
- **Problem**: In arbitrary or even-sized generated mazes, `(width // 2, height // 2)` can land on an internal wall!
- **Investigation To-Do**:
  - Test what happens when the center coordinate is a wall.
  - Wire `_calc_spawn` (or a similar safe corridor resolver) to validate and adjust spawn tiles for Pac-Man and ghosts.

---

## 3. Entity States & Ghost AI Logic

### [ ] Task 3.1: Fix State Alternation/Jitter in `Ghost.update()`
- **Component**: [`src/entities.py`](file:///home/itachi/Pac-Man/src/entities.py#L219-L222)
- **Symptom**:
  ```python
  case GhostState.WANDER if dist <= 2000:
      self.switch_state(GhostState.CHASE)
  case GhostState.CHASE if dist > 10:
      self.switch_state(GhostState.WANDER)
  ```
- **Problem**:
  - If `dist > 10`, it is *also* `<= 2000`.
  - Every single frame, the ghost oscillates between `CHASE` and `WANDER`, alternating between a BFS chase step and a random turn.
- **Guiding Questions for Your Refactor**:
  1. Why was `dist <= 2000` written? Did someone mean `dist <= 10`?
  2. How should mode switching (Scatter/Wander vs Chase) be structured so states do not conflict on the exact same distance threshold?

---

### [ ] Task 3.2: Correct Ghost Initial State on Spawn
- **Component**: [`src/entities.py`](file:///home/itachi/Pac-Man/src/entities.py#L176)
- **Symptom**: Ghosts initialize with `self._state = GhostState.DIED`.
- **Problem**: Ghosts start life considered "dead" and immediately run return-to-base logic until matching their spawn tile.
- **Investigation To-Do**:
  - Initialize ghosts in their proper default state (`GhostState.WANDER` or an initial pen state).

---

### [ ] Task 3.3: Complete Ghost Respawn Reset Logic
- **Component**: [`src/entities.py`](file:///home/itachi/Pac-Man/src/entities.py#L74-L78, L173)
- **Symptom**: `Ghost` inherits `respawn()` from `Entity`, which only resets `_x, _y` and directions.
- **Problem**: If a ghost was `FRIGHTENED` or `DIED` when Pac-Man dies, upon respawn it remains in that state with the same frightened timer!
- **Guiding Questions for Your Refactor**:
  1. How should `Ghost.respawn()` override the base method to reset `_state` back to default and clear `_frightened_time`?

---

### [ ] Task 3.4: Decouple Pathfinding Frequency from Framerate
- **Component**: [`src/entities.py`](file:///home/itachi/Pac-Man/src/entities.py#L229-L230)
- **Symptom**: `self._request_direction()` is executed every tick (60 times/sec) for all 4 ghosts.
- **Problem**: Full BFS graph searches running every frame creates unnecessary CPU load.
- **Guiding Questions for Your Refactor**:
  1. Can a ghost change direction in the middle of a corridor, or only when reaching an intersection/tile center?
  2. Notice the commented-out `# if self.in_center():`. Why was that there, and how can tile-boundary decision making optimize AI evaluation?

---

### [ ] Task 3.5: Fix Ghost Targeting When Pac-Man is Stationary
- **Component**: [`src/ghost_ai.py`](file:///home/itachi/Pac-Man/src/ghost_ai.py#L142, L161, L187)
- **Symptom**: `case GhostState.CHASE if pacman.cur_direction is not Direction.NONE:`
- **Problem**: Whenever the player pauses or stops moving, all ghosts stop chasing and wander randomly.
- **Guiding Questions for Your Refactor**:
  1. Blinky targets Pac-Man's exact tile. Why should Pac-Man's movement direction matter to Blinky?
  2. If Pinky targets 4 tiles ahead and Pac-Man's direction is `NONE`, what should the target naturally default to?

---

### [ ] Task 3.6: Implement Classic Clyde Retreat vs Random Wander
- **Component**: [`src/ghost_ai.py`](file:///home/itachi/Pac-Man/src/ghost_ai.py#L213-L218)
- **Symptom**: When `dist <= 8`, Clyde calls `_wander()` (random moves).
- **Guiding Questions for Your Refactor**:
  1. In standard Pac-Man logic, where does Clyde retreat when he gets too close to Pac-Man? (Hint: check his spawn corner coordinate).
  2. How does heading to his assigned corner create the famous "cowardly" behavior?

---

### [ ] Task 3.7: Optimize `closer_corridor` with Boundaries and $O(1)$ Queue
- **Component**: [`src/ghost_ai.py`](file:///home/itachi/Pac-Man/src/ghost_ai.py#L12-L40)
- **Symptom**:
  - `closer_corridor` does not check `0 <= n_x < maze.width`.
  - BFS uses `queue.pop(0)` ($O(N)$ operations).
- **Guiding Questions for Your Refactor**:
  1. If `maze.is_wall` returns `True` for all out-of-bounds coordinates, what prevents BFS from expanding into negative coordinates infinitely?
  2. How does `collections.deque.popleft()` improve algorithmic complexity?

---

## 4. Consumables & Maze Adapter

### [ ] Task 4.1: Eliminate Global Class State in `Consumable._counter`
- **Component**: [`src/consumables.py`](file:///home/itachi/Pac-Man/src/consumables.py#L29-L48)
- **Symptom**: `_counter` is a class-level variable mutated by consumable instances.
- **Architectural Smell**: If multiple games run or unit tests run concurrently, class variables leak state across test cases.
- **Guiding Questions for Your Refactor**:
  1. Can the maze grid or engine track the count of remaining pellets directly (e.g., counting consumable cells or maintaining a level-scoped tally)?
  2. Why is instance or container ownership cleaner than class-attribute counters?

---

### [ ] Task 4.2: Fix Entry Point Call in `pac_man.py`
- **Component**: [`pac_man.py`](file:///home/itachi/Pac-Man/pac_man.py#L107)
- **Symptom**: `pac_man.py` calls `MazeAdapter().generate_level_maze()`, which crashes immediately with `AttributeError`.
- **Investigation To-Do**:
  - Check the actual method name on `MazeAdapter` (`generate_maze`).
  - Align `pac_man.py` with the adapter's public API.

---

### [ ] Task 4.3: Fix Bare `warn` Statements in `config.py`
- **Component**: [`src/config.py`](file:///home/itachi/Pac-Man/src/config.py#L183, L185, L192, L194, L201, L203)
- **Symptom**: Lines contain the bare word `warn` without parentheses or arguments.
- **Problem**: These are no-op statements that fail to issue any warning when values are missing or invalid.
- **Investigation To-Do**:
  - Replace bare `warn` with proper calls to `warn("Message", category=PacmanConfigWarning, stacklevel=2)`.

---

### [ ] Task 4.4: Fix Type Annotation Mismatch in `Config`
- **Component**: [`src/config.py`](file:///home/itachi/Pac-Man/src/config.py#L34)
- **Symptom**: `highscore_filename: str = Path("highscores.json")`
- **Problem**: The type annotation specifies `str`, but the default value is a `Path` object.
- **Investigation To-Do**:
  - Change annotation to `Path` or `str | Path`, or keep it consistent with its actual type.

---

## 5. UI, Menus & Screens Architecture

### [ ] Task 5.1: Fix Broken Image Paths in `MainMenuScreen`
- **Component**: [`src/main_menu_screen.py`](file:///home/itachi/Pac-Man/src/main_menu_screen.py#L56)
- **Symptom**: `pygame.image.load(f"assets/{name}")` assumes `assets/` is at the working root.
- **Problem**: The assets live in `src/assets/`. If executed from the repository root, image loading raises `FileNotFoundError`.
- **Guiding Questions for Your Refactor**:
  1. How can `Path(__file__).parent / "assets" / name` resolve assets relative to the file location reliably regardless of CWD?

---

### [ ] Task 5.2: Eliminate Mutable Class Variables on `Screen`
- **Component**: [`src/ui/screen.py`](file:///home/itachi/Pac-Man/src/ui/screen.py#L8-L11)
- **Symptom**: `door_w`, `screen_w`, `screen_h`, `door_closed` are stored directly on the `Screen` class.
- **Problem**: Modifying `Screen.door_closed = True` in `MainMenuScreen` mutates state across all screens.
- **Guiding Questions for Your Refactor**:
  1. How should screen dimensions and animation state be managed on screen instances rather than the abstract class?

---

### [ ] Task 5.3: Implement Missing Renderer & PlayScreen Connections
- **Component**: [`src/ui/renderer.py`](file:///home/itachi/Pac-Man/src/ui/renderer.py#L15-L26), [`src/playscreen.py`](file:///home/itachi/Pac-Man/src/playscreen.py#L1-L27)
- **Symptom**:
  - `render_maze`, `render_entities`, `render_hub` (typo for `hud`) in `renderer.py` are empty `pass` stubs.
  - `PlayScreen` only animates doors and has no connection to `GameEngine`.
- **Investigation To-Do**:
  - Connect `PlayScreen` to `GameEngine`.
  - Implement the actual Pygame rendering calls in `Renderer` (using the pattern demonstrated in `pygame_test.py`).

---

### [ ] Task 5.4: Complete UI Flow (Highscores & Instructions Screens)
- **Component**: `src/main_menu_screen.py` buttons `high` and `instrcts`.
- **Symptom**: The main menu contains buttons for Highscores and Instructions, but the `GameStateManager` has no corresponding screens.
- **Investigation To-Do**:
  - Create `HighscoreScreen` (rendering the top 10 scores from `HighscoreManager`).
  - Create `InstructionsScreen` (displaying controls and game objectives).

---

## 6. Project Deliverables & 42 Subject Compliance

### [ ] Task 6.1: Create Project `Makefile`
- **Requirement**: Subject Section III.2 & Architecture Section 2
- **Required Targets**:
  - `install`: Install dependencies using `uv` or `pip`.
  - `run`: Launch the main game (`python pac_man.py` or executable).
  - `clean`: Remove `.pytest_cache`, `__pycache__`, build artifacts, and temporary logs.
  - `lint`: Run `flake8 .` and `mypy . --warn-return-any --warn-unused-ignores`.

---

### [ ] Task 6.2: Write Root `README.md` Following Chapter IX Format
- **Requirement**: Subject Chapter IX
- **Symptom**: `README.md` is currently empty (0 bytes).
- **Mandatory Elements**:
  - *Italicized first line* containing the student logins.
  - Project Overview & Description.
  - Installation & Usage Instructions.
  - Project Management section (task split between the 2 members, timeline/milestones).

---

### [ ] Task 6.3: Codebase Typing & Documentation Sweep
- **Requirement**: Subject Section III.1 (`flake8` and strict `mypy`)
- **Inspection Checklist**:
  - [ ] Add PEP 257 docstrings to all classes and public functions across `src/`.
  - [ ] Add strict type annotations (parameters, return types) across all engine and entity methods.
  - [ ] Remove unused debug files (`logs.txt`) and scratch files from production.
