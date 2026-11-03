from abc import ABC, abstractmethod
from enum import Enum, auto


class GhostState(Enum):
	CHASE = auto()
	FRIGHTENED = auto()
	WANDER = auto()
	DIED = auto()

class EntityEffect(Enum):
	SPEED_BUFF = auto()
	SPEED_DEBUFF = auto()
	INVINCIBILITY = auto()
	FREEZE = auto()


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
	def __init__(self, spawn_x, spawn_y, speed, grid, name):
		self._spawn_x = spawn_x
		self._spawn_y = spawn_y
		self._x = spawn_x
		self._y = spawn_y
		self._speed = speed
		self._grid = grid
		self._cur_direction = Direction.NONE
		self._next_direction = Direction.NONE
		self._base_speed = self._speed
		self._name = name
		self._invincible = False
		self._effects = dict()

	@property
	def name(self):
		return self._name

	@property
	def cur_direction(self):
		return self._cur_direction

	@property
	def next_direction(self):
		return self._next_direction

	@property
	def is_invincible(self):
		return self._invincible

	@property
	def speed(self):
		return self._speed

	@property
	def x(self):
		return self._x

	@property
	def y(self):
		return self._y

	@property
	def tile(self):
		return (round(self._x), round(self._y))

	@property
	def spawn(self):
		return self._spawn_x, self._spawn_y

	@abstractmethod
	def respawn(self):
		pass

	def _recalculate_stats(self):
		"""Recalculate dynamic stats from all currently active effects."""
		# 1. Handle Invincibility
		self._invincible = (EntityEffect.INVINCIBILITY in self._effects)

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
		return effect in self._effects

	def activate_effect(self, effect: EntityEffect, duration=None):
		"""Activate an effect with an optional timer."""
		self._effects[effect] = duration
		self._recalculate_stats()

	def desactivate_effect(self, effect: EntityEffect):
		"""Remove an effect and restore stats cleanly."""
		self._effects.pop(effect, None)
		self._recalculate_stats()

	def remove_all_effects(self):
		self._effects.clear()
		self._recalculate_stats() 

	def get_effects_state(self) -> dict:
		"""Serialize active effects to a JSON-compatible dict."""
		return {effect.name: duration for effect, duration in self._effects.items()}

	def set_effects_state(self, effects_data: dict) -> None:
		"""Deserialize and re-apply effects from a dictionary."""
		self._effects.clear()
		for effect_name, duration in effects_data.items():
			if effect_name in EntityEffect.__members__:
				self._effects[EntityEffect[effect_name]] = duration
		self._recalculate_stats() 

	def check_effect_duration(self, dt):
		if not self._effects: 
			return

		updated_effects = dict()
		stats_changed = False

		for effect, duration in list(self._effects.items()): 
			if duration is None: 
				updated_effects[effect] = None  # Permanent effect / cheat 
			elif duration - dt <= 0:
				stats_changed = True            # Effect expired!
			else:
				updated_effects[effect] = duration - dt 

		self._effects = updated_effects
		if stats_changed:
			self._recalculate_stats()

	def update_fields(self, states):
		for key, value in states.items():
			setattr(self, key, value)

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
			if self.can_move(self._next_direction):
				self._move(distance - max(0.0, remaining), self._next_direction)
				self._cur_direction = self._next_direction
				self._next_direction = Direction.NONE
			elif self.can_move(self._cur_direction):
				self._move(distance - max(0.0, remaining), self._cur_direction)
			else:
				self._cur_direction = Direction.NONE
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

		if self.can_move(self._next_direction) and self._cur_direction is not self._next_direction:
			self._move_to_center_and_stop(distance)
		elif self.can_move(self._cur_direction):
			self._move(distance, self._cur_direction)

	def __eq__(self, other):
		return self.tile == other.tile

	@abstractmethod
	def update(self, dt):
		pass


class PacMan(Entity):
	def __init__(self, spawn_x, spawn_y, speed, grid, lives, name):
		super().__init__(spawn_x, spawn_y, speed, grid, name)
		self._lives = lives

	@property
	def is_alive(self):
		return self._lives > 0

	@property
	def lives(self):
		return self._lives

	def respawn(self):
		self._x, self._y = self._spawn_x, self._spawn_y
		self._cur_direction = Direction.NONE
		self._next_direction = Direction.NONE

	def can_eat_ghost(self, ghost):
		return ghost == self and ghost.is_frighten

	def lose_life(self):
		if self.is_alive:
			self._lives -= 1

	def add_life(self):
		if self.is_alive:
			self._lives += 1

	def toggle_invincibility(self):
		if self.has_effect(EntityEffect.INVINCIBILITY):
			self.desactivate_effect(EntityEffect.INVINCIBILITY)
		else:
			self.activate_effect(EntityEffect.INVINCIBILITY)

	def increase_speed(self):
		if self.has_effect(EntityEffect.SPEED_BUFF):
			self.desactivate_effect(EntityEffect.SPEED_BUFF)
		else:
			self.activate_effect(EntityEffect.SPEED_BUFF)

	def request_direction(self, direction):
		self._next_direction = direction


	def update(self, dt):
		if not self.is_alive:
			return

		self.check_effect_duration(dt)

		distance = self._speed * dt
		self._calc_movement(distance)


class Ghost(Entity):
	def __init__(self, spawn_x, spawn_y, speed, grid, strategy, pacman, name, blinky=None):
		super().__init__(spawn_x, spawn_y, speed, grid, name)
		self._state = GhostState.CHASE
		self._strategy = strategy
		self._pacman = pacman
		self._blinky = blinky
		self._target_tile = None

	@property
	def is_frighten(self):
		return self._state is GhostState.FRIGHTENED

	@property
	def is_frozen(self):
		return self.has_effect(EntityEffect.FREEZE) or self._speed == 0

	@property
	def state(self):
		return self._state

	@property
	def target_tile(self):
		return self._target_tile

	@property
	def frightened_duration(self):
		return self._frightened_time if self.is_frighten else None

	def freeze(self):
		if self.is_frozen:
			self.desactivate_effect(EntityEffect.FREEZE)
		else:
			self.activate_effect(EntityEffect.FREEZE)

	def respawn(self):
		self._x, self._y = self._spawn_x, self._spawn_y
		self._cur_direction = Direction.NONE
		self._next_direction = Direction.NONE
		self._state = GhostState.CHASE
		if self.is_frozen:
			self.freeze()

	def _request_direction(self, blinky=None):
		if self._next_direction is Direction.NONE or self._target_tile is None or self._target_tile == self.tile or self._grid.is_wall(*self._target_tile):
			self._next_direction = self._strategy.compute_next_move(
				self, self._pacman, self._grid, blinky
			)
			gx, gy = self.tile
			self._target_tile = self._next_direction.dx+gx, self._next_direction.dy+gy

	def switch_state(self, new_state):
		self._state = new_state

	def can_eat_pacman(self):
		return self._pacman == self and not self._pacman.is_invincible and self.state in {GhostState.WANDER, GhostState.CHASE}

	def active_frighten_mode(self, duration):
		if self.state not in {GhostState.DIED, GhostState.FRIGHTENED}:
			self.switch_state(GhostState.FRIGHTENED)
			self._frightened_time = duration

	def update(self, dt):
		self.check_effect_duration(dt)
		distance = self._speed * dt


		match self._state:
			case GhostState.FRIGHTENED:
				self._frightened_time -= dt
				if self._frightened_time <= 0:
					self.switch_state(GhostState.CHASE)
			case GhostState.DIED if self.tile == (self._spawn_x, self._spawn_y):
				self.switch_state(GhostState.CHASE)
			case GhostState.DIED:
				distance = (self._base_speed * dt) * 2


		if self._pacman.is_invincible and self._state not in {GhostState.WANDER, GhostState.FRIGHTENED}:
			self.switch_state(GhostState.WANDER)

		self._request_direction(self._blinky)

		self._calc_movement(distance)
