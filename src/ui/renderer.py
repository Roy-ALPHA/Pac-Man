from typing import Any
from maze_adapter import CellType
from enum import Enum
import pygame


class Styles(Enum):

    BLUE = 'maze/blue_wl.png'
    ORNG = 'maze/orng_wl.png'


class Renderer:

    def __init__(self, width: int, height: int):

        pygame.init()
        self.frame = 8
        self.wave = True
        self.anm_fps = 10
        self._screen = pygame.display.set_mode((width, height))
        self._width = width
        self._height = height
        self._tile = 0
        self._off_x = 0
        self._off_y = 0
        pygame.display.set_caption("Pac-Man")

        self._wall_imgs = {
            "wall": self._load(Styles.BLUE),
            "logo": self._load(Styles.ORNG),
        }
        self._wall_imgs_resized: dict[str, pygame.Surface] = {}
        self._masks: dict[tuple[int, int], tuple[int, str]] = {}

    def _get_tile_size(self, maze) -> None:

        self._tile = min(self._width // maze.width,
                         self._height // maze.height)
        self._off_x = (self._width - self._tile * maze.width) // 2
        self._off_y = (self._height - self._tile * maze.height) // 2

    @staticmethod
    def _same_kind(maze, x: int, y: int, cell_type) -> bool:
        if not (0 <= x < maze.width and 0 <= y < maze.height):
            return False
        return maze.grid[y][x].cell_type is cell_type

    @staticmethod
    def _load(style: Styles) -> pygame.Surface:
        path = f"assets/{style.value}"
        return pygame.image.load(path)

    def _wall_mask(self, maze, cell):
        mask = 0
        neighbors = ((1, 0, -1), (2, 1, -1), (4, 1, 0), (8, 1, 1), (16, 0, 1),
                      (32, -1, 1), (64, -1, 0), (128, -1, -1),)

        for bit, dx, dy in neighbors:
            x = cell.x + dx
            y = cell.y + dy

            if self._same_kind(maze, x, y, cell.cell_type):
                mask += bit

        return mask

    def _prepare_maze(self, maze) -> None:

        self._get_tile_size(maze)
        t = self._tile
        self._masks = {}

        for key, img in self._wall_imgs.items():
            self._wall_imgs_resized[key] = pygame.transform.scale(
                img, (16 * t, 16 * self.frame * t))

        for row in maze.grid:
            for cell in row:
                if cell.is_wall:
                    cell_tp = cell.cell_type
                    wall_type = "logo" if cell_tp is CellType.LOGO else "wall"
                    self._masks[(cell.x, cell.y)
                                ] = (self._wall_mask(maze, cell), wall_type)

    def render_maze(self, maze, change_maze: bool = False) -> None:

        if change_maze:
            self._prepare_maze(maze)
            change_maze = False

        t = self._tile
        animation_time = pygame.time.get_ticks() * self.anm_fps // 1000

        for (x, y), (mask, kind) in self._masks.items():
            frame = (animation_time + (x + y if self.wave else 0)) % self.frame
            src = pygame.Rect((mask % 16) * t,
                              (frame * 16 + mask // 16) * t,
                              t, t)
            self.blit_window(self._wall_imgs_resized[kind],
                             (self._off_x + x * t, self._off_y + y * t), src)

    def render_entities(self, player, ghosts) -> None:
        pass

    def render_hub(self, score: int, lives: int, level: int,
                   time_left: float) -> None:
        pass

    def render_menu(self, menu) -> None:
        pass

    def clear(self) -> None:
        self._screen.fill((0, 0, 0))

    def update_display(self) -> None:
        pygame.display.flip()

    def draw_door(self, x: int, door_w: int) -> None:
        pygame.draw.rect(self._screen, 'yellow',
                         (x, 0, door_w, self._height))

    def blit_window(self, to_draw: Any, coord: tuple[int, int],
                    area=None) -> None:
        self._screen.blit(to_draw, coord, area)
