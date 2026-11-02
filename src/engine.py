from . import entities
from . import ghost_ai
from . import consumables
from enum import Enum, auto
from .maze_adapter import MazeAdapter
import os
from pathlib import Path
import sys
import json
from dataclasses import asdict, replace
from .config import Config
from .logs import log, LogType


class EngineState(Enum):
    PLAYING = auto()
    RESPAWNING = auto()
    GAME_OVER = auto()
    GAME_WON = auto()
    STOPPED = auto()


class Cheat(Enum):
    INVINCIBILITY = auto()
    LEVEL_SKIP = auto()
    GHOST_FREEZE = auto()
    EXTRA_LIVES = auto()
    INCREASE_SPEED = auto()


class GameEngine:

    def __init__(self, config):
        self._config = config
        self._maze_adapter = MazeAdapter()
        self._score = 0
        self._cur_level = 1
        self._state = EngineState.RESPAWNING
        self._is_level_loaded = False
        self._data_dir = self._get_save_path()

    @staticmethod
    def _calc_spawn(grid, def_spawn_coor):
        def_x, def_y = def_spawn_coor

        if not grid.is_wall(def_x, def_y):
            return def_x, def_y

        for direction in entities.PRIORITY_DIRECTIONS:
            x = def_x + direction.dx
            y = def_y + direction.dy

            if not grid.is_wall(x, y):
                return x, y

    @property
    def state(self):
        return self._state

    @property
    def score(self):
        return self._score

    def stop(self):
        self._prev_state = self._state
        self._state = EngineState.STOPPED

    def resume(self):
        try:
            self._state = self._prev_state
        except AttributeError:
            pass  # no effect

    def activate_cheat(self, cheat: Cheat):
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

    def _calculate_level_max_time(self):
        total_pellets = consumables.Consumable.pellets()
        return 1000
        return (total_pellets / self._config.pacman_speed) * (3.0 * (self._levelconfig.ghost_speed / self._pacman.speed))

    def _load_level(self, seed=None):
        consumables.Consumable.reset_counter()
        levelconfig = self._config.generate_level(self._cur_level)
        if seed is not None and self._cur_level != 1:
            levelconfig = replace(levelconfig, seed=seed)
        self._grid = self._maze_adapter.generate_maze(levelconfig)
        self._levelconfig = levelconfig
        log(f"Level {self._cur_level} loaded with seed {self._levelconfig.seed}", "Engine", LogType.INFO)
        corners = {
            "top_left": (1, 1),
            "top_right": (self._grid.width - 2, 1),
            "bottom_left": (1, self._grid.height - 2),
            "bottom_right": (self._grid.width - 2, self._grid.height - 2)
        }
        center = (self._grid.width // 2, self._grid.height // 2)

        try:
            self._pacman = entities.PacMan(
                *self._grid.find_nearest_corridor(center),
                self._config.pacman_speed,
                self._grid,
                self._pacman.lives,
                "pacman"
            )
        except AttributeError:
            self._pacman = entities.PacMan(
                *center,
                self._config.pacman_speed,
                self._grid,
                self._config.lives,
                "pacman"
            )

        pinky = entities.Ghost(
            *corners["top_left"],
            self._levelconfig.ghost_speed,
            self._grid,
            ghost_ai.PinkyStrategy(),
            self._pacman,
            "Pinky"
        )
        blinky = entities.Ghost(
            *corners["top_right"],
            self._levelconfig.ghost_speed,
            self._grid,
            ghost_ai.BlinkyStrategy(),
            self._pacman,
            "Blinky"
        )
        inky = entities.Ghost(
            *corners["bottom_right"],
            self._levelconfig.ghost_speed,
            self._grid,
            ghost_ai.InkyStrategy(),
            self._pacman,
            "Inky",
            blinky
        )
        clyde = entities.Ghost(
            *corners["bottom_left"],
            self._levelconfig.ghost_speed,
            self._grid,
            ghost_ai.ClydeStrategy(),
            self._pacman,
            "Clyde"
        )
        self._ghosts = [pinky, blinky, inky, clyde]
        for row in self._grid.grid:
            for cell in row:
                is_wall = cell.is_wall
                is_corner = cell.is_corner(self._grid.width, self._grid.height)
                if not is_wall and not is_corner:
                    cell.add_consumable(consumables.PacGum([consumables.ScoreEffect(self._config.points_per_pacgum)]))
                if is_corner:
                    cell.add_consumable(consumables.SuperPacGum([
                        consumables.FrightenGhostsEffect(self._levelconfig.frightened_duration),
                        consumables.ScoreEffect(self._config.points_per_super_pacgum)
                        ]))
        self._is_game_over = False
        self._level_time = self._calculate_level_max_time()
        self._respawn_timer = 3.0
        self._is_level_loaded = True
        self._skip_level = False

    def _check_collisions(self):
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
            elif ghost.can_eat_pacman():
                if self._pacman.is_alive:
                    self._pacman.lose_life()
                    if self._pacman.is_alive:
                        self._respawn()
                        break

            if not self._pacman.is_alive:
                self._is_game_over = True
                self._state = EngineState.GAME_OVER
                break

    def _respawn(self):
        self._pacman.respawn()
        for ghost in self._ghosts:
            ghost.respawn()
        self._state = EngineState.RESPAWNING
        self._respawn_timer = 3.0

    def add_score(self, score):
        self._score += score

    @property
    def is_game_over(self):
        return self._is_game_over

    @property
    def is_game_won(self):
        return self._cur_level == 10 and self.is_level_completed

    @property
    def is_level_completed(self):
        return not consumables.Consumable.still_any_consumables() or self._skip_level

    def trigger_frightened_mode(self, duration):
        for ghost in self._ghosts:
            ghost.active_frighten_mode(duration)

    def _level_timer(self, dt):
        if self.is_game_over or self.is_game_won or self.is_level_completed:
            return

        self._level_time -= dt

        if self._level_time <= 0:
            self._is_game_over = True
            self._state = EngineState.GAME_OVER

    def _save_states(self) -> bool:                                                                                                                                                                 
            """Safely serialize engine state and session config into a single atomic file."""                                                                                                           
            try:                                                                                                                                                                                        
                states = {                                                                                                                                                                              
                    # 1. Embed session configuration so next levels scale consistently                                                                                                                  
                    "config": asdict(self._config),                                                                                                                                                     
                    "engine": {                                                                                                                                                                         
                        "_cur_level": self._cur_level,                                                                                                                                                  
                        "_score": self._score,                                                                                                                                                          
                        "_state": self._state.name,                                                                                                                                                     
                        "_respawn_timer": getattr(self, "_respawn_timer", 3.0),                                                                                                                         
                        "_is_level_loaded": self._is_level_loaded,                                                                                                                                      
                        "_level_time": getattr(self, "_level_time", None) if self._is_level_loaded else None,                                                                                           
                    },                                                                                                                                                                                  
                    "ghosts": {},                                                                                                                                                                       
                    "pacman": {},                                                                                                                                                                       
                    "maze_eaten": [],                                                                                                                                                                   
                    "seed": getattr(self._levelconfig, "seed", None) if self._is_level_loaded else None,                                                                                                
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
                            "_target_tile": ghost.target_tile if ghost.target_tile else None,                                                                                                     
                            "_frightened_time": getattr(ghost, "_frightened_time", 0.0),                                                                                                                
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
                    }
                                                                                                                                                                                                        
                    for row in self._grid.grid:                                                                                                                                                         
                        for cell in row:                                                                                                                                                                
                            if not cell.is_wall and not cell.consumes:                                                                                                                                  
                                states["maze_eaten"].append((cell.x, cell.y))                                                                                                                           
                                                                                                                                                                                                        
                states_file = self._data_dir / "pacman_states.json"
                self._data_dir.mkdir(parents=True, exist_ok=True)
                states_file.write_text(json.dumps(states, indent=2), encoding="utf-8")
                log(f"Engine state saved to '{states_file.name}'", "Engine", LogType.INFO)
                return True

            except (OSError, TypeError) as err:
                log(f"Failed to save state ({err})", "Engine", LogType.WARNING)
            return False

    def _load_states(self) -> bool:
        """Safely deserialize engine state and session config from disk."""
        states_file = self._data_dir / "pacman_states.json"

        if not states_file.is_file():
            log(f"Save file not found at {states_file}", "Engine", LogType.WARNING)
            return False

        try:
            states = json.loads(states_file.read_text(encoding="utf-8"))
            if not states or not isinstance(states, dict):
                log("Invalid or empty save file", "Engine", LogType.WARNING)
                return False

            # load Config states
            if "config" in states and isinstance(states["config"], dict):
                self._config = Config(**states["config"])
                MazeAdapter.set_maze_size((self._config.width, self._config.height))

            # load engine states
            engine_data = states.get("engine", {})
            if not engine_data:
                log("Engine data missing from save file", "Engine", LogType.WARNING)

            self._cur_level = engine_data.get("_cur_level", 1)
            self._score = engine_data.get("_score", 0)

            if not engine_data.get("_is_level_loaded", False):
                state_name = engine_data.get("_state", "RESPAWNING")
                self._state = EngineState[state_name] if state_name in EngineState.__members__ else EngineState.RESPAWNING
                self._respawn_timer = engine_data.get("_respawn_timer", 3.0)
                return True

            seed = states.get("seed", 42)
            self._load_level(seed)

            self._level_time = engine_data.get("_level_time", 90.0)
            state_name = engine_data.get("_state", "PLAYING")
            self._state = EngineState[state_name] if state_name in EngineState.__members__ else EngineState.PLAYING
            self._respawn_timer = engine_data.get("_respawn_timer", 3.0)

            # load ghosts states
            saved_ghosts = states.get("ghosts", {})
            for ghost in self._ghosts:
                if ghost.name in saved_ghosts:
                    saved_gt_state = saved_ghosts[ghost.name]

                    cur_d = saved_gt_state.get("_cur_direction", "NONE")
                    next_d = saved_gt_state.get("_next_direction", "NONE")

                    cur_d = entities.Direction[cur_d] if cur_d in entities.Direction.__members__ else entities.Direction.NONE
                    next_d = entities.Direction[next_d] if next_d in entities.Direction.__members__ else entities.Direction.NONE

                    ghost_state = saved_gt_state.get("_state", "WANDER")
                    ghost_state = entities.GhostState[ghost_state] if ghost_state in entities.GhostState.__members__ else entities.GhostState.WANDER

                    raw_target = saved_gt_state.get("_target_tile")

                    new_states = {
                        "_spawn_x": saved_gt_state.get("_spawn_x", ghost.spawn[0]),
                        "_spawn_y": saved_gt_state.get("_spawn_y", ghost.spawn[1]),
                        "_x": saved_gt_state.get("_x", ghost.x),
                        "_y": saved_gt_state.get("_y", ghost.y),
                        "_speed": saved_gt_state.get("_speed", ghost.speed),
                        "_cur_direction": cur_d,
                        "_next_direction": next_d,
                        "_state": ghost_state,
                        "_target_tile": tuple(raw_target) if raw_target and len(raw_target) == 2 else None,
                        "_frightened_time": saved_gt_state.get("_frightened_time", 0.0),
                    }
                    ghost.update_fields(new_states)

            # load pacman states
            pacman_data = states.get("pacman", {})
            if pacman_data:
                cur_d = pacman_data.get("_cur_direction", "NONE")
                next_d = pacman_data.get("_next_direction", "NONE")

                cur_d = entities.Direction[cur_d] if cur_d in entities.Direction.__members__ else entities.Direction.NONE
                next_d = entities.Direction[next_d] if next_d in entities.Direction.__members__ else entities.Direction.NONE

                new_states = {
                    "_spawn_x": pacman_data.get("_spawn_x", self._pacman.spawn[0]),
                    "_spawn_y": pacman_data.get("_spawn_y", self._pacman.spawn[1]),
                    "_x": pacman_data.get("_x", self._pacman.x),
                    "_y": pacman_data.get("_y", self._pacman.y),
                    "_speed": pacman_data.get("_speed", self._pacman.speed),
                    "_lives": pacman_data.get("_lives", self._pacman.lives),
                    "_cur_direction": cur_d,
                    "_next_direction": next_d,
                    "_invincible": pacman_data.get("_invincible", False),
                }
                self._pacman.update_fields(new_states)

            # load maze states
            for x, y in states.get("maze_eaten", []):
                cell = self._grid.get_cell(x, y)
                if cell.consumes:
                    if consumables.Consumable.still_any_consumables():
                        consumables.Consumable.decrease_counter()
                cell.remove_consumables()

            self.stop()
            log(f"Engine state restored (Level {self._cur_level}, Score {self._score})", "Engine", LogType.INFO)
            return True

        except (json.JSONDecodeError, KeyError, OSError, ValueError) as err:
            log(f"Failed to load state ({err})", "Engine", LogType.WARNING)
            return False

    @staticmethod
    def _get_save_path(app_name: str = "pacman") -> Path:
        if sys.platform == "win32":
            # 1. Windows: %LOCALAPPDATA% or %APPDATA%
            base_dir = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
            if base_dir:
                data_dir = Path(base_dir) / app_name
            else:
                data_dir = Path.home() / "AppData" / "Local" / app_name

        elif sys.platform == "darwin":
            # 2. macOS: ~/Library/Application Support/<app_name>
            data_dir = Path.home() / "Library" / "Application Support" / app_name

        else:
            # 3. Linux & POSIX (XDG Base Directory Spec)
            xdg_data = os.getenv("XDG_DATA_HOME")
            if xdg_data:
                data_dir = Path(xdg_data) / app_name
            else:
                home = os.getenv("HOME")
                base = (
                    Path(home) / ".local" / "share"
                    if home
                    else Path.home() / ".local" / "share"
                )
            data_dir = base / app_name

        # Create directories if they don't exist yet
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def tick(self, dt, pacman_direction):
        match self._state:
            case EngineState.STOPPED | EngineState.GAME_OVER | EngineState.GAME_WON:
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
                elif self.is_level_completed:
                    self._cur_level += 1
                    self._is_level_loaded = False
                    self._state = EngineState.RESPAWNING
