import pygame
from enum import Enum
from ..consumables import SuperPacGum


class CumsStyle(Enum):

    ROSE = "src/assets/maze/rose_cums.png"
    BLUE = "src/assets/maze/blue_cums.png" 
    GREEN = "src/assets/maze/green_pellets.png"
    ORNG = "src/assets/maze/orng_cums.png"
    RED = "src/assets/maze/red_pellets.png"
    


class RenderConsumables:

    """Draws the animated pac-gums and super pac-gums on the maze cells"""

    def __init__(self, screen: pygame.Surface):

        self._screen: pygame.Surface = screen
        self._anm_fps: int = 10
        self._cums_key = ['rose', 'blue', 'green', 'orng', 'red']
        self._curr_key = self._cums_key[0]
        self._key_index = 1
        self._frame = 8
        self._sheet: dict[str, pygame.Surface] = {}
        self._tile: int = 0
        self._off_x: int = 0
        self._off_y: int = 0

    @staticmethod
    def _is_super(consumable) -> bool:
        return isinstance(consumable, SuperPacGum)

    def prepare(self, maze_render) -> None:
        """Load and scale the sheets so each frame is exactly one tile."""

        self._tile = maze_render.tile
        self._off_x = maze_render.off_x
        self._off_y = maze_render.off_y

        for style, key in zip(CumsStyle, self._cums_key):
            image = pygame.image.load(style.value).convert_alpha()
            self._sheet[key] = pygame.transform.scale(
                image, (self._frame * self._tile, 2 * self._tile)
            )

    def _change_style(self) -> None:

        i = self._key_index
        names = self._cums_key
        self._curr_key = names[i % len(names)]
        self._key_index += 1

    def _draw_consumable(self, maze) -> None:

        t = self._tile
        frame = (pygame.time.get_ticks() * self._anm_fps // 1000) % self._frame
        sheet = self._sheet[self._curr_key]

        for row in maze.grid:
            for cell in row:

                if not cell.consumes:
                    continue

                is_super = any(self._is_super(c) for c in cell.consumes)
                sheet_row = 1 if is_super else 0

                area = pygame.Rect(frame * t, sheet_row * t, t, t)
                self._screen.blit(
                    sheet,
                    (self._off_x + cell.x * t, self._off_y + cell.y * t),
                    area,
                )

    def render(self, maze, change_style) -> None:

        if change_style:
            self._change_style()

        self._draw_consumable(maze)
