"""Core game engine coordinating logic, states, collisions, and persistence."""

from __future__ import annotations

from dataclasses import asdict, replace
from enum import Enum, auto
import json
from typing import Any
from .config import Config, LevelConfig
from . import consumables
from .data_dir import DATA_DIR
from . import entities
from . import ghost_ai
from .logs import log, LogType
from .maze_adapter import MazeAdapter, MazeGrid


class EngineState(Enum):
    """High-level simulation state of the game engine."""

    PLAYING = auto()
    RESPAWNING = auto()
    GAME_OVER = auto()
    GAME_WON = auto()
    STOPPED = auto()


class Cheat(Enum):
    """Available developer and debugging cheats."""

    INVINCIBILITY = auto()
    LEVEL_SKIP = auto()
    GHOST_FREEZE = auto()
    EXTRA_LIVES = auto()
    INCREASE_SPEED = auto()


class GameEngine:
    """Core game engine managing characters, grid, levels, and game loop."""

    def __init__(self, config: Config) -> None:
        """Initialize the game engine with the given configuration.

        Args:
            config: Game configuration parameters.
        """
        self._config: Config = config
        self._maze_adapter: MazeAdapter = MazeAdapter()
        self._score: int = 0
        self._cur_level: int = 1
        self._state: EngineState = EngineState.RESPAWNING
        self._prev_state: EngineState = EngineState.RESPAWNING
        self._is_level_loaded: bool = False
        self._pacman: entities.PacMan
        self._ghosts: list[entities.Ghost] = []
        self._grid: MazeGrid
        self._levelconfig: LevelConfig
        self._is_game_over: bool = False
        self._level_time: float = 0.0
        self._respawn_timer: float = 3.0
        self._skip_level: bool = False

    @property
    def state(self) -> EngineState:
        """Return the current engine state.

        Returns:
            EngineState: Active simulation state.
        """
        return self._state

    @property
    def score(self) -> int:
        """Return the current player score.

        Returns:
            int: Total accumulated points.
        """
        return self._score

    def stop(self) -> None:
        """Pause engine execution and store previous state."""
        self._prev_state = self._state
        self._state = EngineState.STOPPED

    def resume(self) -> None:
        """Resume engine execution from paused state."""
        try:
            self._state = self._prev_state
        except AttributeError:
            pass  # no effect

    def activate_cheat(self, cheat: Cheat) -> None:
        """Execute a debug cheat modifying game or entity state.

        Args:
            cheat: The cheat enum to trigger.
        """
        match cheat:
            case Cheat.INVINCIBILITY:
                self._pacman.toggle_invincibility()
            case Cheat.INCREASE_SPEED:
                self._pacman.increase_speed()
            case Cheat.LEVEL_SKIP:
                self._skip_level = True
                consumables.Consumable.reset_counter()
            case Cheat.EXTRA_LIVES:
                self._pacman.add_life()
            case Cheat.GHOST_FREEZE:
                for ghost in self._ghosts:
                    ghost.freeze()
        log(f"Cheat activated: {cheat.name}", "Engine", LogType.INFO)

    def _calculate_level_max_time(self) -> float:
        """Calculate the level countdown timer based on pellet count.

        Returns:
            float: Maximum level duration in seconds.
        """
        total_pellets = consumables.Consumable.pellets()
        ratio = (
            3.0 * (self._levelconfig.ghost_speed / self._pacman.speed)
        )
        calculated = (total_pellets / self._config.pacman_speed) * ratio
        return max(calculated, 30.0)

    def _load_level(self, seed: int | None = None) -> None:
        """Generate maze grid, pellets, and spawn characters for the level.

        Args:
            seed: Optional custom seed override.
        """
        consumables.Consumable.reset_counter()
        levelconfig = self._config.generate_level(self._cur_level)
        if seed is not None and self._cur_level != 1:
            levelconfig = replace(levelconfig, seed=seed)
        self._grid = self._maze_adapter.generate_maze(levelconfig)
        self._levelconfig = levelconfig
        log(
            f"Level {self._cur_level} loaded with seed "
            f"{self._levelconfig.seed}",
            "Engine",
            LogType.INFO,
        )
        corners = {
            "top_left": (1, 1),
            "top_right": (self._grid.width - 2, 1),
            "bottom_left": (1, self._grid.height - 2),
            "bottom_right": (self._grid.width - 2, self._grid.height - 2),
        }
        center = (self._grid.width // 2, self._grid.height // 2)

        try:
            self._pacman = entities.PacMan(
                *self._grid.find_nearest_corridor(center),
                self._config.pacman_speed,
                self._grid,
                self._pacman.lives,
                "pacman",
            )
        except AttributeError:
            self._pacman = entities.PacMan(
                *self._grid.find_nearest_corridor(center),
                self._config.pacman_speed,
                self._grid,
                self._config.lives,
                "pacman",
            )

        pinky = entities.Ghost(
            *corners["top_left"],
            self._levelconfig.ghost_speed,
            self._grid,
            ghost_ai.PinkyStrategy(),
            self._pacman,
            "Pinky",
        )
        blinky = entities.Ghost(
            *corners["top_right"],
            self._levelconfig.ghost_speed,
            self._grid,
            ghost_ai.BlinkyStrategy(),
            self._pacman,
            "Blinky",
        )
        inky = entities.Ghost(
            *corners["bottom_right"],
            self._levelconfig.ghost_speed,
            self._grid,
            ghost_ai.InkyStrategy(),
            self._pacman,
            "Inky",
            blinky,
        )
        clyde = entities.Ghost(
            *corners["bottom_left"],
            self._levelconfig.ghost_speed,
            self._grid,
            ghost_ai.ClydeStrategy(),
            self._pacman,
            "Clyde",
        )
        self._ghosts = [pinky, blinky, inky, clyde]
        for row in self._grid.grid:
            for cell in row:
                is_wall = cell.is_wall
                is_corner = cell.is_corner(
                    self._grid.width, self._grid.height
                )
                if not is_wall and not is_corner:
                    score_eff = consumables.ScoreEffect(
                        self._config.points_per_pacgum
                    )
                    cell.add_consumable(consumables.PacGum([score_eff]))
                if is_corner:
                    cell.add_consumable(
                        consumables.SuperPacGum([
                            consumables.FrightenGhostsEffect(
                                self._levelconfig.frightened_duration
                            ),
                            consumables.ScoreEffect(
                                self._config.points_per_super_pacgum
                            ),
                            consumables.SpeedBuffEffect(
                                self._levelconfig.frightened_duration,
                                [self._pacman],
                            ),
                            consumables.SpeedDebuffEffect(
                                self._levelconfig.frightened_duration,
                                self._ghosts,
                            ),
                        ])
                    )
        self._is_game_over = False
        self._level_time = self._calculate_level_max_time()
        self._respawn_timer = 3.0
        self._is_level_loaded = True
        self._skip_level = False

    def _check_collisions(self) -> None:
        """Resolve collisions between Pac-Man, consumables, and ghosts."""
        if self.is_game_over or self.is_game_won or self.is_level_completed:
            return

        pacman_x, pacman_y = self._pacman.tile
        cell = self._grid.get_cell(pacman_x, pacman_y)
        for consumable in cell.consumes:
            consumable.effect(self)
        cell.remove_consumables()

        for ghost in self._ghosts:
            if self._pacman.can_eat_ghost(ghost):
                self.add_score(self._config.points_per_ghost)
                ghost.switch_state(entities.GhostState.DIED)
                log(
                    f"Pac-Man ate ghost {ghost.name} "
                    f"(+{self._config.points_per_ghost} pts)",
                    "Engine",
                    LogType.INFO,
                )
            elif ghost.can_eat_pacman():
                if self._pacman.is_alive:
                    self._pacman.lose_life()
                    if self._pacman.is_alive:
                        self._respawn()
                        break

            if not self._pacman.is_alive:
                self._is_game_over = True
                self._state = EngineState.GAME_OVER
                log(
                    "Game Over: All lives lost!",
                    "Engine",
                    LogType.WARNING,
                )
                break

    def _respawn(self) -> None:
        """Reset character positions and enter temporary respawn freeze."""
        self._pacman.respawn()
        for ghost in self._ghosts:
            ghost.respawn()
        self._state = EngineState.RESPAWNING
        self._respawn_timer = 3.0

    def add_score(self, score: int) -> None:
        """Add points to the current player score.

        Args:
            score: Points to add.
        """
        self._score += score

    @property
    def is_game_over(self) -> bool:
        """Check whether the game has ended in defeat.

        Returns:
            bool: True if game over.
        """
        return self._is_game_over

    @property
    def is_game_won(self) -> bool:
        """Check whether all levels have been beaten.

        Returns:
            bool: True if final level is completed.
        """
        return self._cur_level == 10 and self.is_level_completed

    @property
    def is_level_completed(self) -> bool:
        """Check whether all consumables have been cleared in this level.

        Returns:
            bool: True if no consumables remain or level was skipped.
        """
        return (
            not consumables.Consumable.still_any_consumables()
            or self._skip_level
        )

    def trigger_frightened_mode(self, duration: float) -> None:
        """Put all active ghosts into frightened fleeing mode.

        Args:
            duration: Duration in seconds.
        """
        for ghost in self._ghosts:
            ghost.active_frighten_mode(duration)

    def apply_effect(
        self,
        effect: entities.EntityEffect,
        duration: float | None = None,
        targets: Any = None,
    ) -> None:
        """Apply a status effect to designated target characters.

        Args:
            effect: Effect enum to apply.
            duration: Duration in seconds, or None for permanent.
            targets: Target entity, list, or designation string.
        """
        target_entities: list[entities.Entity] = []
        if targets == "pacman" or targets is None or targets is self._pacman:
            target_entities.append(self._pacman)
        elif targets == "ghosts" or targets is self._ghosts:
            target_entities.extend(self._ghosts)
        elif isinstance(targets, list):
            target_entities.extend(targets)

        for entity in target_entities:
            entity.activate_effect(effect, duration=duration)

    def increase_speed(
        self, duration: float, targets: Any = "pacman"
    ) -> None:
        """Apply a temporary speed buff to target characters.

        Args:
            duration: Duration in seconds.
            targets: Target entities.
        """
        self.apply_effect(
            entities.EntityEffect.SPEED_BUFF,
            duration=duration,
            targets=targets,
        )

    def decrease_speed(
        self, duration: float, targets: Any = "pacman"
    ) -> None:
        """Apply a temporary speed debuff to target characters.

        Args:
            duration: Duration in seconds.
            targets: Target entities.
        """
        self.apply_effect(
            entities.EntityEffect.SPEED_DEBUFF,
            duration=duration,
            targets=targets,
        )

    def _level_timer(self, dt: float) -> None:
        """Decrement level countdown timer and trigger game over on expiry.

        Args:
            dt: Delta time elapsed in seconds.
        """
        if self.is_game_over or self.is_game_won or self.is_level_completed:
            return

        self._level_time -= dt

        if self._level_time <= 0:
            self._is_game_over = True
            self._state = EngineState.GAME_OVER
            log(
                "Game Over: Level time expired!",
                "Engine",
                LogType.WARNING,
            )

    def _save_states(self) -> bool:
        """Safely serialize engine state and session config into a JSON file.

        Returns:
            bool: True if serialization and write succeeded, False otherwise.
        """
        try:
            states: dict[str, Any] = {
                "config": asdict(self._config),
                "engine": {
                    "_cur_level": self._cur_level,
                    "_score": self._score,
                    "_state": self._state.name,
                    "_respawn_timer": getattr(
                        self, "_respawn_timer", 3.0
                    ),
                    "_is_level_loaded": self._is_level_loaded,
                    "_level_time": (
                        getattr(self, "_level_time", None)
                        if self._is_level_loaded
                        else None
                    ),
                },
                "ghosts": {},
                "pacman": {},
                "maze_eaten": [],
                "seed": (
                    getattr(self._levelconfig, "seed", None)
                    if self._is_level_loaded
                    else None
                ),
            }

            if self._is_level_loaded:
                for ghost in self._ghosts:
                    states["ghosts"][ghost.name] = {
                        "_spawn_x": ghost.spawn[0],
                        "_spawn_y": ghost.spawn[1],
                        "_x": ghost.x,
                        "_y": ghost.y,
                        "_speed": ghost.speed,
                        "_cur_direction": ghost.cur_direction.name,
                        "_next_direction": ghost.next_direction.name,
                        "_state": ghost.state.name,
                        "_target_tile": (
                            ghost.target_tile if ghost.target_tile else None
                        ),
                        "_frightened_time": getattr(
                            ghost, "_frightened_time", 0.0
                        ),
                        "_effects": ghost.get_effects_state(),
                    }

                states["pacman"] = {
                    "_spawn_x": self._pacman.spawn[0],
                    "_spawn_y": self._pacman.spawn[1],
                    "_x": self._pacman.x,
                    "_y": self._pacman.y,
                    "_speed": self._pacman.speed,
                    "_lives": self._pacman.lives,
                    "_cur_direction": self._pacman.cur_direction.name,
                    "_next_direction": self._pacman.next_direction.name,
                    "_invincible": self._pacman.is_invincible,
                    "_effects": self._pacman.get_effects_state(),
                }

                for row in self._grid.grid:
                    for cell in row:
                        if not cell.is_wall and not cell.consumes:
                            states["maze_eaten"].append((cell.x, cell.y))

            states_file = DATA_DIR / "pacman_states.json"
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            states_file.write_text(
                json.dumps(states, indent=2), encoding="utf-8"
            )
            log(
                f"Engine state saved to '{states_file.name}'",
                "Engine",
                LogType.INFO,
            )
            return True

        except (OSError, TypeError) as err:
            log(f"Failed to save state ({err})", "Engine", LogType.WARNING)
        return False

    def _load_states(self) -> bool:
        """Safely deserialize engine state and session config from disk.

        Returns:
            bool: True if deserialization succeeded, False otherwise.
        """
        states_file = DATA_DIR / "pacman_states.json"

        if not states_file.is_file():
            log(
                f"Save file not found at {states_file}",
                "Engine",
                LogType.WARNING,
            )
            return False

        try:
            states = json.loads(states_file.read_text(encoding="utf-8"))
            if not states or not isinstance(states, dict):
                log("Invalid or empty save file", "Engine", LogType.WARNING)
                return False

            # load Config states
            if "config" in states and isinstance(states["config"], dict):
                self._config = Config(**states["config"])
                MazeAdapter.set_maze_size(
                    (self._config.width, self._config.height)
                )

            # load engine states
            engine_data = states.get("engine", {})
            if not engine_data:
                log(
                    "Engine data missing from save file",
                    "Engine",
                    LogType.WARNING,
                )

            self._cur_level = engine_data.get("_cur_level", 1)
            self._score = engine_data.get("_score", 0)

            if not engine_data.get("_is_level_loaded", False):
                state_name = engine_data.get("_state", "RESPAWNING")
                if state_name in EngineState.__members__:
                    self._state = EngineState[state_name]
                else:
                    self._state = EngineState.RESPAWNING
                self._respawn_timer = engine_data.get("_respawn_timer", 3.0)
                return True

            seed = states.get("seed", 42)
            self._load_level(seed)

            self._level_time = engine_data.get("_level_time", 90.0)
            state_name = engine_data.get("_state", "PLAYING")
            if state_name in EngineState.__members__:
                self._state = EngineState[state_name]
            else:
                self._state = EngineState.PLAYING
            self._respawn_timer = engine_data.get("_respawn_timer", 3.0)

            # load ghosts states
            saved_ghosts = states.get("ghosts", {})
            for ghost in self._ghosts:
                if ghost.name in saved_ghosts:
                    saved_gt = saved_ghosts[ghost.name]

                    cur_d_name = saved_gt.get("_cur_direction", "NONE")
                    next_d_name = saved_gt.get("_next_direction", "NONE")

                    if cur_d_name in entities.Direction.__members__:
                        cur_d = entities.Direction[cur_d_name]
                    else:
                        cur_d = entities.Direction.NONE

                    if next_d_name in entities.Direction.__members__:
                        next_d = entities.Direction[next_d_name]
                    else:
                        next_d = entities.Direction.NONE

                    st_name = saved_gt.get("_state", "WANDER")
                    if st_name in entities.GhostState.__members__:
                        ghost_state = entities.GhostState[st_name]
                    else:
                        ghost_state = entities.GhostState.WANDER

                    raw_target = saved_gt.get("_target_tile")
                    if raw_target and len(raw_target) == 2:
                        target_tile: tuple[int, int] | None = tuple(raw_target)
                    else:
                        target_tile = None

                    new_states = {
                        "_spawn_x": saved_gt.get(
                            "_spawn_x", ghost.spawn[0]
                        ),
                        "_spawn_y": saved_gt.get(
                            "_spawn_y", ghost.spawn[1]
                        ),
                        "_x": saved_gt.get("_x", ghost.x),
                        "_y": saved_gt.get("_y", ghost.y),
                        "_speed": saved_gt.get("_speed", ghost.speed),
                        "_cur_direction": cur_d,
                        "_next_direction": next_d,
                        "_state": ghost_state,
                        "_target_tile": target_tile,
                        "_frightened_time": saved_gt.get(
                            "_frightened_time", 0.0
                        ),
                    }
                    ghost.update_fields(new_states)
                    if "_effects" in saved_gt:
                        ghost.set_effects_state(saved_gt["_effects"])

            # load pacman states
            pacman_data = states.get("pacman", {})
            if pacman_data:
                cur_d_name = pacman_data.get("_cur_direction", "NONE")
                next_d_name = pacman_data.get("_next_direction", "NONE")

                if cur_d_name in entities.Direction.__members__:
                    cur_d = entities.Direction[cur_d_name]
                else:
                    cur_d = entities.Direction.NONE

                if next_d_name in entities.Direction.__members__:
                    next_d = entities.Direction[next_d_name]
                else:
                    next_d = entities.Direction.NONE

                new_states = {
                    "_spawn_x": pacman_data.get(
                        "_spawn_x", self._pacman.spawn[0]
                    ),
                    "_spawn_y": pacman_data.get(
                        "_spawn_y", self._pacman.spawn[1]
                    ),
                    "_x": pacman_data.get("_x", self._pacman.x),
                    "_y": pacman_data.get("_y", self._pacman.y),
                    "_speed": pacman_data.get("_speed", self._pacman.speed),
                    "_lives": pacman_data.get("_lives", self._pacman.lives),
                    "_cur_direction": cur_d,
                    "_next_direction": next_d,
                    "_invincible": pacman_data.get("_invincible", False),
                }
                self._pacman.update_fields(new_states)
                if "_effects" in pacman_data:
                    self._pacman.set_effects_state(pacman_data["_effects"])
                elif pacman_data.get("_invincible", False):
                    self._pacman.activate_effect(
                        entities.EntityEffect.INVINCIBILITY
                    )

            # load maze states
            for x, y in states.get("maze_eaten", []):
                cell = self._grid.get_cell(x, y)
                if cell.consumes:
                    if consumables.Consumable.still_any_consumables():
                        consumables.Consumable.decrease_counter()
                cell.remove_consumables()

            self.stop()
            log(
                f"Engine state restored "
                f"(Level {self._cur_level}, Score {self._score})",
                "Engine",
                LogType.INFO,
            )
            return True

        except (json.JSONDecodeError, KeyError, OSError, ValueError) as err:
            log(f"Failed to load state ({err})", "Engine", LogType.WARNING)
            return False

    def tick(self, dt: float, pacman_direction: entities.Direction) -> None:
        """Advance the game simulation step by delta time.

        Args:
            dt: Frame elapsed time in seconds.
            pacman_direction: Directional input command for Pac-Man.
        """
        match self._state:
            case (
                EngineState.STOPPED
                | EngineState.GAME_OVER
                | EngineState.GAME_WON
            ):
                return

            case EngineState.RESPAWNING:
                if not self._is_level_loaded:
                    self._load_level()
                    return

                self._respawn_timer -= dt
                if self._respawn_timer <= 0:
                    self._state = EngineState.PLAYING

            case EngineState.PLAYING:
                self._pacman.request_direction(pacman_direction)
                self._pacman.update(dt)

                for ghost in self._ghosts:
                    ghost.update(dt)

                self._check_collisions()
                self._level_timer(dt)

                if self.is_game_won:
                    self._state = EngineState.GAME_WON
                    log(
                        "Game Won! All levels completed!",
                        "Engine",
                        LogType.INFO,
                    )
                elif self.is_level_completed:
                    log(
                        f"Level {self._cur_level} cleared! "
                        f"Advancing to level {self._cur_level + 1}.",
                        "Engine",
                        LogType.INFO,
                    )
                    self._cur_level += 1
                    self._is_level_loaded = False
                    self._state = EngineState.RESPAWNING
