# Actual Progress Tracking vs. Timeline Baseline

*42 Network / 1337 Coding School — Pac-Man Project Management*

---

## 1. Schedule Variance Analysis

Throughout the 8-week lifecycle, weekly retrospectives compared actual feature completion against the initial baseline roadmap. The project concluded strictly on time for the November 11 target, with internal schedule adjustments made to accommodate unexpected technical challenges.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      MILESTONE VARIANCE SUMMARY                        │
├─────────────────────────┬──────────────┬──────────────┬────────────────┤
│ Milestone               │ Baseline     │ Actual       │ Schedule Delta │
├─────────────────────────┼──────────────┼──────────────┼────────────────┤
│ M1: Architecture Gate   │ Sep 30, 2026 │ Oct 02, 2026 │ +2 days        │
│ M2: Alpha Playable Demo │ Oct 15, 2026 │ Oct 19, 2026 │ +4 days        │
│ M3: Beta Feature Ready  │ Oct 31, 2026 │ Nov 02, 2026 │ +2 days        │
│ M4: Final Gold Master   │ Nov 11, 2026 │ Nov 11, 2026 │ On Schedule    │
└─────────────────────────┴──────────────┴──────────────┴────────────────┘
```

---

## 2. Sprint-by-Sprint Variance Breakdown

| Sprint & Deliverable | Planned Days | Actual Days | Variance | Root Cause Analysis & Compensating Action |
| :--- | :---: | :---: | :---: | :--- |
| **Sprint 1: Maze Adapter & Wheel Integration** | 4 | 5 | +1 day | The external wheel `mazegenerator` required custom parsing to distinguish corridors from outer boundary walls. Resolved by introducing `MazeAdapter` class. |
| **Sprint 1: Config Parser (Lark Grammar)** | 3 | 4 | +1 day | Allowing `#`, `//`, and `/* */` comments required building a grammar with Lark before feeding clean JSON into `json.loads`. |
| **Sprint 2: Menu UI & Screen Transitions** | 5 | 5 | 0 days | Executed on schedule; door sliding animations completed cleanly. |
| **Sprint 2: Maze Autotiling (Bitmasking)** | 5 | 11 | **+6 days** | *Major Bottleneck*: Computing the 8-neighbor bitmask for outer and inner corner wall joints and mapping them accurately to the sprite sheet required extensive visual trial and error. |
| **Sprint 2: Continuous Physics & Turn Snapping** | 4 | 7 | **+3 days** | Continuous movement caused Pac-Man to get stuck at corner intersections if turning keys were pressed mid-tile. Required building a tile-center buffering algorithm. |
| **Sprint 3: Ghost AI Personalities (4 Ghosts)** | 5 | 4 | -1 day | Replicating the classic arcade targeting formulas (Pittman's Pac-Man Dossier) was straightforward once math vector helpers were established. |
| **Sprint 3: BFS Pathfinding Optimization** | 4 | 6 | +2 days | Standard recursive BFS caused occasional frame drops on larger mazes with dead-ends. Rewritten using an iterative deque with visited sets and fallback routing. |
| **Sprint 3: Entity Renderers (Pac-Man & Ghosts)** | 5 | 4 | -1 day | Reused modular pattern across `RenderPlayer` and `RenderGhost`, accelerating completion. |
| **Sprint 4: State Serialization (Save & Resume)** | 4 | 3 | -1 day | Having pure dataclasses with no pygame objects made JSON serialization clean and fast. |
| **Sprint 4: Highscores & Validation Screen** | 3 | 3 | 0 days | Developed smoothly; integrated XDG standard directory for persistent storage. |
| **Sprint 4: Animated Logger & Fault Tolerance** | 3 | 3 | 0 days | Integrated asynchronous Rich live spinners with bounded cropping and thread-safe file I/O. |
| **Sprint 4: Standalone Packaging (PyInstaller)** | 3 | 4 | +1 day | Authored `PacMan.spec` to bundle runtime dependencies, `.whl` modules, icons, and asset trees across Linux, macOS, and Windows. |
| **Sprint 4: Code Quality (Mypy, Flake8, Docs)** | 4 | 4 | 0 days | Strict enforcement completed across all 23 modules without regression. |

---

## 3. Git Commit Milestone Correlation Table

Every major project milestone is directly grounded in the Git version history of the repository:

| Date | Commit Hash | Author | Milestone / Achievement | Deliverable Impact |
| :--- | :--- | :--- | :--- | :--- |
| **2026-09-17** | `a364d19` | `yoelboud` | Initial repository structure | Established base Git environment. |
| **2026-09-24** | `262f861` | `yoelboud` | Created `MazeAdapter` | Encapsulated external `mazegenerator` wheel. |
| **2026-10-04** | `cb173b4` | `abchtaib` | `main_menu_done` | Completed Main Menu UI and asset loading. |
| **2026-10-07** | `da62e79` | `abchtaib` | Button hover effects | Added interactive visual feedback on menus. |
| **2026-10-17** | `4e9e310` | `yoelboud` | Pygame GUI test harness & audit checklist | Created unified testing rig and engine audit. |
| **2026-10-18** | `07a6ce3` | `abchtaib` | Initial maze rendering | First connected wall textures rendered on screen. |
| **2026-10-19** | `69efc11` | `yoelboud` | Added `CellType.LOGO` for 42 wall | Supported custom colored walls for "42" maze branding. |
| **2026-10-23** | `97f637c` | `abchtaib` | Refined autotiling bitmasking | Fixed seamless wall connections across all 8 neighbors. |
| **2026-10-26** | `c769035` | `abchtaib` | Consumables rendering | Implemented normal pacgums and pulsing super pacgums. |
| **2026-10-26** | `fbe1c96` | `abchtaib` | Pac-Man player rendering | Directional mouth-chomping animation integrated. |
| **2026-10-27** | `747ff49` | `abchtaib` | Ghost rendering | Added 4 ghost colors, frightened blue, and eaten eyes. |
| **2026-10-31** | `cd65b1e` | `yoelboud` | Project root entry point `pac_man.py` | Unified application controller linking UI and Engine. |
| **2026-11-02** | `fe67d0c` | `abchtaib` | Cheat mode UI | Added HUD overlays for active cheats (Invincible, Freeze, etc.). |
| **2026-11-02** | `5a8f71a` | `yoelboud` | Buffs and debuffs system | Wired engine effects to speed boost, freeze, and invincibility. |
| **2026-11-04** | `df93f9f` | `yoelboud` | Off-center turn freezing fix | Critical bug fix ensuring Pac-Man snaps to corridor centers. |
| **2026-11-07** | `3a436f9` | `yoelboud` | Flake8, Mypy and Docstring sweep | Cleaned entire codebase to 100% strict compliance. |
| **2026-11-07** | `6590de3` | `yoelboud` | BFS pathfinding optimization | Eliminated ghost hesitation and CPU spikes on large mazes. |
| **2026-11-09** | `3b3d8f8` | `yoelboud` | Adopted `platformdirs` for XDG storage | Cleaned up save directory paths across Linux/macOS/Windows. |
| **2026-11-16** | `34da74f` | `yoelboud` | Refactor logger I/O & terminal overflow | Synchronized thread writes, added `vertical_overflow="crop"` and text truncation. |
| **2026-11-19** | `51fc7d9` | `yoelboud` | Add PyInstaller spec (`PacMan.spec`) | Multi-platform packaging for Linux, macOS (.app), and Windows. |
| **2026-11-19** | `ccda15f` | `yoelboud` | Makefile `build` automation | Added `make build` target for PyInstaller executable generation. |
| **2026-11-19** | `034598d` | `abchtaib` | Executable asset path resolution | Ensured frozen binary locates `assets/` and runtime bundles cleanly. |
| **2026-11-20** | `9e62770` | `yoelboud` | Pause and stop menu integration | Polished in-game pause workflow and state transitions. |
| **2026-11-20** | `1434fba` | `abchtaib` | Documentation & UI synchronization | Synchronized documentation with latest game features. |

---

## 4. Cumulative Velocity & Delivery Trajectory

```
Tasks Completed
    ▲
 30 ┼─────────────────────────────────────────────────────────────● Gold Master (28 tasks)
    │                                                      ╭──────╯
 25 ┼────────────────────────────────────────────────╭─────╯
    │                                          ╭─────╯ Beta Complete
 20 ┼────────────────────────────────────╭─────╯ (21 tasks)
    │                              ╭─────╯
 15 ┼────────────────────────╭─────╯ Alpha Demo (14 tasks)
    │                  ╭─────╯
 10 ┼────────────╭─────╯ Architecture Gate (8 tasks)
    │      ╭─────╯
  5 ┼──────╯
    │
  0 ┴──────┴───────────┴───────────┴───────────┴───────────┴───────────┴────────► Weeks
   W0     W1          W2          W4          W6          W7          W8
 (Sep 17)            (Sep 30)    (Oct 15)    (Oct 31)    (Nov 07)    (Nov 11)
```

### Key Takeaways from Tracking
1. **Concurrency Succeeded**: Splitting logic and rendering into decoupled modules allowed `abchtaib` to spend 6 extra days perfecting the complex autotiling visual system without blocking `yoelboud` from advancing the ghost AI and physics engine.
2. **Integration Gates Prevented End-of-Project Chaos**: Holding structured Alpha (Oct 19) and Beta (Nov 02) checkpoints caught integration mismatches early, leaving the final 10 days purely for polishing, static analysis, and documentation.
