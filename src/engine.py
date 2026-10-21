from . import entities
from . import ghost_ai
from . import consumables
from enum import Enum, auto
from .maze_adapter import MazeAdapter

f = open("logs.txt", "w")

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

    def _load_level(self):
        consumables.Consumable.reset_counter()
        levelconfig = self._config.generate_level(self._cur_level)
        self._grid = self._maze_adapter.generate_maze(levelconfig)
        self._levelconfig = levelconfig
        corners = {
            "top_left": (1, 1),
            "top_right": (self._grid.width - 2, 1),
            "bottom_left": (1, self._grid.height - 2),
            "bottom_right": (self._grid.width - 2, self._grid.height - 2)
        }
        center = (self._grid.width // 2, self._grid.height // 2)

        try:
            self._pacman = entities.PacMan(
                *center,
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
        self._level_time = self._levelconfig.level_max_time
        self._respawn_timer = 3.0
        self._is_level_loaded = True
        self._skip_level = False

    def _check_collisions(self):
        if self.is_game_over or self.is_game_won or self.is_level_completed:
            return

        pacman_x, pacman_y = self._pacman.tile
        cell = self._grid.grid[pacman_y][pacman_x]
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
