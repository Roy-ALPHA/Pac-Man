from enum import Enum
import pygame
from maze_adapter import CellType


class Styles(Enum):

    BLUE = 'maze/blue_wl.png'
    ORNG = 'maze/orng_wl.png'
    ROSE = 'maze/rose_wl.png'


class RenderMaze:

    """Handles everything related to drawing the maze walls."""

    def __init__(self, screen: pygame.Surface, width: int, height: int):

        self._screen: pygame.Surface = screen
        self._width: int = width
        self._height: int = height

        self._frame: int = 8
        self._anm_fps: int = 10
        self._tile: int = 0
        self._off_x: int = 0
        self._off_y: int = 0

        self._walls_names: list[str] = ['rose', 'blue']
        self._wall_index: int = 0
        self._loaded_images: dict[str, pygame.Surface] = {}
        self._curr_style: dict[str, pygame.Surface] = {}
        self._resized_walls: dict[str, pygame.Surface] = {}
        self._masks: dict[tuple[int, int], tuple[int, str]] = {}

    @property
    def tile(self) -> int:
        return self._tile

    @property
    def off_x(self) -> int:
        return self._off_x

    @property
    def off_y(self) -> int:
        return self._off_y

    @staticmethod
    def _same_wall_type(maze, x: int, y: int, cell_type) -> bool:
        if not (0 <= x < maze.width and 0 <= y < maze.height):
            return False
        return maze.grid[y][x].cell_type is cell_type

    @staticmethod
    def _load(style: Styles) -> pygame.Surface:
        path = f"assets/{style.value}"
        return pygame.image.load(path)

    @staticmethod
    def _get_wall_type(cell) -> str:
        return "logo" if cell.cell_type is CellType.LOGO else "wall"

    def _get_tile_size(self, maze) -> None:

        self._tile = min(self._width // maze.width,
                         self._height // maze.height)
        self._off_x = (self._width - self._tile * maze.width) // 2
        self._off_y = (self._height - self._tile * maze.height) // 2

    def _get_cell_mask(self, maze, cell) -> int:

        mask = 0
        neighbors = ((1, 0, -1), (2, 1, -1), (4, 1, 0), (8, 1, 1), (16, 0, 1),
                     (32, -1, 1), (64, -1, 0), (128, -1, -1),)

        for neighbor_value, dx, dy in neighbors:
            x = cell.x + dx
            y = cell.y + dy

            if self._same_wall_type(maze, x, y, cell.cell_type):
                mask += neighbor_value


        return mask

    def _prepare_styles(self, maze) -> None:

        self._get_tile_size(maze)
        t = self._tile
        frame = self._frame

        self._loaded_images = {
            "blue": self._load(Styles.BLUE),
            "rose": self._load(Styles.ROSE),
            "orng": self._load(Styles.ORNG)
        }

        for key, img in self._loaded_images.items():
            self._resized_walls[key] = pygame.transform.scale(
                img, (16 * t, 16 * t * frame)
            )

        self._curr_style['logo'] = self._resized_walls['orng']
        self._curr_style['wall'] = self._resized_walls['blue']

    def prepare(self, maze) -> None:

        self._prepare_styles(maze)
        self._masks.clear()

        for row in maze.grid:
            for cell in row:
                if cell.is_wall:
                    wall_type = self._get_wall_type(cell)
                    self._masks[(cell.x, cell.y)] = (
                        self._get_cell_mask(maze, cell), wall_type)

    def change_style(self) -> None:

        i = self._wall_index
        name = self._walls_names[i % len(self._walls_names)]
        self._curr_style['wall'] = self._resized_walls[name]
        self._wall_index += 1

    def _draw_walls(self) -> None:

        t = self._tile
        anm_time = pygame.time.get_ticks() * self._anm_fps // 1000

        for (x, y), (mask, wall_type) in self._masks.items():
            frame = (anm_time + x + y) % self._frame
            area = pygame.Rect((mask % 16) * t, (frame * 16 + mask // 16) * t,
                               t, t)
            self._screen.blit(self._curr_style[wall_type],
                              (self._off_x + x * t, self._off_y + y * t),
                              area)

    def render(self, change_style: bool) -> None:

        if change_style:
            self.change_style()

        self._draw_walls()
