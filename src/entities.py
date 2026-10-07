from abc import ABC, abstractmethod
from enum import Enum, auto
import math


class GhostState(Enum):
    CHASE = auto()
    FRIGHTENED = auto()
    WANDER = auto()
    DIED = auto()
    FROZEN = auto()


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    NONE = (0, 0)

    @property
    def dx(self) -> int:
        return self.value[0]

    @property
    def dy(self) -> int:
        return self.value[1]

    def opposite(self) -> "Direction":
        opposites = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
            Direction.NONE: Direction.NONE,
        }
        return opposites[self]


PRIORITY_DIRECTIONS = [Direction.UP, Direction.LEFT, Direction.DOWN, Direction.RIGHT]


class Entity(ABC):
    def __init__(self, spawn_x, spawn_y, speed, grid):
        self._spawn_x = spawn_x
        self._spawn_y = spawn_y
        self._x = spawn_x
        self._y = spawn_y
        self._speed = speed
        self._grid = grid
        self._cur_direction = Direction.NONE
        self._next_direction = Direction.NONE

    @property
    def cur_direction(self):
        return self._cur_direction

    @property
    def tile(self):
        return (round(self._x), round(self._y))

    @property
    def spawn(self):
        return self._spawn_x, self._spawn_y

    def increase_speed(self):
        self._speed += 2

    def respawn(self):
        self._x, self._y = self._spawn_x, self._spawn_y
        self._cur_direction = Direction.NONE
        self._next_direction = Direction.NONE

    def can_move(self, direction):
        if direction is Direction.NONE:
            return False
        tile_x, tile_y = self.tile
        target_x = tile_x + direction.dx
        target_y = tile_y + direction.dy
        return not self._grid.is_wall(target_x, target_y)

    def _move(self, distance: float, direction):
        self._x += direction.dx * distance
        self._y += direction.dy * distance

    def _move_to_center_and_stop(self, distance):
        center_x, center_y = self.tile
        remaining = (center_x - self._x) * self._cur_direction.dx + (center_y - self._y) * self._cur_direction.dy
        if remaining <= 0 or distance >= remaining:
            self._x, self._y = float(center_x), float(center_y)
            self._cur_direction = Direction.NONE
            if self.can_move(self._next_direction):
                self._move(distance - max(0.0, remaining), self._next_direction)
                self._cur_direction = self._next_direction
                self._next_direction = Direction.NONE
        else:
            self._move(distance, self._cur_direction)

    def _calc_movement(self, distance):
        if self._cur_direction is Direction.NONE:
            if self.can_move(self._next_direction):
                self._cur_direction = self._next_direction
                self._next_direction = Direction.NONE
                self._move(distance, self._cur_direction)
            return

        if self._cur_direction.opposite() is self._next_direction:
            self._move(distance, self._next_direction)
            self._cur_direction = self._next_direction
            self._next_direction = Direction.NONE
            return

        if not self.can_move(self._cur_direction) or self._next_direction is not Direction.NONE:
            self._move_to_center_and_stop(distance)
        else:
            self._move(distance, self._cur_direction)

    def __eq__(self, other):
        return self.tile == other.tile

    @abstractmethod
    def update(self, dt):
        pass


class PacMan(Entity):
    def __init__(self, spawn_x, spawn_y, speed, grid, lives):
        super().__init__(spawn_x, spawn_y, speed, grid)
        self._lives = lives
        self._invincible = False

    @property
    def is_alive(self):
        return self._lives > 0

    @property
    def is_invincible(self):
        return self._invincible

    def can_eat_ghost(self, ghost):
        return ghost == self and ghost.is_frighten

    def toggle_invincibility(self):
        self._invincible = not self._invincible

    def lose_life(self):
        if self.is_alive:
            self._lives -= 1

    def add_life(self):
        if self.is_alive:
            self._lives += 1

    def request_direction(self, direction):
        self._next_direction = direction

    def update(self, dt):
        if not self.is_alive:
            return

        distance = self._speed * dt
        self._calc_movement(distance)


class Ghost(Entity):
    def __init__(self, spawn_x, spawn_y, speed, grid, strategy, pacman, blinky=None):
        super().__init__(spawn_x, spawn_y, speed, grid)
        self._state = GhostState.DIED
        self._strategy = strategy
        self._pacman = pacman
        self._blinky = blinky

    @property
    def is_frighten(self):
        return self._state is GhostState.FRIGHTENED

    @property
    def state(self):
        return self._state

    def _request_direction(self, blinky=None):
        self._next_direction = self._strategy.compute_next_move(
            self, self._pacman, self._grid, blinky
        )

    def switch_state(self, new_state):
        self._state = new_state

    def can_eat_pacman(self):
        return self._pacman == self and not self._pacman.is_invincible and self.state in {GhostState.WANDER, GhostState.CHASE}

    def active_frighten_mode(self, duration):
        self.switch_state(GhostState.FRIGHTENED)
        self._frightened_time = duration

    def update(self, dt):
        distance = self._speed * dt

        dist = math.dist(self.tile, self._pacman.tile)
        distance_to_tile_center = math.dist((self._x, self._y), self.tile)

        match self._state:
            case GhostState.FRIGHTENED:
                self._frightened_time -= dt
                if self._frightened_time <= 0:
                    self.switch_state(GhostState.WANDER)
            case GhostState.DIED if self.tile == (self._spawn_x, self._spawn_y):
                self.switch_state(GhostState.WANDER)
            case GhostState.WANDER if dist <= 10:
                self.switch_state(GhostState.CHASE)
            case GhostState.CHASE if dist > 10:
                self.switch_state(GhostState.WANDER)
            case GhostState.FROZEN:
                return

        if self._pacman.is_invincible and self._state not in {GhostState.WANDER, GhostState.FRIGHTENED}:
            self.switch_state(GhostState.WANDER)

        if not self.can_move(self._cur_direction) or not distance_to_tile_center:
            self._request_direction(self._blinky)

        self._calc_movement(distance)
