"""Maze adapter and grid model interfacing with the maze generator."""

from contextlib import redirect_stdout
from dataclasses import dataclass, field
from enum import Enum, auto
import io
from typing import Any
from mazegenerator import MazeGenerator
from .consumables import Consumable
from .entities import PRIORITY_DIRECTIONS
from .logger import log, LogType
from collections import deque


class CellType(Enum):
    """Semantic type of a maze cell."""

    WALL = auto()
    CORRIDOR = auto()
    LOGO = auto()


@dataclass(slots=True)
class Cell:
    """Represents an individual coordinate cell within the maze grid."""

    x: int
    y: int
    cell_type: CellType = CellType.WALL
    consumes: list[Consumable] = field(default_factory=list)

    def is_corner(self, width: int, height: int) -> bool:
        """Check whether this cell is located at one of the four grid corners.

        Args:
            width: Total width of the grid.
            height: Total height of the grid.

        Returns:
            bool: True if the cell is a corner, False otherwise.
        """
        corners = (
            (1, 1),
            (width - 2, 1),
            (1, height - 2),
            (width - 2, height - 2),
        )

        return (self.x, self.y) in corners

    @property
    def is_wall(self) -> bool:
        """Check whether this cell is an impassable wall or logo barrier.

        Returns:
            bool: True if this cell cannot be traversed.
        """
        return self.cell_type in (CellType.WALL, CellType.LOGO)

    def remove_consumables(self) -> None:
        """Clear all consumables located on this cell."""
        self.consumes = []

    def add_consumable(self, consumable: Consumable) -> None:
        """Place a consumable item on this cell.

        Args:
            consumable: The consumable item to add.
        """
        self.consumes.append(consumable)


@dataclass(slots=True)
class MazeGrid:
    """2D grid structure containing cells, entry, and exit points."""

    width: int
    height: int
    grid: list[list[Cell]]
    maze_entry: tuple[int, int]
    maze_exit: tuple[int, int]

    def get_cell(self, x: int, y: int) -> Cell:
        """Retrieve the cell object at coordinates (x, y).

        Args:
            x: Column index.
            y: Row index.

        Returns:
            Cell: The cell instance at the given coordinates.
        """
        return self.grid[y][x]

    def is_wall(self, x: int, y: int) -> bool:
        """Check whether coordinates point to a wall or are out of bounds.

        Args:
            x: Column index.
            y: Row index.

        Returns:
            bool: True if the coordinate is impassable or out of bounds.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x].is_wall
        return True

    def find_nearest_corridor(self, coor: tuple[int, int]) -> tuple[int, int]:
        """Find the nearest walkable corridor cell using breadth-first search.

        Args:
            coor: (x, y) coordinates of the search center.

        Returns:
            tuple[int, int]: (x, y) coordinates of the nearest open corridor.
        """
        if not self.is_wall(*coor):
            return coor

        x = max(1, min(coor[0], self.width - 2))
        y = max(1, min(coor[1], self.height - 2))
        coor = (x, y)

        queue = deque([coor])
        visited = {coor}

        while queue:
            cx, cy = queue.popleft()

            for d in PRIORITY_DIRECTIONS:
                n_x, n_y = cx + d.dx, cy + d.dy
                if (n_x, n_y) in visited:
                    continue

                if not self.is_wall(n_x, n_y):
                    return n_x, n_y

                queue.append((n_x, n_y))
                visited.add((n_x, n_y))

        return coor


class MazeAdapter:
    """Adapter bridging the external maze generator and the game grid."""

    _width: int = 15
    _height: int = 15

    def __init__(self) -> None:
        """Initialize the maze adapter."""
        self._generator_cls = MazeGenerator

    @classmethod
    def set_maze_size(cls, size: tuple[int, int]) -> None:
        """Set the base dimensions for maze generation.

        Args:
            size: (width, height) tuple of base dimensions.
        """
        cls._width, cls._height = size

    def generate_maze(self, level: Any) -> MazeGrid:
        """Generate an expanded, playable maze grid for the specified level.

        Args:
            level: Level configuration containing the generator seed.

        Returns:
            MazeGrid: The constructed maze grid.

        Raises:
            Exception: If maze generation fails.
        """
        maze_width, maze_height = MazeAdapter._width, MazeAdapter._height

        tmp_stdout = io.StringIO()

        try:
            with redirect_stdout(tmp_stdout):
                entry_cell = (0, maze_height // 2)
                exit_cell = (maze_width - 1, maze_height // 2)
                original_maze = self._generator_cls(
                    size=(maze_width, maze_height),
                    seed=level.seed, entry_cell=entry_cell,
                    exit_cell=exit_cell,
                )

            warn_msgs = tmp_stdout.getvalue()

            if warn_msgs:
                self._warn(warn_msgs)

            extended_maze = MazeAdapter._extract_corridors(
                original_maze.maze
            )

            ext_x = 2 * maze_width + 1
            ext_y = 2 * maze_height + 1

            return MazeGrid(
                width=ext_x,
                height=ext_y,
                grid=extended_maze,
                maze_entry=(0, ext_y // 2),
                maze_exit=(ext_x - 1, ext_y // 2),
            )
        except Exception as e:
            log(
                f"Maze generation failure: {e}",
                "MazeAdapter",
                LogType.WARNING,
            )
            raise

    @staticmethod
    def _extract_corridors(
        bitmask_maze: list[list[int]],
    ) -> list[list[Cell]]:
        """Expand bitmask maze cells into a traversable 2D grid.

        Args:
            bitmask_maze: 2D bitmask array produced by the maze generator.

        Returns:
            list[list[Cell]]: Expanded 2D grid containing corridors and walls.
        """
        raw_w = len(bitmask_maze[0])
        raw_h = len(bitmask_maze)

        extended_w = 2 * raw_w + 1  # 2h + 1
        extended_h = 2 * raw_h + 1  # 2w + 1

        extended_maze = [
            [
                Cell(x=x, y=y, cell_type=CellType.WALL)
                for x in range(extended_w)
            ]
            for y in range(extended_h)
        ]

        for y in range(len(bitmask_maze)):
            for x in range(len(bitmask_maze[0])):

                val = bitmask_maze[y][x]

                if val == 15:
                    extended_maze[2 * y + 1][2 * x + 1].cell_type = (
                        CellType.LOGO
                    )
                    continue

                cx, cy = 2 * x + 1, 2 * y + 1

                extended_maze[cy][cx].cell_type = CellType.CORRIDOR

                if not bool(val & 1):  # true if the north is not wall
                    extended_maze[cy - 1][cx].cell_type = CellType.CORRIDOR
                if not bool(val & 2):  # true if the east is not wall
                    extended_maze[cy][cx + 1].cell_type = CellType.CORRIDOR
                if not bool(val & 4):  # true if the south is not wall
                    extended_maze[cy + 1][cx].cell_type = CellType.CORRIDOR
                if not bool(val & 8):  # true if the west is not wall
                    extended_maze[cy][cx - 1].cell_type = CellType.CORRIDOR

        for y in range(raw_h):
            for x in range(raw_w):
                if bitmask_maze[y][x] != 15:
                    continue
                cx, cy = 2 * x + 1, 2 * y + 1
                if x + 1 < raw_w and bitmask_maze[y][x + 1] == 15:
                    extended_maze[cy][cx + 1].cell_type = CellType.LOGO
                if y + 1 < raw_h and bitmask_maze[y + 1][x] == 15:
                    extended_maze[cy + 1][cx].cell_type = CellType.LOGO

        return extended_maze

    @staticmethod
    def _warn(warn_msgs: str) -> None:
        """Forward generator stdout messages to the logger.

        Args:
            warn_msgs: Multiline string containing stdout output.
        """
        for warn_msg in warn_msgs.splitlines():
            msg = warn_msg.strip()
            log(msg, "MazeAdapter", LogType.WARNING)
