from src.ui.screen import Screen
from src.ui.renderer import Renderer
from src.ui.inputhandler import InputCommand
import pygame


class InstructionsScreen(Screen):

    LINES = [
        ("GOAL", 'yellow'),
        ("Eat all the dots in the maze to finish the level.", 'white'),
        ("Finish all the levels to win the game.", 'white'),
        ("", 'None'),
        ("CONTROLS", 'yellow'),
        ("Arrow keys or WASD: move Pac-Man", 'white'),
        ("P or Space: pause the game", 'white'),
        ("C: change the maze style", 'white'),
        ("", 'None'),
        ("GHOSTS", 'yellow'),
        ("Touching a ghost costs you one life.", 'white'),
        ("Big dots in the corners make the ghosts scared.", 'white'),
        ("Eat a scared ghost to get extra points.", 'white'),
        ("", 'None'),
        ("GAME OVER", 'yellow'),
        ("You lose when you have no lives left.", 'white'),
        ("You also lose when the level time is up.", 'white'),
        ("", 'None'),
        ("At the end, type your name and click Save to join the highscores.",
         'white'),
    ]

    def __init__(self) -> None:
        self._title_font = pygame.font.Font(None, 90)
        self._font = pygame.font.Font(None, 36)

    def handle_input(self, command: InputCommand) -> None:
        if command.mouse_clicked:
            command.back = True

    def update(self, dt: float) -> None:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def render(self, render: Renderer) -> None:
        render.clear()

        self._draw_centered(render, self._title_font, "HOW TO PLAY",
                            60, 'yellow')

        y = 140
        for text, color in self.LINES:
            if text:
                self._draw_centered(render, self._font, text, y, color)
            y += 30

        self._draw_centered(render, self._font, "Click anywhere to go back",
                            self.screen_h - 30, 'gray')

    def _draw_centered(self, render: Renderer, font: pygame.font.Font,
                       text: str, y: int, color: str) -> None:
        image = font.render(text, True, color)
        render.blit_window(image, image.get_rect(
            center=(self.middle_w, y)).topleft)
