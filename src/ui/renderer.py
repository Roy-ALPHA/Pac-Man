import pygame


class Renderer:

    def __init__(self):

        pygame.init()
        info: pygame.surface = pygame.display.Info()
        self._screen = pygame.display.set_mode(
            (info.current_w, info.current_h - 69), pygame.RESIZABLE)
        self._sprites: dict = {}

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
