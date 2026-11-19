from ..data_dir import ASSETS_DIR
from ..maze_adapter import CellType
from typing import Any
import pygame


class RenderMaze:

    """
    Class that is responsible about rendering the maze
    """

    WALL_FILES = ['blue_wl.png', 'rose_wl.png', 'red_walls.png',
                  'purple_walls.png', 'green_walls.png']
    LOGO_FILE = 'orng_wl.png'

    NEIGHBORS = ((1, 0, -1), (2, 1, -1), (4, 1, 0), (8, 1, 1),
                 (16, 0, 1), (32, -1, 1), (64, -1, 0), (128, -1, -1))

    def __init__(self, screen: pygame.Surface, width: int, height: int):
        """
        Method that initialize all the attribute of the instance
        created from this class
        """
        self._screen = screen
        self._width = width
        self._height = height
        self._frames = 8
        self._fps = 10

        self._tile = 0
        self._off_x = 0
        self._off_y = 0

        self._wall_sheets: list[pygame.Surface] = []
        self._logo_sheet: pygame.Surface | None = None
        self._style = 0
        self._walls: list[tuple[int, int, int, bool]] = []

    @property
    def tile(self) -> int:
        """
        Method that return the tile size
        """
        return self._tile

    @property
    def off_x(self) -> int:
        """
        Method that return the offset x to centrelize
        the maze in the middle
        """
        return self._off_x

    @property
    def off_y(self) -> int:
        """
        Method that return the offset y to centrelize
        the maze in the middle
        """
        return self._off_y

    def prepare(self, maze: Any) -> None:
        """
        After every new maze this method prepare the envirment
        for the new maze
        """
        self._tile = min(self._width // maze.width,
                         self._height // maze.height)
        self._off_x = (self._width - self._tile * maze.width) // 2
        self._off_y = (self._height - self._tile * maze.height) // 2

        self._wall_sheets = [self._load(f) for f in self.WALL_FILES]
        self._logo_sheet = self._load(self.LOGO_FILE)

        self._walls.clear()
        for row in maze.grid:
            for cell in row:
                if cell.is_wall:
                    is_logo = cell.cell_type is CellType.LOGO
                    self._walls.append(
                        (cell.x, cell.y, self._get_mask(maze, cell), is_logo))

    def render(self, change_style: bool) -> None:
        """
        Method that is responsible about rendering the maze
        on the screen
        """
        if change_style:
            self._style = (self._style + 1) % len(self._wall_sheets)

        logo_sheet = self._logo_sheet

        t = self._tile
        time = pygame.time.get_ticks() * self._fps // 1000

        for x, y, mask, is_logo in self._walls:
            sheet = logo_sheet if is_logo else self._wall_sheets[
                self._style]
            frame = (time + x + y) % self._frames
            area = pygame.Rect((mask % 16) * t, (frame * 16 + mask // 16) * t,
                               t, t)
            if sheet:
                self._screen.blit(sheet, (self._off_x + x * t,
                                          self._off_y + y * t), area)

    def _load(self, file: str) -> pygame.Surface:
        """
        Method that load image and transform its dimension and
        return its object
        """
        image = pygame.image.load(ASSETS_DIR / "maze" / file)
        
        t = self._tile
        return pygame.transform.scale(image, (16 * t, 16 * t * self._frames))

    def _get_mask(self, maze: Any, cell: Any) -> int:
        """
        Method that calculate the mask for every cell
        """
        mask = 0
        for value, dx, dy in self.NEIGHBORS:
            x, y = cell.x + dx, cell.y + dy
            inside = 0 <= x < maze.width and 0 <= y < maze.height
            if inside and maze.grid[y][x].cell_type is cell.cell_type:
                mask += value
        return mask
