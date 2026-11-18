from src.ui.screen import Screen
from src.ui.renderer import Renderer
from src.ui.inputhandler import InputCommand
from src.highscore import HighscoreManager
import pygame


class HighscoreScreen(Screen):

    """Class responsable about the highscore screen
    """
    def __init__(self, highscores: HighscoreManager) -> None:
        """
        The method that initialize all the attribute of the
        instance created from this class
        """
        self._highscores = highscores
        self._title_font = pygame.font.Font(None, 90)
        self._font = pygame.font.Font(None, 50)

    def handle_input(self, command: InputCommand) -> None:
        """
        This method check if the mouse is clicked any where
        to go back to the main menu

        """
        if command.mouse_clicked:
            command.back = True

    def update(self, dt: float) -> None:
        """
        Method that change the cursor of the mouse
        """
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        if dt:
            return

    def render(self, render: Renderer) -> None:

        """
        Method responsable about rendring all the text for the highscore
        screen
        """
        mid = self.middle_w

        render.clear()
        render.draw_text(self._title_font, "HIGH SCORES", 'yellow', (mid, 60))

        scores = self._highscores.get_top_scores(10)
        render.draw_text(self._font, "" if scores else "No scores yet",
                         'white', (mid, 300))

        for rank, (name, score) in enumerate(scores, start=1):
            y = (50 * rank) + 100
            render.draw_text(self._font, f"{rank}. {name}", 'white',
                             (mid - 250, y), center=False)
            render.draw_text(self._font, str(score), 'yellow',
                             (mid + 150, y), center=False)

        render.draw_text(self._font, "Click anywhere to go back", 'gray',
                         (mid, self.screen_h - 50))
