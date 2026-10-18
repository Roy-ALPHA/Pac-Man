from abc import ABC, abstractmethod
from .entities import GhostState, PRIORITY_DIRECTIONS, Direction
import random
import math

# f = open("logs.txt", "w")


class GhostStrategy(ABC):

    @staticmethod
    def closer_corridor(coor, maze):
        if not maze.is_wall(*coor):
            return coor

        x = coor[0]
        y = coor[1]
        x = max(1, min(coor[0], maze.width - 2))
        y = max(1, min(coor[1], maze.height - 2))
        coor = (x, y)

        queue = [coor]
        visited = {coor}

        while queue:

            x, y = queue.pop(0)

            for d in PRIORITY_DIRECTIONS:

                n_x, n_y = x+d.dx, y+d.dy
                if (n_x, n_y) in visited:
                    continue

                if not maze.is_wall(n_x, n_y):
                    return n_x, n_y

                queue.append((n_x, n_y))
                visited.add((n_x, n_y))

    @staticmethod
    def _go_to(from_coor, to_coor, opposite, maze, test=None):
        target = GhostStrategy.closer_corridor(to_coor, maze)

        if from_coor == target:
            return GhostStrategy._wander(from_coor, opposite, maze)

        def search(with_opposite):
            visited = {from_coor}
            queue = [from_coor]

            tracker = {
                from_coor: None
            }

            while queue:

                cur = queue.pop(0)

                if cur == target:
                    break

                for d in PRIORITY_DIRECTIONS:
                    if cur == from_coor and with_opposite and opposite is d:
                        continue

                    cur_x, cur_y = cur

                    n = d.dx + cur_x, d.dy + cur_y

                    if maze.is_wall(*n) or n in visited:
                        continue

                    queue.append(n)
                    visited.add(n)
                    tracker[n] = cur

            return tracker if len(tracker) > 1 else None

        tracker = search(True)
        if not tracker:
            tracker = search(False)
        # print(tracker if target not in tracker else "", file=f)

        if not tracker or target not in tracker:                                                                                                                                                                  
            return GhostStrategy._wander(from_coor, opposite, maze)

        path = []
        cur = target
        while cur != from_coor:
            path.append(cur)
            cur = tracker[cur]

        if not path:                                                                                                                                                                                              
            return GhostStrategy._wander(from_coor, opposite, maze)  

        path.reverse()

        # print(test, from_coor, target, path, file=f)
        for d in PRIORITY_DIRECTIONS:
            if (d.dx+from_coor[0], d.dy+from_coor[1]) == path[0]:
                return d

        return GhostStrategy._wander(from_coor, opposite, maze)

    @staticmethod
    def _wander(coor, opposite, maze):
        cur_x, cur_y = coor
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

        if not valid_moves:
            return ghost.cur_direction.opposite()

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
            case GhostState.DIED:
                return self._go_to(blinky.tile, blinky.spawn, blinky.cur_direction.opposite(), maze)
            case GhostState.WANDER:
                return self._wander(blinky.tile, blinky.cur_direction.opposite(), maze)


class PinkyStrategy(GhostStrategy):

    def _chase(self, pinky, pacman, maze):
        pacman_x, pacman_y = pacman.tile
        target = pacman.tile
        if pacman.cur_direction is not Direction.NONE:
            target = (pacman_x + 4 * pacman.cur_direction.dx, pacman_y + 4 * pacman.cur_direction.dy)
        return self._go_to(pinky.tile, target, pinky.cur_direction.opposite(), maze)

    def compute_next_move(self, pinky, pacman, maze, binky=None):
        match pinky.state:
            case GhostState.CHASE:
                return self._chase(pinky, pacman, maze)
            case GhostState.FRIGHTENED:
                return self._frighten(pinky, pacman, maze)
            case GhostState.DIED:
                return self._go_to(pinky.tile, pinky.spawn, pinky.cur_direction.opposite(), maze)
            case GhostState.WANDER:
                return self._wander(pinky.tile, pinky.cur_direction.opposite(), maze)


class InkyStrategy(GhostStrategy):

    def _chase(self, inky, pacman, maze, blinky):
        blinky_x, blinky_y = blinky.tile
        pacman_x, pacman_y = pacman.tile
        target = pacman.tile

        if pacman.cur_direction is not Direction.NONE:
            p_prime_x, p_prime_y = (pacman_x+2*pacman.cur_direction.dx, pacman_y+2*pacman.cur_direction.dy)
            vector_x, vector_y = (p_prime_x-blinky_x, p_prime_y-blinky_y)
            target = (vector_x*2+blinky_x, vector_y*2+blinky_y)

        if target != pacman.tile and target == inky.tile:
            return self._wander(inky.tile, inky.cur_direction.opposite(), maze)

        return self._go_to(inky.tile, target, inky.cur_direction.opposite(), maze)

    def compute_next_move(self, inky, pacman, maze, blinky=None):
        match inky.state:
            case GhostState.CHASE:
                return self._chase(inky, pacman, maze, blinky)
            case GhostState.FRIGHTENED:
                return self._frighten(inky, pacman, maze)
            case GhostState.DIED:
                return self._go_to(inky.tile, inky.spawn, inky.cur_direction.opposite(), maze)
            case GhostState.WANDER:
                return self._wander(inky.tile, inky.cur_direction.opposite(), maze)


class ClydeStrategy(GhostStrategy):

    def _decide(self, clyde, pacman, maze):

        dist = math.dist(clyde.tile, pacman.tile)
        target = clyde.spawn

        if dist > 8:
            target = pacman.tile

        if clyde.tile == clyde.spawn:
            return self._wander(clyde.tile, clyde.cur_direction.opposite(), maze)

        return self._go_to(clyde.tile, target, clyde.cur_direction.opposite(), maze)

    def compute_next_move(self, clyde, pacman, maze, blinky=None):
        match clyde.state:
            case GhostState.FRIGHTENED:
                return self._frighten(clyde, pacman, maze)
            case (GhostState.CHASE | GhostState.WANDER):
                return self._decide(clyde, pacman, maze)
            case GhostState.DIED:
                return self._go_to(clyde.tile, clyde.spawn, clyde.cur_direction.opposite(), maze)
