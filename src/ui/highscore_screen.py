from src.ui.screen import Screen
from src.ui.renderer import Renderer
from src.ui.inputhandler import InputCommand
from src.highscore import HighscoreManager
import pygame


class HighscoreScreen(Screen):

    def __init__(self, highscores: HighscoreManager) -> None:
        self._highscores = highscores
        self._title_font = pygame.font.Font(None, 90)
        self._font = pygame.font.Font(None, 50)

    def handle_input(self, command: InputCommand) -> None:

        if command.mouse_clicked:
            command.back = True

    def update(self, dt: float) -> None:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def render(self, render: Renderer) -> None:
        render.clear()

        self._draw_text(render, self._title_font, "HIGH SCORES",
                        self.middle_w - 200, 60, 'yellow')

        scores = self._highscores.get_top_scores(10)

        if not scores:
            self._draw_text(render, self._font, "No scores yet",
                            self.middle_w - 100, 300, 'white')

        for rank, (name, score) in enumerate(scores, start=1):
            y = 180 + (rank - 1) * 50
            self._draw_text(render, self._font, f"{rank}. {name}",
                            self.middle_w - 250, y, 'white')
            self._draw_text(render, self._font, str(score),
                            self.middle_w + 150, y, 'yellow')

        self._draw_text(render, self._font, "Click the mouse anywhere to go back",
                        self.middle_w - 230, self.screen_h - 70, 'gray')

    def _draw_text(self, render: Renderer, font: pygame.font.Font,
                   text: str, x: int, y: int, color: str) -> None:
        image = font.render(text, True, color)
        render.blit_window(image, (x, y))