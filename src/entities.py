"""Entities, direction vectors, and character state models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import TYPE_CHECKING, Any
from .logs import log, LogType

if TYPE_CHECKING:
    from .ghost_ai import GhostStrategy
    from .maze_adapter import MazeGrid


class GhostState(Enum):
    """Behavioral state of a ghost entity."""

    CHASE = auto()
    FRIGHTENED = auto()
    WANDER = auto()
    DIED = auto()


class EntityEffect(Enum):
    """Temporary or permanent status effects applied to an entity."""

    SPEED_BUFF = auto()
    SPEED_DEBUFF = auto()
    INVINCIBILITY = auto()
    FREEZE = auto()


class Direction(Enum):
    """Movement direction vectors on the 2D maze grid."""

    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    NONE = (0, 0)

    @property
    def dx(self) -> int:
        """Return horizontal step component.

        Returns:
            int: -1, 0, or 1.
        """
        return self.value[0]

    @property
    def dy(self) -> int:
        """Return vertical step component.

        Returns:
            int: -1, 0, or 1.
        """
        return self.value[1]

    def opposite(self) -> "Direction":
        """Return the opposite direction vector.

        Returns:
            Direction: Directly reverse direction.
        """
        opposites = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
            Direction.NONE: Direction.NONE,
        }
        return opposites[self]


PRIORITY_DIRECTIONS = [
    Direction.UP,
    Direction.LEFT,
    Direction.DOWN,
    Direction.RIGHT,
]


class Entity(ABC):
    """Abstract base class for all movable grid characters."""

    def __init__(
        self,
        spawn_x: float,
        spawn_y: float,
        speed: float,
        grid: MazeGrid,
        name: str,
    ) -> None:
        """Initialize base entity attributes and coordinates.

        Args:
            spawn_x: Initial horizontal spawn tile coordinate.
            spawn_y: Initial vertical spawn tile coordinate.
            speed: Base speed in tiles per second.
            grid: Active maze grid reference.
            name: Human-readable entity name.
        """
        self._spawn_x: float = spawn_x
        self._spawn_y: float = spawn_y
        self._x: float = float(spawn_x)
        self._y: float = float(spawn_y)
        self._speed: float = float(speed)
        self._grid: MazeGrid = grid
        self._cur_direction: Direction = Direction.NONE
        self._next_direction: Direction = Direction.NONE
        self._base_speed: float = self._speed
        self._name: str = name
        self._invincible: bool = False
        self._effects: dict[EntityEffect, float | None] = {}

    @property
    def name(self) -> str:
        """Return the entity's display name.

        Returns:
            str: Name identifier.
        """
        return self._name

    @property
    def cur_direction(self) -> Direction:
        """Return the current movement direction.

        Returns:
            Direction: Active movement direction.
        """
        return self._cur_direction

    @property
    def next_direction(self) -> Direction:
        """Return the buffered next movement direction.

        Returns:
            Direction: Pending queued direction.
        """
        return self._next_direction

    @property
    def is_invincible(self) -> bool:
        """Check whether the entity is invulnerable to death.

        Returns:
            bool: True if invincible, False otherwise.
        """
        return self._invincible

    @property
    def speed(self) -> float:
        """Return current effective movement speed.

        Returns:
            float: Speed in tiles per second.
        """
        return self._speed

    @property
    def x(self) -> float:
        """Return continuous horizontal position.

        Returns:
            float: Exact x position.
        """
        return self._x

    @property
    def y(self) -> float:
        """Return continuous vertical position.

        Returns:
            float: Exact y position.
        """
        return self._y

    @property
    def tile(self) -> tuple[int, int]:
        """Return rounded grid tile coordinates.

        Returns:
            tuple[int, int]: (tile_x, tile_y) on the grid.
        """
        return (round(self._x), round(self._y))

    @property
    def spawn(self) -> tuple[int, int]:
        """Return initial spawn tile coordinates.

        Returns:
            tuple[int, int]: (spawn_x, spawn_y) on the grid.
        """
        return round(self._spawn_x), round(self._spawn_y)

    @abstractmethod
    def respawn(self) -> None:
        """Reset entity position and state back to its spawn location."""
        pass

    def _recalculate_stats(self) -> None:
        """Recalculate dynamic stats from all currently active effects."""
        # 1. Handle Invincibility
        self._invincible = EntityEffect.INVINCIBILITY in self._effects

        # 2. Handle Speed & Freeze
        if EntityEffect.FREEZE in self._effects:
            self._speed = 0.0
        else:
            multiplier = 1.0
            if EntityEffect.SPEED_BUFF in self._effects:
                multiplier *= 1.5
            if EntityEffect.SPEED_DEBUFF in self._effects:
                multiplier *= 0.5
            self._speed = self._base_speed * multiplier

    def has_effect(self, effect: EntityEffect) -> bool:
        """Check whether a specific status effect is currently active.

        Args:
            effect: Effect to query.

        Returns:
            bool: True if effect is active, False otherwise.
        """
        return effect in self._effects

    def activate_effect(
        self, effect: EntityEffect, duration: float | None = None
    ) -> None:
        """Activate an effect with an optional timer.

        Args:
            effect: Effect to apply.
            duration: Duration in seconds, or None for permanent.
        """
        self._effects[effect] = duration
        self._recalculate_stats()
        dur_str = f"{duration:.1f}s" if duration is not None else "permanent"
        log(
            f"{self._name} gained {effect.name} ({dur_str})",
            "Entity",
            LogType.INFO,
        )

    def desactivate_effect(self, effect: EntityEffect) -> None:
        """Remove an effect and restore stats cleanly.

        Args:
            effect: Effect to remove.
        """
        if effect in self._effects:
            self._effects.pop(effect, None)
            self._recalculate_stats()
            log(
                f"{self._name} lost effect {effect.name}",
                "Entity",
                LogType.INFO,
            )

    def remove_all_effects(self) -> None:
        """Clear all active status effects and recalculate base stats."""
        self._effects.clear()
        self._recalculate_stats()

    def get_effects_state(self) -> dict[str, float | None]:
        """Serialize active effects to a JSON-compatible dict.

        Returns:
            dict[str, float | None]: Mapping of effect name to duration.
        """
        return {
            effect.name: duration for effect, duration in self._effects.items()
        }

    def set_effects_state(
        self, effects_data: dict[str, float | None]
    ) -> None:
        """Deserialize and re-apply effects from a dictionary.

        Args:
            effects_data: Dictionary mapping effect names to durations.
        """
        self._effects.clear()
        for effect_name, duration in effects_data.items():
            if effect_name in EntityEffect.__members__:
                self._effects[EntityEffect[effect_name]] = duration
        self._recalculate_stats()

    def check_effect_duration(self, dt: float) -> None:
        """Update effect timers and expire finished effects.

        Args:
            dt: Delta time elapsed in seconds.
        """
        if not self._effects:
            return

        updated_effects: dict[EntityEffect, float | None] = {}
        stats_changed = False

        for effect, duration in list(self._effects.items()):
            if duration is None:
                updated_effects[effect] = None  # Permanent effect / cheat
            elif duration - dt <= 0:
                stats_changed = True  # Effect expired!
                log(
                    f"{self._name} effect expired: {effect.name}",
                    "Entity",
                    LogType.INFO,
                )
            else:
                updated_effects[effect] = duration - dt

        self._effects = updated_effects
        if stats_changed:
            self._recalculate_stats()

    def update_fields(self, states: dict[str, Any]) -> None:
        """Update internal instance variables from a dictionary.

        Args:
            states: Key-value mapping of attribute names to values.
        """
        for key, value in states.items():
            setattr(self, key, value)

    def can_move(self, direction: Direction) -> bool:
        """Check whether the entity can traverse into an adjacent tile.

        Args:
            direction: Candidate direction to step.

        Returns:
            bool: True if destination tile is not a wall.
        """
        if direction is Direction.NONE:
            return False
        tile_x, tile_y = self.tile
        target_x = tile_x + direction.dx
        target_y = tile_y + direction.dy
        return not self._grid.is_wall(target_x, target_y)

    def _move(self, distance: float, direction: Direction) -> None:
        """Translate entity coordinates along a direction vector.

        Args:
            distance: Distance in tile units.
            direction: Direction vector to step along.
        """
        self._x += direction.dx * distance
        self._y += direction.dy * distance

    def _move_to_center_and_stop(self, distance: float) -> None:
        """Move towards the center of current tile before turning or stopping.

        Args:
            distance: Travel distance budget for this frame.
        """
        center_x, center_y = self.tile
        remaining = (
            (center_x - self._x) * self._cur_direction.dx
            + (center_y - self._y) * self._cur_direction.dy
        )
        if remaining <= 0 or distance >= remaining:
            self._x, self._y = float(center_x), float(center_y)
            if self.can_move(self._next_direction):
                self._move(
                    distance - max(0.0, remaining), self._next_direction
                )
                self._cur_direction = self._next_direction
                self._next_direction = Direction.NONE
            elif self.can_move(self._cur_direction):
                self._move(
                    distance - max(0.0, remaining), self._cur_direction
                )
            else:
                self._cur_direction = Direction.NONE
        else:
            self._move(distance, self._cur_direction)

    def _calc_movement(self, distance: float) -> None:
        """Calculate continuous translation across tiles taking turns.

        Args:
            distance: Movement distance budget in tile units.
        """
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

        can_turn = self.can_move(self._next_direction) and (
            self._cur_direction is not self._next_direction
        )
        blocked = (
            not self.can_move(self._cur_direction)
            and not self.can_move(self._next_direction)
        )

        if can_turn or blocked:
            self._move_to_center_and_stop(distance)
        elif self.can_move(self._cur_direction):
            self._move(distance, self._cur_direction)

    def __eq__(self, other: object) -> bool:
        """Check equality between two entities based on grid tile position.

        Args:
            other: Other object to compare against.

        Returns:
            bool: True if both entities share the same tile coordinates.
        """
        if not isinstance(other, Entity):
            return False
        return self.tile == other.tile

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update entity position and timers by delta time.

        Args:
            dt: Frame delta time in seconds.
        """
        pass


class PacMan(Entity):
    """Player-controlled Pac-Man character entity."""

    def __init__(
        self,
        spawn_x: float,
        spawn_y: float,
        speed: float,
        grid: MazeGrid,
        lives: int,
        name: str,
    ) -> None:
        """Initialize Pac-Man character with life count.

        Args:
            spawn_x: Spawn column.
            spawn_y: Spawn row.
            speed: Base travel speed in tiles per second.
            grid: Active maze grid reference.
            lives: Initial lives count.
            name: Entity name.
        """
        super().__init__(spawn_x, spawn_y, speed, grid, name)
        self._lives: int = lives

    @property
    def is_alive(self) -> bool:
        """Check whether Pac-Man has any remaining lives.

        Returns:
            bool: True if lives > 0.
        """
        return self._lives > 0

    @property
    def lives(self) -> int:
        """Return the current remaining lives count.

        Returns:
            int: Remaining lives.
        """
        return self._lives

    def respawn(self) -> None:
        """Reset Pac-Man position to spawn tile and clear all effects."""
        self._x, self._y = self._spawn_x, self._spawn_y
        self._cur_direction = Direction.NONE
        self._next_direction = Direction.NONE
        self.remove_all_effects()

    def can_eat_ghost(self, ghost: Ghost) -> bool:
        """Check whether Pac-Man can consume a vulnerable ghost.

        Args:
            ghost: Target ghost to evaluate.

        Returns:
            bool: True if colliding with a frightened ghost.
        """
        return ghost == self and ghost.is_frighten

    def lose_life(self) -> None:
        """Decrement lives count by one if currently alive."""
        if self.is_alive:
            self._lives -= 1
            log(
                f"Pac-Man lost a life! Remaining lives: {self._lives}",
                "PacMan",
                LogType.WARNING,
            )

    def add_life(self) -> None:
        """Increment lives count by one if currently alive."""
        if self.is_alive:
            self._lives += 1
            log(
                f"Pac-Man gained an extra life! Total lives: {self._lives}",
                "PacMan",
                LogType.INFO,
            )

    def toggle_invincibility(self) -> None:
        """Toggle invincibility cheat effect on or off."""
        if self.has_effect(EntityEffect.INVINCIBILITY):
            self.desactivate_effect(EntityEffect.INVINCIBILITY)
        else:
            self.activate_effect(EntityEffect.INVINCIBILITY)

    def increase_speed(self) -> None:
        """Toggle speed buff cheat effect on or off."""
        if self.has_effect(EntityEffect.SPEED_BUFF):
            self.desactivate_effect(EntityEffect.SPEED_BUFF)
        else:
            self.activate_effect(EntityEffect.SPEED_BUFF)

    def request_direction(self, direction: Direction) -> None:
        """Buffer a player directional input command.

        Args:
            direction: Requested input direction.
        """
        self._next_direction = direction

    def update(self, dt: float) -> None:
        """Update Pac-Man timers, apply buffs, and advance position.

        Args:
            dt: Frame elapsed time in seconds.
        """
        if not self.is_alive:
            return

        self.check_effect_duration(dt)

        distance = self._speed * dt
        self._calc_movement(distance)


class Ghost(Entity):
    """Enemy Ghost entity controlled by targeting strategy AI."""

    def __init__(
        self,
        spawn_x: float,
        spawn_y: float,
        speed: float,
        grid: MazeGrid,
        strategy: GhostStrategy,
        pacman: PacMan,
        name: str,
        blinky: Ghost | None = None,
    ) -> None:
        """Initialize ghost character with strategic AI and targets.

        Args:
            spawn_x: Spawn column.
            spawn_y: Spawn row.
            speed: Base travel speed in tiles per second.
            grid: Active maze grid reference.
            strategy: Targeting AI strategy instance.
            pacman: Target Pac-Man entity reference.
            name: Ghost name.
            blinky: Optional Blinky reference for flanking AI.
        """
        super().__init__(spawn_x, spawn_y, speed, grid, name)
        self._state: GhostState = GhostState.CHASE
        self._strategy: GhostStrategy = strategy
        self._pacman: PacMan = pacman
        self._blinky: Ghost | None = blinky
        self._target_tile: tuple[int, int] | None = None
        self._frightened_time: float = 0.0

    @property
    def is_frighten(self) -> bool:
        """Check whether the ghost is in frightened fleeing mode.

        Returns:
            bool: True if state is FRIGHTENED.
        """
        return self._state is GhostState.FRIGHTENED

    @property
    def is_frozen(self) -> bool:
        """Check whether the ghost is currently immobilized.

        Returns:
            bool: True if freeze effect is active or speed is 0.
        """
        return self.has_effect(EntityEffect.FREEZE) or self._speed == 0

    @property
    def state(self) -> GhostState:
        """Return the current behavioral state of the ghost.

        Returns:
            GhostState: Current state enum.
        """
        return self._state

    @property
    def target_tile(self) -> tuple[int, int] | None:
        """Return the current target tile coordinates.

        Returns:
            tuple[int, int] | None: Target (x, y) or None.
        """
        return self._target_tile

    @property
    def frightened_duration(self) -> float | None:
        """Return remaining seconds of frightened mode if active.

        Returns:
            float | None: Remaining duration or None.
        """
        return self._frightened_time if self.is_frighten else None

    def freeze(self) -> None:
        """Toggle freeze cheat effect on or off."""
        if self.is_frozen:
            self.desactivate_effect(EntityEffect.FREEZE)
        else:
            self.activate_effect(EntityEffect.FREEZE)

    def respawn(self) -> None:
        """Reset ghost position back to its corner and enter CHASE state."""
        self._x, self._y = self._spawn_x, self._spawn_y
        self._cur_direction = Direction.NONE
        self._next_direction = Direction.NONE
        self._state = GhostState.CHASE
        self.remove_all_effects()

    def _request_direction(self, blinky: Ghost | None = None) -> None:
        """Recalculate AI movement direction when reaching target tile.

        Args:
            blinky: Optional Blinky reference for flanking.
        """
        should_recalc = (
            self._next_direction is Direction.NONE
            or self._target_tile is None
            or self._target_tile == self.tile
            or self._grid.is_wall(*self._target_tile)
        )
        if should_recalc:
            self._next_direction = self._strategy.compute_next_move(
                self, self._pacman, self._grid, blinky
            )
            gx, gy = self.tile
            self._target_tile = (
                self._next_direction.dx + gx,
                self._next_direction.dy + gy,
            )

    def switch_state(self, new_state: GhostState) -> None:
        """Transition ghost into a new behavioral state.

        Args:
            new_state: New GhostState to transition into.
        """
        if self._state != new_state:
            self._state = new_state
            log(
                f"Ghost {self._name} transitioned to {new_state.name}",
                "Ghost",
                LogType.INFO,
            )

    def can_eat_pacman(self) -> bool:
        """Check whether the ghost can currently eliminate Pac-Man.

        Returns:
            bool: True if colliding with non-invincible Pac-Man.
        """
        return (
            self._pacman == self
            and not self._pacman.is_invincible
            and self.state in {GhostState.WANDER, GhostState.CHASE}
        )

    def active_frighten_mode(self, duration: float) -> None:
        """Engage frightened mode for the specified duration.

        Args:
            duration: Frightened duration in seconds.
        """
        if self.state not in {GhostState.DIED, GhostState.FRIGHTENED}:
            self.switch_state(GhostState.FRIGHTENED)
            self._frightened_time = duration

    def update(self, dt: float) -> None:
        """Update ghost timers, manage state transitions, and step position.

        Args:
            dt: Frame elapsed time in seconds.
        """
        self.check_effect_duration(dt)
        distance = self._speed * dt

        match self._state:
            case GhostState.FRIGHTENED:
                self._frightened_time -= dt
                if self._frightened_time <= 0:
                    self.switch_state(GhostState.CHASE)
            case (
                GhostState.DIED
            ) if self.tile == (int(self._spawn_x), int(self._spawn_y)):
                self.switch_state(GhostState.CHASE)
            case GhostState.DIED:
                distance = (self._base_speed * dt) * 2

        if (
            self._pacman.is_invincible
            and self._state not in {GhostState.WANDER, GhostState.FRIGHTENED}
        ):
            self.switch_state(GhostState.WANDER)

        self._request_direction(self._blinky)

        self._calc_movement(distance)
