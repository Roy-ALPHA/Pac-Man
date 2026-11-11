# Blocking Points, Technical Challenges & Conflict Resolution

*42 Network / 1337 Coding School — Pac-Man Project Management*

---

## 1. Overview of Project Blocking Points

During the 8-week engineering lifecycle of the Pac-Man project, several non-trivial technical hurdles and workflow bottlenecks were encountered. Because the team maintained high code quality and strict architectural boundaries, each blocker was documented, diagnosed, and resolved systematically without compromising project delivery.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MAJOR BLOCKING POINTS                           │
├─────────┬───────────────────────────┬───────────────┬──────────────────┤
│ Blocker │ Description               │ Domain        │ Resolution       │
├─────────┼───────────────────────────┼───────────────┼──────────────────┤
│ **BP-01**| Off-Center Turn Freezing  | Physics Math  | Buffer & Snap    │
│ **BP-02**| Leaky Model-View Coupling | Architecture  | PlayEngine Facade│
│ **BP-03**| 8-Neighbor Autotiling Del | Rendering     | Bitmask Atlas    │
│ **BP-04**| Git Divergence on Effects | Version Ctrl  | 3-Way Desk Merge │
│ **BP-05**| Mypy & Flake8 Violations  | Code Quality  | Sprint 4 Sweep   │
└─────────┴───────────────────────────┴───────────────┴──────────────────┘
```

---

## 2. In-Depth Analysis of Critical Blockers

### Blocker BP-01: Floating-Point Coordinate Drift & Off-Center Freezing
- **The Challenge**:
  Entities in `entities.py` update their positions continuously based on variable frame delta times:
  $$x_{\text{new}} = x_{\text{old}} + v_x \cdot \Delta t$$
  When a player queued a direction change (e.g. from RIGHT to UP), if the key was pressed when $x = 3.63$, attempting to turn UP immediately failed because $x = 3.63$ overlapped with a wall boundary. Pac-Man abruptly halted mid-corridor, unable to turn or advance forward.
- **Impact**: Game was virtually unplayable during rapid key sequences.
- **Collaborative Resolution**:
  - `abchtaib` identified the visual freezing behavior during menu-to-game transition testing.
  - `yoelboud` diagnosed the root cause in the collision detection logic.
  - The team implemented an **axis-locked turn buffering algorithm** (commit `df93f9f`): the requested direction is preserved in memory; Pac-Man continues moving in his existing direction until $\| x - \text{round}(x) \| < 0.1$, at which point his position is snapped to exact integer coordinates and the perpendicular velocity is engaged.

---

### Blocker BP-02: Leaky Abstraction & Tight Model-View Coupling
- **The Challenge**:
  During early development, the display test harness (`pygame_test.py`) directly accessed private engine attributes:
  ```python
  # ARCHITECTURAL SMELL (Pre-Refactor)
  for ghost in engine._ghosts:
      if ghost.state == GhostState.FRIGHTENED:
          surface.blit(blue_ghost, (ghost.x * tile, ghost.y * tile))
  ```
  Furthermore, `src/ui/screen.py` maintained mutable state variables at the class level (`Screen.door_closed = True`), causing side effects across different screens.
- **Impact**: Violations of the 42 subject's strict requirement for decoupled architecture; any change to engine internals broke the renderer.
- **Resolution**:
  - Created `PlayEngine` as a clean facade in `src/playscreen.py`, exposing only public, read-only properties (`pacman`, `ghosts`, `grid`, `score`, `lives`, `level_time`).
  - Removed all mutable class variables from `Screen`, enforcing instance encapsulation.
  - Renderers now only receive lightweight state snapshots and cannot mutate game physics.

---

### Blocker BP-03: Maze Wall Autotiling & Corner Bitmask Mapping
- **The Challenge**:
  Procedurally generated mazes from the `A-Maze-ing` package do not follow a fixed static map. Wall joints can form 256 distinct 8-neighbor combinations (isolated single walls, straight corridors, T-junctions, inner corners, outer bevels, and dead-ends). Mapping these configurations accurately to the sprite sheet created visual glitches where walls appeared disconnected.
- **Impact**: Threatened to delay Sprint 2 milestones by over a week.
- **Resolution**:
  - `abchtaib` created a standalone visualization script that loaded the sprite atlas and systematically tested every bitmask value against neighbor masks.
  - A lookup dictionary was implemented in `render_maze.py` that maps bitmask values to specific sprite rectangles. Outer wall borders and internal 42 logo blocks (`CellType.LOGO`) were given dedicated palette rules.

---

### Blocker BP-04: Git Merge Conflict on Entity Buffs & Debuffs
- **The Challenge**:
  On November 3, 2026, `yoelboud` implemented status effects (frightened timers, freeze, speed boosts) in `src/entities.py`, while `abchtaib` refactored cheat indicators and entity rendering in the same files. A simultaneous push caused significant merge conflicts across 10 files (commit `3c3d978`).
- **Impact**: High risk of code regression or overwritten features.
- **Resolution**:
  - The developers halted remote pushes and met in-person at the 1337 school cluster.
  - A temporary branch `temp-save` was created to isolate the work.
  - Each conflict in `entities.py` and `engine.py` was resolved line-by-line using git diff tools, ensuring that typed entity interfaces were preserved.
  - Unit tests and headless engine runs verified zero functional regressions before merging back into `main`.

---

### Blocker BP-05: Strict Static Typing (`mypy`) & PEP 8 (`flake8`) Compliance
- **The Challenge**:
  Prior to Sprint 4, running `mypy . --strict` reported over 40 typing errors, including untyped Lark grammar returns, missing optional types (`Optional[PacMan]`), and dynamic dictionary values. `flake8` reported line-length and unused import warnings.
- **Impact**: Inability to pass the mandatory automated audit guidelines in Chapter III and X.
- **Resolution**:
  - Conducted a dedicated code quality sprint (commit `3a436f9` and `1c86914`).
  - Added explicit type annotations (`int`, `float`, `Tuple[int, int]`, `Optional[T]`) across all classes and functions.
  - Added complete PEP 257 docstrings for all modules, classes, and public methods.
  - Result: 0 `flake8` errors, 0 `mypy` warnings.

---

## 3. Team Dynamics & Conflict Resolution Governance

When technical opinions diverged, the team adhered to three established principles:

### 1. Evidence-Based Decision Making
Opinions were replaced by demonstrable proof:
- If a debate arose over pathfinding algorithms (A* vs. BFS), execution time benchmarks on a $31 \times 31$ grid proved BFS was both faster and mathematically identical for unit-cost grids.
- If a dispute arose over configuration parsing, real-world examples with `#` and `/* */` comments demonstrated why a Lark grammar was necessary over raw `json.loads`.

### 2. Respect for Domain Ownership
- **Visuals & UX**: `abchtaib` made final calls regarding menu pacing, button hover responsiveness, sprite animation frame rates, and color schemes.
- **Physics & Engine Math**: `yoelboud` made final calls regarding tick discretization, continuous velocity equations, BFS deque traversal, and state serialization.

### 3. Open Retrospective Culture
At the end of each sprint, the team held a brief retrospective asking:
- *What went well?* (Decoupled MVC architecture enabled rapid parallel coding).
- *What slowed us down?* (Underestimating wall autotiling edge cases).
- *What must we adjust?* (Define interface types earlier before beginning implementation).

This collaborative mindset enabled both developers to complete the project smoothly, deliver an exceptional game, and exceed all 42 project management expectations.
