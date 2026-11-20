# Quality Assurance & Acceptance Test Plan

*42 Network / 1337 Coding School — Pac-Man Project Management*

---

## 1. Test Strategy Overview

Quality Assurance was conducted through a combination of:
1. **Automated Static Verification**: `flake8` for PEP 8 compliance and `mypy --strict` for static type safety.
2. **Headless Domain Logic Testing**: Verifying entity math, maze adapters, and highscore mechanics without launching an active display.
3. **Structured Acceptance Testing**: Systematic validation against all functional requirements specified in the 42 subject (Chapters IV, V, VI, VII).
4. **Regression & Stress Testing**: Rigorous testing under edge cases (corrupted files, boundary dimensions, rapid key inputs, cheat combinations).

---

## 2. Acceptance Test Matrix (Features Verified)

### Category A: Configuration & Initialization

| Test ID | Feature Under Test | Test Scenario / Input | Expected Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **TC-A01** | Valid Configuration | Standard `config.json` with all default parameters. | Engine loads all values accurately; level 1 starts with seed 42. | **PASS** |
| **TC-A02** | Commented Config | Comments formatted as `#`, `//`, and `/* ... */`. | Lark grammar strips comments; JSON parses without error. | **PASS** |
| **TC-A03** | Missing Config File | `config.json` deleted or renamed. | Warning logged; game safely initializes using default values. | **PASS** |
| **TC-A04** | Invalid JSON Syntax | Broken brackets or stray characters in `config.json`. | Warning logged; game safely initializes using default values. | **PASS** |
| **TC-A05** | Out-of-Bounds Values | `width: 3`, `height: -5`, `lives: 0`. | Values are clamped to minimum safe thresholds (`width >= 7`, etc.). | **PASS** |

### Category B: Procedural Maze & Navigation

| Test ID | Feature Under Test | Test Scenario / Input | Expected Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **TC-B01** | Level 1 Determinism | Launch new game with `seed: 42`. | Maze geometry, corridor layout, and dot placements are identical across runs. | **PASS** |
| **TC-B02** | Subsequent Seeds | Advance from Level 1 to Level 2. | Level 2 generates a distinct, non-identical procedural maze. | **PASS** |
| **TC-B03** | Wall Collision Check | Move Pac-Man directly into an adjacent wall cell. | Movement is blocked cleanly; no clipping or sprite penetration occurs. | **PASS** |
| **TC-B04** | Tile Turn Buffering | Press perpendicular direction key while mid-tile. | Pac-Man continues moving and executes turn exactly at the tile center. | **PASS** |
| **TC-B05** | 42 Logo Walls | Generate maze with logo enabled. | Logo walls are rendered with distinct dedicated colors (`CellType.LOGO`). | **PASS** |

### Category C: Entities, Consumables & Ghost AI

| Test ID | Feature Under Test | Test Scenario / Input | Expected Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **TC-C01** | Normal Pacgum | Pac-Man consumes normal dot. | Score increments by $+10$; dot disappears from grid. | **PASS** |
| **TC-C02** | Super Pacgum | Pac-Man consumes corner energizer. | Score increments by $+50$; all 4 ghosts enter `FRIGHTENED` mode (blue). | **PASS** |
| **TC-C03** | Eating Frightened Ghost | Pac-Man collides with blue ghost. | Score increments by $+200$; ghost turns into eyes and flees to spawn. | **PASS** |
| **TC-C04** | Ghost AI Personalities | Observe 4 ghosts in `CHASE` mode. | Blinky attacks directly, Pinky ambushes, Inky flanks, Clyde retreats if close. | **PASS** |
| **TC-C05** | Ghost Respawn & Eyes | Eaten ghost reaches home tile. | Eyes transform back to normal ghost; ghost resumes chase. | **PASS** |
| **TC-C06** | Level Completion | Pac-Man consumes the final remaining dot. | Level advances immediately; next maze generates; 3s countdown begins. | **PASS** |

### Category D: Difficulty Scaling (Levels 1 to 10)

| Test ID | Feature Under Test | Test Scenario / Input | Expected Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **TC-D01** | Ghost Speed Scaling | Progress from Level 1 to Level 5. | Ghost speed increases dynamically according to formula: $\min(4.8, \text{speed} + 0.1 \cdot (N-1))$. | **PASS** |
| **TC-D02** | Frightened Time Scale| Eat super-pellet on Level 8. | Frightened timer is noticeably shorter ($\max(2.0, \text{dur} - 0.5 \cdot (N-1))$). | **PASS** |
| **TC-D03** | Level Timer Scale | Observe level timer on higher levels. | Level duration is computed dynamically based on total pellets and speed ratio ($\max(30.0, \dots)$ seconds). | **PASS** |
| **TC-D04** | Game Victory | Eat all dots on Level 10. | Game transitions to `GAME_WON` state; victory banner displays. | **PASS** |

### Category E: Cheats, Highscores & State Persistence

| Test ID | Feature Under Test | Test Scenario / Input | Expected Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **TC-E01** | Cheat Toggle (`F1`) | Press `F1` during gameplay. | Cheat mode toggles ON/OFF; active cheats overlay appears in red on HUD. | **PASS** |
| **TC-E02** | Cheat 1 (Invincible) | Press `1` in cheat mode, touch ghost. | Pac-Man blinks visually; life count is NOT deducted on contact. | **PASS** |
| **TC-E03** | Cheat 3 (Freeze) | Press `3` in cheat mode. | Ghosts freeze in place; Pac-Man moves freely. | **PASS** |
| **TC-E04** | Cheat 5 (Skip Level) | Press `5` in cheat mode. | Current level ends; game advances immediately to next level. | **PASS** |
| **TC-E05** | Highscore Entry | Finish game, enter name `"HERO"`, save. | Score is saved to `highscores.json`; displayed on Top 10 table. | **PASS** |
| **TC-E06** | Invalid Name Rejection| Enter empty name, or symbols like `$$$`. | System displays error explanation; prompts player to re-enter valid name. | **PASS** |
| **TC-E07** | Save Game (`P`) | Pause game, click **Save Game**, quit. | Full state serializes to XDG JSON file; Resume button active on restart. | **PASS** |
| **TC-E08** | Resume Game | Click **Resume** in Main Menu. | Game loads exact level, score, lives, eaten dots, and starts in paused state. | **PASS** |

### Category F: Logging, Storage & Packaging

| Test ID | Feature Under Test | Test Scenario / Input | Expected Result | Status |
| :---: | :--- | :--- | :--- | :--- |
| **TC-F01** | Terminal Logger Bounding | Generate rapid logs in 80x24 terminal. | Box widths capped to $\le 76$ chars, messages truncate at 48 chars, max 3 boxes, no vertical screen scrolling. | **PASS** |
| **TC-F02** | Fault-Tolerant File I/O | Simulate read-only log directory or disk full. | Logger catches `OSError` cleanly; engine and game continue without crash. | **PASS** |
| **TC-F03** | Standalone Executable | Execute `make build` and run binary from `dist/`. | Onefile executable launches independently with embedded assets and platform icons. | **PASS** |

---

## 3. Comprehensive Bug Tracker & Fix Log

The following table documents real defects discovered during development iterations, their root causes, and verified solutions:

| Bug ID | Severity | Discovered Component | Description & Symptoms | Root Cause | Fix Commit | Verified By |
| :---: | :---: | :--- | :--- | :--- | :---: | :---: |
| **BUG-01** | **Critical** | `src/entities.py` | **Off-Center Turn Freeze**: Pac-Man froze awkwardly off-center (e.g. at $x = 3.6$ instead of reaching center $x = 4.0$). | Direction switch evaluated before confirming alignment, leaving entity trapped between grid lines. | `df93f9f` | `abchtaib` & `yoelboud` |
| **BUG-02** | **Major** | `src/engine.py` | **Lives Reset on Advance**: When advancing from Level 1 to Level 2, Pac-Man lives were reset back to config default (3). | `_load_level()` reconstructed `PacMan` unconditionally instead of preserving active instance state. | `3a436f9` | `yoelboud` |
| **BUG-03** | **Major** | `src/ghost_ai.py` | **Ghost Hesitation & FPS Drops**: In complex maze topologies, ghosts occasionally stuttered or dropped FPS. | Recursive BFS without visited set deduplication; targets inside walls triggered exhaustive search. | `6590de3` | `yoelboud` |
| **BUG-04** | **Major** | `src/maze_adapter.py` | **Static Class Variable Mutation**: Calling `generate_maze()` without `Config.from_file()` crashed with `TypeError`. | Dimensions were stored as mutable class variables on `MazeAdapter` instead of passing per-level arguments. | `3a436f9` | `yoelboud` |
| **BUG-05** | **Medium** | `src/ui/screen.py` | **Shared Screen Mutation**: Setting `door_closed = True` in `MainMenuScreen` corrupted door state in `PlayScreen`. | State was defined as mutable class-level attributes on abstract `Screen` class. | `94fd083` | `abchtaib` |
| **BUG-06** | **Medium** | `src/engine.py` | **Pause Countdown Skip**: Pausing during the 3-second respawn countdown and resuming immediately launched game. | `resume()` hardcoded `_state = EngineState.PLAYING` instead of restoring `_previous_state`. | `e0ff397` | `abchtaib` |
| **BUG-07** | **Medium** | `src/entities.py` | **Respawn Effect Leak**: Ghosts killed while frightened retained speed debuffs after respawning at home tile. | Status effect collection was not cleared when repositioning entity to spawn. | `235336d` | `yoelboud` |
| **BUG-08** | **Low** | `src/data_dir.py` | **Filesystem Permission Warning**: Hardcoded relative save paths failed when executing from external directories. | State path assumed current working directory had write access. Refactored to `platformdirs`. | `3b3d8f8` | `yoelboud` |
| **BUG-09** | **Low** | `src/config.py` | **Windows Encoding Mismatch**: Non-ASCII characters in config path or system locale broke parser on Windows. | `open()` was invoked without explicit `encoding="utf-8"`. | `1c86914` | `abchtaib` |
| **BUG-10** | **Medium** | `src/logger.py` | **Live Terminal Overflow**: Rapid game logging caused screen scrolling, desynchronizing Rich live cursor and stamping duplicate frames. | Unbounded table history and horizontal text wrap. Fixed with `BOX_WIDTH = 76`, `MAX_TABLES = 3`, and `vertical_overflow="crop"`. | `34da74f` | `yoelboud` |
| **BUG-11** | **Medium** | `src/logger.py` | **Unprotected Concurrency in File I/O**: File write/flush executed outside thread lock, risking race conditions and crash on OS write error. | Missing synchronization and exception guards. Wrapped writes in `self._lock` and `try...except OSError`. | `34da74f` | `yoelboud` |
| **BUG-12** | **Major** | `PacMan.spec` | **Asset Directory Missing in Frozen Binary**: Standalone executable failed on start with missing sprite assets. | Bundled datas path not copied into runtime temporary directory. Added `('assets', 'assets')` to Analysis datas. | `51fc7d9` | `yoelboud` & `abchtaib` |
