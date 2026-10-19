from mazegenerator import MazeGenerator
from dataclasses import dataclass, field
from enum import Enum, auto
from consumables import Consumable
import io
from contextlib import redirect_stdout
import warnings
from errors import MazeAdapterWarning


class CellType(Enum):
    WALL = auto()
    CORRIDOR = auto()
    LOGO = auto()


@dataclass(slots=True)
class Cell:
    x: int
    y: int
    cell_type: CellType = CellType.WALL
    consumes: Consumable = field(default_factory=list)

    def is_corner(self, width, height):
        corners = (
            (1, 1),
            (width - 2, 1),
            (1, height - 2),
            (width - 2, height - 2),
        )

        return (self.x, self.y) in corners

    @property
    def is_wall(self):
        return self.cell_type is CellType.WALL

    def remove_consumables(self):
        self.consumes = []

    def add_consumable(self, consumable):
        self.consumes.append(consumable)


@dataclass(slots=True)
class MazeGrid:
    width: int
    height: int
    grid: list[list[Cell]]
    maze_entry: tuple[int, int]
    maze_exit: tuple[int, int]

    def get_cell(self, x: int, y: int):
        return self.grid[y][x]

    def is_wall(self, x: int, y: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x].is_wall
        return True


class MazeAdapter:

    _width = None
    _height = None

    def __init__(self):
        self._generator_cls = MazeGenerator

    @classmethod
    def set_maze_size(cls, size):
        cls._width, cls._height = size

    def generate_maze(self, level) -> MazeGrid:
        maze_width, maze_height = MazeAdapter._width, MazeAdapter._height

        tmp_stdout = io.StringIO()

        try:
            with redirect_stdout(tmp_stdout):
                entry_cell = (0, maze_height // 2)
                exit_cell = (maze_width - 1, maze_height // 2)
                original_maze = self._generator_cls(
                    size=(maze_width, maze_height),
                    seed=level.seed, entry_cell=entry_cell,
                    exit_cell=exit_cell
                    )

            warn_msgs = tmp_stdout.getvalue()

            if warn_msgs:
                self._warn(warn_msgs)

            extended_maze = MazeAdapter._extract_corridors(original_maze.maze)

            ext_x = 2 * maze_width + 1
            ext_y = 2 * maze_height + 1

            return MazeGrid(
                width=ext_x,
                height=ext_y,
                grid=extended_maze,
                maze_entry=(0, ext_y // 2),
                maze_exit=(ext_x - 1, ext_y // 2)
            )
        except Exception as e:
            warnings.warn(
                f"Maze generation failure: {e}",
                category=MazeAdapterWarning,
                stacklevel=2
                )
            raise

    @staticmethod
    def _extract_corridors(bitmask_maze):
        raw_w = len(bitmask_maze[0])
        raw_h = len(bitmask_maze)

        extended_w = 2 * raw_w + 1  # 2h + 1
        extended_h = 2 * raw_h + 1  # 2w + 1

        extended_maze = [
            [Cell(x=x, y=y, cell_type=CellType.WALL) for x in range(extended_w)]
            for y in range(extended_h)
        ]

        for y in range(len(bitmask_maze)):
            for x in range(len(bitmask_maze[0])):

                val = bitmask_maze[y][x]

                if val == 15:
                    extended_maze[2 * y + 1][2 * x + 1].cell_type = CellType.LOGO
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

        return extended_maze

    @staticmethod
    def _warn(warn_msgs):
        for warn_msg in warn_msgs.splitlines():
            msg = warn_msg.strip()
            warnings.warn(
                msg,
                category=MazeAdapterWarning,
                stacklevel=3
            )
