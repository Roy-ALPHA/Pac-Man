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

        # if from_coor == to_coor:
        #     return Direction.NONE

        # to_coor = GhostStrategy.closer_corridor(to_coor, maze)

        # queue = [from_coor]
        # visited = {from_coor}

        # tracker = {
        #     from_coor: None
        # }

        # filtered_d = [d for d in PRIORITY_DIRECTIONS if d is not opposite]

        # if not filtered_d:
        #     filtered_d.append(opposite)

        # while queue:

        #     cur_x, cur_y = queue.pop(0)
        #     # if (cur_x, cur_y) == to_coor:
        #     #     break
        #     directions = filtered_d if (cur_x, cur_y) == from_coor else PRIORITY_DIRECTIONS
        #     for d in directions:

        #         n_x, n_y = cur_x+d.dx, cur_y+d.dy
        #         if maze.is_wall(n_x, n_y) or (n_x, n_y) in visited:
        #             continue

        #         tracker[(n_x, n_y)] = (cur_x, cur_y)

        #         queue.append((n_x, n_y))
        #         visited.add((n_x, n_y))

        # print("start->", from_coor, "target->", to_coor, file=f); print(True if to_coor in tracker else False, maze.is_wall(*to_coor), test, file=f)
        # path = []
        # cur_coor = to_coor

        # while cur_coor != from_coor:
        #     path.append(cur_coor)
        #     cur_coor = tracker[cur_coor]

        # path.reverse()

        # n_coor = path.pop(0)

        # for d in PRIORITY_DIRECTIONS:
        #     if (d.dx+from_coor[0], d.dy+from_coor[1]) == n_coor:
        #         return d
        # return Direction.NONE
        from collections import deque

        to_coor = GhostStrategy.closer_corridor(to_coor, maze)

        start = tuple(from_coor)
        target = tuple(to_coor)

        if start == target:
            return Direction.NONE

        def search(allow_opposite):
            queue = deque([start])
            visited = {start}
            first_direction = {start: None}

            while queue:
                x, y = queue.popleft()
                current = (x, y)

                if current == target:
                    return first_direction[current]

                for direction in PRIORITY_DIRECTIONS:
                    if (
                        current == start
                        and not allow_opposite
                        and direction is opposite
                    ):
                        continue

                    neighbor = (
                        x + direction.dx,
                        y + direction.dy,
                    )

                    if maze.is_wall(*neighbor) or neighbor in visited:
                        continue

                    visited.add(neighbor)

                    if current == start:
                        first_direction[neighbor] = direction
                    else:
                        first_direction[neighbor] = first_direction[current]

                    queue.append(neighbor)

            return None

        direction = search(allow_opposite=False)

        if direction is None:
            direction = search(allow_opposite=True)

        return direction

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
        return self._go_to(blinky.tile, pacman.tile, blinky.cur_direction.opposite(), maze, "blinky")

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
        return self._go_to(pinky.tile, (target_x, target_y), pinky.cur_direction.opposite(), maze, "pinky")

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

        return self._go_to(inky.tile, (target_x, target_y), inky.cur_direction.opposite(), maze, "inky")

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
            return self._go_to(clyde.tile, pacman.tile, clyde.cur_direction.opposite(), maze, "clyde")
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
