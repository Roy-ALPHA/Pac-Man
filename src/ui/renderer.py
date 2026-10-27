from typing import Any
import pygame
from .render_maze import RenderMaze
from .render_consumables import RenderConsumables
from .render_player import RenderPlayer
from .render_ghost import RenderGhost


class Renderer:

    """Manager class owns the window and delegates drawing to other classes"""

    def __init__(self, width: int, height: int):

        pygame.init()
        self._screen: pygame.Surface = pygame.display.set_mode((width, height))
        self._width: int = width
        self._height: int = height
        pygame.display.set_caption("Pac-Man")

        self._maze_renderer: RenderMaze = RenderMaze(
            self._screen, width, height)
        self._consumables_renderer: RenderConsumables = RenderConsumables(
            self._screen)
        self._player_renderer: RenderPlayer = RenderPlayer(self._screen)
        self._ghost_renderer: RenderGhost = RenderGhost(self._screen)
        self._first_maze = True

    def render_maze(self, maze, change_style: bool) -> None:

        if self._first_maze:
            self._first_maze = False
            self._maze_renderer.prepare(maze)
            self._consumables_renderer.prepare(self._maze_renderer)
            self._player_renderer.prepare(self._maze_renderer)
            self._ghost_renderer.prepare(self._maze_renderer)

        self._maze_renderer.render(change_style)
        self._consumables_renderer.render(maze, change_style)

    def render_entities(self, player, ghosts) -> None:
        self._player_renderer.render(player)
        self._ghost_renderer.render(ghosts)

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
