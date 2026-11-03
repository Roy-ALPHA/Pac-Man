from typing import Any
import pygame
from .render_maze import RenderMaze
from .render_consumables import RenderConsumables
from .render_player import RenderPlayer
from .render_ghost import RenderGhost


class Renderer:

    HUD_WIDTH = 200

    def __init__(self, width: int, height: int):

        pygame.init()
        self._screen = pygame.display.set_mode((width, height))
        self._width = width
        self._height = height
        pygame.display.set_caption("Pac-Man")
        self._label_font = pygame.font.Font(None, 30)
        self._value_font = pygame.font.Font(None, 50)
        self._maze_renderer = RenderMaze(self._screen,
                                         width - self.HUD_WIDTH, height)
        self._consumables_renderer = RenderConsumables(self._screen)
        self._player_renderer = RenderPlayer(self._screen)
        self._ghost_renderer = RenderGhost(self._screen)
        self._maze = None

    def render_maze(self, maze, change_style: bool) -> None:

        if self._maze is not maze:
            self._maze = maze
            self._maze_renderer.prepare(maze)
            self._consumables_renderer.prepare(self._maze_renderer)
            self._player_renderer.prepare(self._maze_renderer)
            self._ghost_renderer.prepare(self._maze_renderer)

        self._maze_renderer.render(change_style)
        self._consumables_renderer.render(maze, change_style)

    def draw_text(self, font: pygame.font.Font, text: str, color: str,
                  pos: tuple[int, int], center: bool = True) -> None:

        if not text:
            return

        image = font.render(text, True, color)
        rect = (image.get_rect(center=pos) if center
                else image.get_rect(topleft=pos))
        self._screen.blit(image, rect)
    def render_entities(self, player, ghosts) -> None:
        self._player_renderer.render(player)
        self._ghost_renderer.render(ghosts)

    def render_hub(self, score: int, lives: int, level: int,
                   max_level: int, time_left: float) -> None:

        x = self._width - self.HUD_WIDTH

        pygame.draw.rect(self._screen, (20, 20, 60),
                         (x, 0, self.HUD_WIDTH, self._height))
        pygame.draw.line(self._screen, 'yellow', (x, 0), (x, self._height), 3)

        lines = [("SCORE", score), ("LIVES", lives),
                 ("LEVEL", f"{level}/{max_level}"), ("TIME", int(time_left))]

        for i, (label, value) in enumerate(lines):
            y = 60 + i * 90
            self._screen.blit(
                self._label_font.render(label, True, 'yellow'), (x + 20, y))
            self._screen.blit(
                self._value_font.render(str(value), True, 'white'),
                (x + 20, y + 28))

    def clear(self) -> None:
        self._screen.fill((0, 0, 0))

    def update_display(self) -> None:
        pygame.display.flip()

    def draw_door(self, x: int, door_w: int) -> None:
        pygame.draw.rect(self._screen, 'yellow', (x, 0, door_w, self._height))

    def blit_window(self, to_draw: Any, coord: tuple[int, int],
                    area=None) -> None:
        self._screen.blit(to_draw, coord, area)