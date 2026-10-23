from typing import Any
import pygame
from .maze_render import RenderMaze


class Renderer:

    """Manager class it owns the window and delegates drawing"""

    def __init__(self, width: int, height: int):

        pygame.init()
        self._screen: pygame.Surface = pygame.display.set_mode((width, height))
        self._width: int = width
        self._height: int = height
        pygame.display.set_caption("Pac-Man")

        self._maze_renderer: RenderMaze = RenderMaze(
            self._screen, width, height)

    def render_maze(self, maze, change_style: bool,
                    first_maze: bool = False) -> None:
        self._maze_renderer.render(maze, change_style, first_maze)

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
