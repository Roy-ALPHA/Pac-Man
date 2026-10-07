from abc import ABC, abstractmethod
from .entities import Direction, GhostState, PRIORITY_DIRECTIONS
import random
import math


class GhostStrategy(ABC):

    @staticmethod
    def _go_to(from_coor, to_coor, opposite, maze):
        ghost_x, ghost_y = from_coor

        valid_moves = []

        for direction in PRIORITY_DIRECTIONS:
            if direction is opposite:
                continue

            next_x, next_y = (ghost_x + direction.dx, ghost_y + direction.dy)
            if maze.is_wall(next_x, next_y):
                continue

            dist = math.dist((next_x, next_y), to_coor)

            valid_moves.append((dist, direction))

        if not valid_moves:
            return opposite

        return min(valid_moves, key=lambda move: move[0])[1]

    @staticmethod
    def _wander(ghost, maze):
        cur_x, cur_y = ghost.tile
        opposite = ghost.cur_direction.opposite()
        valid_moves = [
            direction
            for direction in PRIORITY_DIRECTIONS
            if not maze.is_wall(cur_x+direction.dx, cur_y+direction.dy) and direction is not opposite
            ]

        if not valid_moves:
            return opposite

        return random.choice(valid_moves)

    @staticmethod
    def _frighten(ghost, pacman, maze):
        ghost_x, ghost_y = ghost.tile

        valid_moves = []

        for direction in PRIORITY_DIRECTIONS:

            next_x, next_y = (direction.dx + ghost_x, direction.dy + ghost_y)
            if maze.is_wall(next_x, next_y):
                continue

            dist = math.dist((next_x, next_y), pacman.tile)

            valid_moves.append((dist, direction))

        return max(valid_moves, key=lambda move: move[0])[1]

    @abstractmethod
    def compute_next_move(self, ghost, pacman, maze, binky=None):
        pass


class BlinkyStrategy(GhostStrategy):

    def _chase(self, blinky, pacman, maze):
        return self._go_to(blinky.tile, pacman.tile, blinky.cur_direction.opposite(), maze)

    def compute_next_move(self, blinky, pacman, maze, binky=None):
        match blinky.state:
            case GhostState.CHASE:
                return self._chase(blinky, pacman, maze)
            case GhostState.FRIGHTENED:
                return self._frighten(blinky, pacman, maze)
            case GhostState.WANDER:
                return self._wander(blinky, maze)
            case GhostState.DIED:
                return self._go_to(blinky.tile, blinky.spawn, blinky.cur_direction.opposite(), maze)


class PinkyStrategy(GhostStrategy):

    def _chase(self, pinky, pacman, maze):
        pacman_x, pacman_y = pacman.tile
        target_x, target_y = (pacman_x+4*pacman.cur_direction.dx, pacman_y+4*pacman.cur_direction.dy)
        return self._go_to(pinky.tile, (target_x, target_y), pinky.cur_direction.opposite(), maze)

    def compute_next_move(self, pinky, pacman, maze, binky=None):
        match pinky.state:
            case GhostState.CHASE:
                return self._chase(pinky, pacman, maze)
            case GhostState.FRIGHTENED:
                return self._frighten(pinky, pacman, maze)
            case GhostState.WANDER:
                return self._wander(pinky, maze)
            case GhostState.DIED:
                return self._go_to(pinky.tile, pinky.spawn, pinky.cur_direction.opposite(), maze)


class InkyStrategy(GhostStrategy):

    def _chase(self, inky, pacman, maze, blinky):
        blinky_x, blinky_y = blinky.tile
        pacman_x, pacman_y = pacman.tile

        p_prime_x, p_prime_y = (pacman_x+2*pacman.cur_direction.dx, pacman_y+2*pacman.cur_direction.dy)

        vector_x, vector_y = (p_prime_x-blinky_x, p_prime_y-blinky_y)

        target_x, target_y = (vector_x*2+blinky_x, vector_y*2+blinky_y)

        return self._go_to(inky.tile, (target_x, target_y), inky.cur_direction.opposite(), maze)

    def compute_next_move(self, inky, pacman, maze, blinky=None):
        match inky.state:
            case GhostState.CHASE:
                return self._chase(inky, pacman, maze, blinky)
            case GhostState.FRIGHTENED:
                return self._frighten(inky, pacman, maze)
            case GhostState.WANDER:
                return self._wander(inky, maze)
            case GhostState.DIED:
                return self._go_to(inky.tile, inky.spawn, inky.cur_direction.opposite(), maze)


class ClydeStrategy(GhostStrategy):

    def _decide(self, clyde, pacman, maze):

        dist = math.dist(clyde.tile, pacman.tile)

        if dist > 8:
            return self._go_to(clyde.tile, pacman.tile, clyde.cur_direction.opposite(), maze)
        else:
            return self._wander(clyde, maze)

    def compute_next_move(self, clyde, pacman, maze, blinky=None):
        match clyde.state:
            case GhostState.FRIGHTENED:
                return self._frighten(clyde, pacman, maze)
            case (GhostState.CHASE | GhostState.WANDER):
                return self._decide(clyde, pacman, maze)
            case GhostState.DIED:
                return self._go_to(clyde.tile, clyde.spawn, clyde.cur_direction.opposite(), maze)
