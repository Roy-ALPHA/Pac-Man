# Team Organization & Governance

*42 Network / 1337 Coding School — Pac-Man Project Management*

---

## 1. Team Structure & Role Division

To maximize velocity and eliminate merge bottlenecks, responsibilities were partitioned strictly along architectural boundaries following the **Model-View-Controller (MVC)** paradigm.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CO-OWNERS & ARCHITECTS                          │
│               Abdellah Chtaibi (abchtaib) & Younss Boudali (yoelboud)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
┌─────────────────────────────────┐   ┌──────────────────────────────────┐
│   USER INTERFACE & RENDERING    │   │      GAME LOGIC & ENGINE         │
│  Abdellah Chtaibi (abchtaib)    │   │     Younss Boudali (yoelboud)    │
├─────────────────────────────────┤   ├──────────────────────────────────┤
│ • Pygame-ce Renderer Pipeline   │   │ • Core Engine Loop & Physics     │
│ • Maze Autotiling (Bitmask)     │   │ • Entity State Machines          │
│ • Sprite Sheet Animation        │   │ • Ghost AI (BFS & Personalities) │
│ • Screen State Management       │   │ • Consumables & Effect System    │
│ • Menus (Main, Pause, Win/Loss) │   │ • Maze Adapter (A-Maze-ing Wheel)│
│ • Input Handler (Command Queue) │   │ • Config Parser (Lark Grammar)   │
│ • Heads-Up Display (HUD) & Cheat│   │ • Save/Resume State Serialization│
│ • Highscores & Instructions UI  │   │ • Highscore Manager & File I/O   │
│ • Visual Asset Integration      │   │ • Animated Terminal Logger (Rich)│
│                                 │   │ • Packaging (PyInstaller / Spec) │
└─────────────────────────────────┘   └──────────────────────────────────┘
```

### Detailed Contributor Profiles

#### Abdellah Chtaibi (`abchtaib`) — Rendering & Frontend Architect
- **Domain**: Visual presentation, user interaction, screen lifecycle, and graphical asset integration.
- **Specific Modules**:
  - `src/ui/renderer.py`: Master rendering coordinator.
  - `src/ui/render_maze.py`: Procedural tile selection based on 8-neighbor bitmasking for contiguous walls.
  - `src/ui/render_player.py`: Pac-Man direction-oriented sprite rendering and death animations.
  - `src/ui/render_ghost.py`: Multi-state ghost rendering (Chasing, Frightened blue flashing, Eaten eyes).
  - `src/ui/render_consumables.py`: Pulsing super-pellets and standard pac-gums.
  - `src/ui/inputhandler.py`: Translating keyboard/mouse events into immutable `InputCommand` objects.
  - `src/ui/screen.py` & UI implementations (`main_menu_screen.py`, `playscreen.py`, `highscore_screen.py`, `instructions_screen.py`).
  - Visual asset slicing, scaling, hover states, and font typography.

#### Younss Boudali (`yoelboud`) — Game Logic & Systems Architect
- **Domain**: Simulation mathematics, physics, autonomous agent AI, data parsing, logging, and packaging.
- **Specific Modules**:
  - `src/engine.py`: Fixed-timestep game loop, collision detection, level advancement, timers, cheat execution.
  - `src/entities.py`: `PacMan` and `Ghost` entity classes, grid positioning, tile centering, movement vectors.
  - `src/ghost_ai.py`: Targeted pathfinding for Blinky, Pinky, Inky, and Clyde; BFS shortest-path corridor solver.
  - `src/maze_adapter.py`: Adapter layer isolating the external `A-Maze-ing` generator wheel; corridor identification and cell categorization.
  - `src/consumables.py`: Polymorphic pellet objects and temporary status effect application.
  - `src/config.py`: Dynamic JSON configuration loader with Lark comment stripping (`#`, `//`, `/* */`) and level math.
  - `src/highscore.py`: Top 10 leaderboard validation and JSON persistence.
  - `src/data_dir.py`: Cross-platform XDG-compliant storage management (`DATA_DIR`, `LOGS_DIR`).
  - `src/logger.py`: Asynchronous animated terminal logger with Rich live spinners, overflow cropping, and fault-tolerant file I/O.
  - Packaging & Build: `PacMan.spec`, multi-platform standalone PyInstaller build pipeline (Linux onefile, Windows `.exe`, macOS `.app`), and `Makefile` build targets.

---

## 2. RACI Matrix

The RACI model defines task accountability across the project lifecycle:
- **R (Responsible)**: Does the actual work to complete the deliverable.
- **A (Accountable)**: Approves and bears ultimate ownership of the module.
- **C (Consulted)**: Provides two-way input and feedback on design/interfaces.
- **I (Informed)**: Kept updated on progress and changes.

| Project Component / Activity | `abchtaib` (UI/Render) | `yoelboud` (Logic/Engine) |
| :--- | :---: | :---: |
| **System Architecture Definition** | A / R | A / R |
| **Interface Contracts (`InputCommand`, `PlayEngine`, `Screen`)** | R / C | A / R |
| **Config Parser & JSON Rules (`config.py`)** | I | A / R |
| **Maze Adapter & Wheel Integration (`maze_adapter.py`)** | C | A / R |
| **Engine Physics & Collision System (`engine.py`)** | C | A / R |
| **Ghost AI Target Algorithms & BFS (`ghost_ai.py`)** | I | A / R |
| **Consumables & Buffs/Debuffs System (`consumables.py`)** | C | A / R |
| **Pygame Display Pipeline & Renderers (`src/ui/`)** | A / R | C |
| **Maze Wall Autotiling Bitmask Calculation** | A / R | C |
| **Input Translation & Command Queue (`inputhandler.py`)** | A / R | C |
| **Game UI Screens & Menu Transitions** | A / R | I |
| **HUD, Lives, Level Timer, Cheat Status Display** | A / R | C |
| **Game Save/Resume Serialization Logic** | C | A / R |
| **Save/Resume Menu Integration & Button States** | A / R | I |
| **Highscore Validation & File Persistence (`highscore.py`)** | I | A / R |
| **Highscore Table Screen & Name Input UI** | A / R | I |
| **XDG Directory Resolution (`data_dir.py`)** | I | A / R |
| **Animated Terminal Logger (`logger.py`)** | I | A / R |
| **Multi-Platform Packaging & PyInstaller (`PacMan.spec`)** | C | A / R |
| **Makefile Automation (`build`, `run`, `lint`, `clean`)** | R | A / R |
| **Static Typing (`mypy`) & Code Quality (`flake8`)** | R | A / R |
| **Documentation & 42 Subject Compliance (Chapters IV-IX)** | A / R | A / R |

---

## 3. Governance & Decision-Making Framework

To prevent conflicts and maintain high technical standards, the team established three core governance rules:

### Rule 1: Contract-First Design
Neither developer was permitted to write implementation code that relied on the other until the **Public Interface** was mutually reviewed, typed, and merged into `main`.
*Example*: Before `abchtaib` rendered ghosts, `yoelboud` defined `GhostState` (`CHASE`, `SCATTER`, `FRIGHTENED`, `EATEN`), `direction`, and continuous `(x, y)` coordinates. `abchtaib` could then build `render_ghost.py` using dummy mock objects without waiting for ghost pathfinding completion.

### Rule 2: Architecture Decision Records (ADRs)
When major technical forks arose, options were documented with trade-offs. Decisions were settled based on:
1. **Subject Compliance**: Strict alignment with the 42 Pac-Man specifications.
2. **Determinism & Testability**: Favoring pure functional logic and clean state isolation over implicit global mutations.
3. **User Experience**: Maintaining smooth 60 FPS rendering without visual jitter or input lag.

### Rule 3: Breaking Ties & Consensus
If a technical disagreement occurred:
1. An empirical benchmark or test harness was constructed (such as `terminal_test.py` or `pygame_test.py`).
2. The alternative requiring less coupling and fewer global side effects was chosen.
3. In matters strictly concerning graphic aesthetics, frame rendering, and user controls, `abchtaib` held casting vote.
4. In matters strictly concerning engine tick math, entity state rules, and algorithmic complexity, `yoelboud` held casting vote.

---

## 4. Communication & Synchronization Protocols

```
┌───────────────────────────────────────────────────────────────────────┐
│                       COMMUNICATION CHANNELS                         │
├─────────────────────┬───────────────────┬─────────────────────────────┤
│ Channel             │ Frequency         │ Purpose                     │
├─────────────────────┼───────────────────┼─────────────────────────────┤
│ 1337 Cluster Sync   │ Daily (in-person) │ • 10-minute standup at desk │
│                     │                   │ • Pair programming tricky   │
│                     │                   │   bugs (e.g. tile snapping) │
│                     │                   │ • Cross-machine integration │
├─────────────────────┼───────────────────┼─────────────────────────────┤
│ GitHub Pull Requests│ On feature finish │ • Code reviews              │
│ & Commit Logs       │                   │ • Merge conflict prevention │
│                     │                   │ • Static analysis check     │
├─────────────────────┼───────────────────┼─────────────────────────────┤
│ Discord Developer   │ Real-time async   │ • Sharing stack traces      │
│ Channel             │                   │ • Screenshot previews of UI │
│                     │                   │ • Sudden blocking alerts    │
└─────────────────────┴───────────────────┴─────────────────────────────┘
```

### Issue Handling & Incident Escalation Workflow
1. **Identification**: When a bug or unexpected behavior was detected, the discoverer documented the reproduction steps (seed, level, key sequence, error log).
2. **Triaging**:
   - If visual (e.g., sprite tear, misaligned button, incorrect color palette) $\rightarrow$ Assigned to `abchtaib`.
   - If logical (e.g., ghost passing through wall, timer discrepancy, score mismatch, save corruption) $\rightarrow$ Assigned to `yoelboud`.
   - If boundary/interface (e.g., input not propagating to engine, pause state freezing wrong counters) $\rightarrow$ Handled jointly via pair debugging.
3. **Verification**: A fix was only considered resolved when demonstrated across both local Linux workstations with `flake8` and `mypy` passing cleanly.
