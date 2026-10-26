import pygame
from maze_adapter import CellType
from enum import Enum
from consumables import (Consumable, PacGum, SuperPacGum,
                         ScoreEffect, FrightenGhostsEffect)



class CumsStyle(Enum):

    ROSE = "assets/maze/rose_cums.png"
    BLUE = "assets/maze/blue_cums.png"


class RenderConsumables:

    """Draws the animated pac-gums and super pac-gums on the maze cells."""

    def __init__(self, screen: pygame.Surface):

        self._screen: pygame.Surface = screen
        self._anm_fps: int = 10
        self._cums_key = ['rose', 'blue']
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

    @staticmethod
    def _place_consumables(maze) -> None:

        """Fill the maze corridors with pac-gums (super ones on the corners)."""

        Consumable.reset_counter()

        for row in maze.grid:
    
            for cell in row:
        
                if cell.cell_type is not CellType.CORRIDOR:
                    continue

                if not (1 <= cell.x < maze.width - 1
                        and 1 <= cell.y < maze.height - 1):
                    continue

                if cell.is_corner(maze.width, maze.height):
                    cell.add_consumable(
                        SuperPacGum([ScoreEffect(10), FrightenGhostsEffect(6)])) # i need to give those values from the config file not harcoded(10, 6)
                else:
                    cell.add_consumable(PacGum([ScoreEffect(10)]))# same thing for here read the above commente

    def prepare(self, maze_render, maze) -> None:
        """Load and scale the sheet so each frame is exactly one tile."""

        self._tile = maze_render.tile
        self._off_x = maze_render.off_x
        self._off_y = maze_render.off_y

        sheets: dict[str, pygame.Surface] = {}
        for path, key in zip(CumsStyle, self._cums_key):
            sheets[key] = pygame.image.load(path.value)
            self._sheet[key] = pygame.transform.scale(
                sheets[key], (self._frame * self._tile, 2 * self._tile)
            )
        
        self._place_consumables(maze)

    def _change_style(self) -> None:

        i = self._key_index
        names = self._cums_key
        self._curr_key = names[i % len(names)]
        self._key_index += 1


    def _draw_consumable(self, maze) -> None:
        
        t = self._tile
        frame = (pygame.time.get_ticks() * self._anm_fps // 1000) % self._frame

        for row in maze.grid:
            for cell in row:

                if not cell.consumes:
                    continue

                is_super = any(self._is_super(c) for c in cell.consumes)
                sheet_row = 1 if is_super else 0

                area = pygame.Rect(frame * t, sheet_row * t, t, t)
                self._screen.blit(
                    self._sheet[self._curr_key],
                    (self._off_x + cell.x * t, self._off_y + cell.y * t),
                    area,
                )

    def render(self, maze, change_style) -> None:

        if change_style:
            self._change_style()

        self._draw_consumable(maze)
