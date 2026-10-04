from typing import Any
import pygame


class Renderer:

    def __init__(self, width: int, height: int):

        pygame.init()
        self._screen = pygame.display.set_mode((width, height))
        self._width = width
        self._height = height
        pygame.display.set_caption("Pac-Man")

    def render_maze(self, maze) -> None:
        pass

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

    def get_image(self, path: str) -> pygame.Surface:
        return pygame.image.load(path)

    def blit_window(self, to_draw: Any, coord: tuple[int, int]) -> None:
        self._screen.blit(to_draw, coord)
