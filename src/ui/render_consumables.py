from ..consumables import SuperPacGum
from ..maze_adapter import MazeGrid
from src.ui.render_maze import RenderMaze
import pygame


class RenderConsumables:

    """
    Class that is responsible about rendering the pac-cums
    and superpac-cums
    """
    FILES = ['rose_cums.png', 'blue_cums.png', 'green_pellets.png',
             'orng_cums.png', 'red_pellets.png']

    def __init__(self, screen: pygame.Surface):
        """
        Method that initialize all the attribute of the
        instance created from this class
        """
        self._screen = screen
        self._frames = 8
        self._fps = 10
        self._tile = 0
        self._off_x = 0
        self._off_y = 0
        self._sheets: list[pygame.Surface] = []
        self._style = 0

    def prepare(self, maze_render: RenderMaze) -> None:
        """
        Method that prepare the envirment for the consumable
        to be rendered
        """
        self._tile = maze_render.tile
        self._off_x = maze_render.off_x
        self._off_y = maze_render.off_y

        self._sheets.clear()
        for file in self.FILES:
            image = pygame.image.load(f"src/assets/maze/{file}")
            self._sheets.append(pygame.transform.scale(
                image, (self._frames * self._tile, 2 * self._tile)))

    def render(self, maze: MazeGrid, change_style: bool) -> None:
        """
        Method that is responsible about rendrening the
        consumable (pac-cums and super pac-cums)
        """
        if change_style:
            self._style = (self._style + 1) % len(self._sheets)

        t = self._tile
        frame = (pygame.time.get_ticks() * self._fps // 1000) % self._frames
        sheet = self._sheets[self._style]

        for row in maze.grid:
            for cell in row:
                if not cell.consumes:
                    continue

                is_super = any(isinstance(c, SuperPacGum)
                               for c in cell.consumes)
                area = pygame.Rect(frame * t, (1 if is_super else 0) * t, t, t)
                self._screen.blit(sheet, (self._off_x + cell.x * t,
                                          self._off_y + cell.y * t), area)
