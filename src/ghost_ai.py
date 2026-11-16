"""Ghost artificial intelligence algorithms and targeting strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
import math
import random
from typing import TYPE_CHECKING
from .entities import Direction, GhostState, PRIORITY_DIRECTIONS
from collections import deque

if TYPE_CHECKING:
    from .entities import Ghost, PacMan
    from .maze_adapter import MazeGrid


class GhostStrategy(ABC):
    """Abstract base class defining ghost movement and targeting behavior."""

    @staticmethod
    def _go_to(
        from_coor: tuple[int, int],
        to_coor: tuple[int, int],
        opposite: Direction,
        maze: MazeGrid,
    ) -> Direction:
        """Calculate the next direction along the shortest path toward target.

        Args:
            from_coor: Starting (x, y) coordinates.
            to_coor: Target (x, y) coordinates.
            opposite: Direction opposite to current movement (forbidden move).
            maze: The active maze grid.

        Returns:
            Direction: Chosen direction along the shortest path.
        """
        target = maze.find_nearest_corridor(to_coor)

        if from_coor == target:
            return GhostStrategy._wander(from_coor, opposite, maze)

        def search(skip_opposite: bool) -> Direction:
            """Find the next direction towards target using BFS.

            Args:
                skip_opposite: Whether reversing into opposite is skipped.

            Returns:
                Direction: Next direction towards target or Direction.NONE.
            """
            queue: deque[tuple[tuple[int, int], Direction]] = deque(
                [(from_coor, Direction.NONE)]
            )
            visited = {from_coor}

            while queue:
                cur, first_direction = queue.popleft()
                if cur == target:
                    return first_direction

                for d in PRIORITY_DIRECTIONS:
                    if (
                        skip_opposite
                        and cur == from_coor
                        and d is opposite
                    ):
                        continue

                    cx, cy = cur
                    next_coor = d.dx + cx, d.dy + cy
                    if maze.is_wall(*next_coor) or next_coor in visited:
                        continue

                    visited.add(next_coor)
                    next_direction = (
                        d if first_direction is Direction.NONE
                        else first_direction
                    )
                    queue.append((next_coor, next_direction))

            return Direction.NONE

        direction = search(skip_opposite=True)
        if direction is Direction.NONE:
            direction = search(skip_opposite=False)

        return (
            direction if direction is not Direction.NONE
            else GhostStrategy._wander(from_coor, opposite, maze)
        )

    @staticmethod
    def _wander(
        coor: tuple[int, int],
        opposite: Direction,
        maze: MazeGrid,
    ) -> Direction:
        """Select a random open non-reversing direction among adjacent tiles.

        Args:
            coor: Current (x, y) coordinates.
            opposite: Opposite direction to avoid.
            maze: The active maze grid.

        Returns:
            Direction: Randomly chosen valid direction.
        """
        cur_x, cur_y = coor
        valid_moves = [
            direction
            for direction in PRIORITY_DIRECTIONS
            if not maze.is_wall(cur_x + direction.dx, cur_y + direction.dy)
            and direction is not opposite
        ]

        if not valid_moves:
            return opposite

        return random.choice(valid_moves)

    @staticmethod
    def _frighten(
        ghost: Ghost,
        pacman: PacMan,
        maze: MazeGrid,
    ) -> Direction:
        """Select an escape direction maximizing distance and open exits.

        Args:
            ghost: The ghost entity in frightened mode.
            pacman: The Pac-Man player entity.
            maze: The active maze grid.

        Returns:
            Direction: Best fleeing direction.
        """
        ghost_x, ghost_y = ghost.tile
        candidates: list[tuple[float, int, Direction]] = []

        for direction in PRIORITY_DIRECTIONS:
            next_x = ghost_x + direction.dx
            next_y = ghost_y + direction.dy

            if maze.is_wall(next_x, next_y):
                continue

            if direction is ghost.cur_direction.opposite():
                continue

            distance = math.dist((next_x, next_y), pacman.tile)

            exits = 0
            for next_direction in PRIORITY_DIRECTIONS:
                x = next_x + next_direction.dx
                y = next_y + next_direction.dy

                if maze.is_wall(x, y):
                    continue
                if next_direction is direction.opposite():
                    continue

                exits += 1

            candidates.append((distance, exits, direction))

        safe_candidates = [c for c in candidates if c[1] > 0]

        if safe_candidates:
            candidates = safe_candidates

        if not candidates:
            return ghost.cur_direction.opposite()

        best_move: tuple[float, int, Direction] = max(
            candidates, key=lambda move: (move[0], move[1])
        )
        return best_move[2]

    @abstractmethod
    def compute_next_move(
        self,
        ghost: Ghost,
        pacman: PacMan,
        maze: MazeGrid,
        blinky: Ghost | None = None,
    ) -> Direction:
        """Compute the ghost's next movement direction based on its state.

        Args:
            ghost: The ghost entity making the move.
            pacman: The Pac-Man player entity.
            maze: The active maze grid.
            blinky: Optional reference to Blinky (used by Inky's algorithm).

        Returns:
            Direction: Chosen movement direction.
        """
        pass


class BlinkyStrategy(GhostStrategy):
    """Targeting strategy for Blinky (Red Ghost - Direct Chaser)."""

    def _chase(
        self,
        blinky: Ghost,
        pacman: PacMan,
        maze: MazeGrid,
    ) -> Direction:
        """Pursue Pac-Man directly towards his current tile.

        Args:
            blinky: The Blinky ghost entity.
            pacman: The Pac-Man player entity.
            maze: The active maze grid.

        Returns:
            Direction: Direction towards Pac-Man's tile.
        """
        return self._go_to(
            blinky.tile,
            pacman.tile,
            blinky.cur_direction.opposite(),
            maze,
        )

    def compute_next_move(
        self,
        ghost: Ghost,
        pacman: PacMan,
        maze: MazeGrid,
        blinky: Ghost | None = None,
    ) -> Direction:
        """Calculate Blinky's next move based on current ghost state.

        Args:
            ghost: The Blinky ghost entity.
            pacman: The Pac-Man player entity.
            maze: The active maze grid.
            blinky: Optional reference to Blinky (unused).

        Returns:
            Direction: Chosen direction.
        """
        match ghost.state:
            case GhostState.CHASE:
                return self._chase(ghost, pacman, maze)
            case GhostState.FRIGHTENED:
                return self._frighten(ghost, pacman, maze)
            case GhostState.DIED:
                return self._go_to(
                    ghost.tile,
                    ghost.spawn,
                    ghost.cur_direction.opposite(),
                    maze,
                )
            case GhostState.WANDER:
                return self._wander(
                    ghost.tile,
                    ghost.cur_direction.opposite(),
                    maze,
                )
        return Direction.NONE


class PinkyStrategy(GhostStrategy):
    """Targeting strategy for Pinky (Pink Ghost - Ambusher)."""

    def _chase(
        self,
        pinky: Ghost,
        pacman: PacMan,
        maze: MazeGrid,
    ) -> Direction:
        """Target 4 tiles ahead of Pac-Man's current facing direction.

        Args:
            pinky: The Pinky ghost entity.
            pacman: The Pac-Man player entity.
            maze: The active maze grid.

        Returns:
            Direction: Direction towards the ambush tile.
        """
        pacman_x, pacman_y = pacman.tile
        target = pacman.tile
        if pacman.cur_direction is not Direction.NONE:
            target = (
                pacman_x + 4 * pacman.cur_direction.dx,
                pacman_y + 4 * pacman.cur_direction.dy,
            )
        return self._go_to(
            pinky.tile,
            target,
            pinky.cur_direction.opposite(),
            maze,
        )

    def compute_next_move(
        self,
        pinky: Ghost,
        pacman: PacMan,
        maze: MazeGrid,
        blinky: Ghost | None = None,
    ) -> Direction:
        """Calculate Pinky's next move based on current ghost state.

        Args:
            pinky: The Pinky ghost entity.
            pacman: The Pac-Man player entity.
            maze: The active maze grid.
            blinky: Optional reference to Blinky (unused).

        Returns:
            Direction: Chosen direction.
        """
        match pinky.state:
            case GhostState.CHASE:
                return self._chase(pinky, pacman, maze)
            case GhostState.FRIGHTENED:
                return self._frighten(pinky, pacman, maze)
            case GhostState.DIED:
                return self._go_to(
                    pinky.tile,
                    pinky.spawn,
                    pinky.cur_direction.opposite(),
                    maze,
                )
            case GhostState.WANDER:
                return self._wander(
                    pinky.tile,
                    pinky.cur_direction.opposite(),
                    maze,
                )
        return Direction.NONE


class InkyStrategy(GhostStrategy):
    """Targeting strategy for Inky (Cyan Ghost - Flanker)."""

    def _chase(
        self,
        inky: Ghost,
        pacman: PacMan,
        maze: MazeGrid,
        blinky: Ghost,
    ) -> Direction:
        """Target tile mirrored across Blinky and 2 tiles ahead of Pac-Man.

        Args:
            inky: The Inky ghost entity.
            pacman: The Pac-Man player entity.
            maze: The active maze grid.
            blinky: The Blinky ghost entity used as pivot.

        Returns:
            Direction: Direction towards the flanking tile.
        """
        blinky_x, blinky_y = blinky.tile
        pacman_x, pacman_y = pacman.tile
        target = pacman.tile

        if pacman.cur_direction is not Direction.NONE:
            p_prime_x = pacman_x + 2 * pacman.cur_direction.dx
            p_prime_y = pacman_y + 2 * pacman.cur_direction.dy
            vector_x = p_prime_x - blinky_x
            vector_y = p_prime_y - blinky_y
            target = (vector_x * 2 + blinky_x, vector_y * 2 + blinky_y)

        if target != pacman.tile and target == inky.tile:
            return self._wander(
                inky.tile, inky.cur_direction.opposite(), maze
            )

        return self._go_to(
            inky.tile, target, inky.cur_direction.opposite(), maze
        )

    def compute_next_move(
        self,
        inky: Ghost,
        pacman: PacMan,
        maze: MazeGrid,
        blinky: Ghost | None = None,
    ) -> Direction:
        """Calculate Inky's next move based on current ghost state.

        Args:
            inky: The Inky ghost entity.
            pacman: The Pac-Man player entity.
            maze: The active maze grid.
            blinky: Optional reference to Blinky.

        Returns:
            Direction: Chosen direction.
        """
        match inky.state:
            case GhostState.CHASE:
                if blinky is not None:
                    return self._chase(inky, pacman, maze, blinky)
                return self._wander(
                    inky.tile, inky.cur_direction.opposite(), maze
                )
            case GhostState.FRIGHTENED:
                return self._frighten(inky, pacman, maze)
            case GhostState.DIED:
                return self._go_to(
                    inky.tile,
                    inky.spawn,
                    inky.cur_direction.opposite(),
                    maze,
                )
            case GhostState.WANDER:
                return self._wander(
                    inky.tile,
                    inky.cur_direction.opposite(),
                    maze,
                )
        return Direction.NONE


class ClydeStrategy(GhostStrategy):
    """Targeting strategy for Clyde (Orange Ghost - Scatterer)."""

    def _decide(
        self,
        clyde: Ghost,
        pacman: PacMan,
        maze: MazeGrid,
    ) -> Direction:
        """Chase Pac-Man when far (> 8 tiles), or retreat to home corner.

        Args:
            clyde: The Clyde ghost entity.
            pacman: The Pac-Man player entity.
            maze: The active maze grid.

        Returns:
            Direction: Chosen direction.
        """
        dist = math.dist(clyde.tile, pacman.tile)
        target = clyde.spawn

        if dist > 8:
            target = pacman.tile
        elif clyde.tile == clyde.spawn or dist < 8:
            return self._wander(
                clyde.tile, clyde.cur_direction.opposite(), maze
            )

        return self._go_to(
            clyde.tile, target, clyde.cur_direction.opposite(), maze
        )

    def compute_next_move(
        self,
        clyde: Ghost,
        pacman: PacMan,
        maze: MazeGrid,
        blinky: Ghost | None = None,
    ) -> Direction:
        """Calculate Clyde's next move based on current ghost state.

        Args:
            clyde: The Clyde ghost entity.
            pacman: The Pac-Man player entity.
            maze: The active maze grid.
            blinky: Optional reference to Blinky (unused).

        Returns:
            Direction: Chosen direction.
        """
        match clyde.state:
            case GhostState.FRIGHTENED:
                return self._frighten(clyde, pacman, maze)
            case (GhostState.CHASE | GhostState.WANDER):
                return self._decide(clyde, pacman, maze)
            case GhostState.DIED:
                return self._go_to(
                    clyde.tile,
                    clyde.spawn,
                    clyde.cur_direction.opposite(),
                    maze,
                )
        return Direction.NONE
