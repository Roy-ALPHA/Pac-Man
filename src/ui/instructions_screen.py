from src.ui.screen import Screen
from src.ui.renderer import Renderer
from src.ui.inputhandler import InputCommand
import pygame


class InstructionsScreen(Screen):

    # ALL CAPITALS = heading (yellow). Empty text = blank line.
    LINES = [
        "GOAL",
        "Eat all the dots in the maze to finish the level.",
        "Finish all the levels to win the game.",
        "",
        "CONTROLS",
        "Arrow keys or WASD: move Pac-Man",
        "P or Space: pause the game (you can save there)",
        "C: change the maze style",
        "",
        "GHOSTS",
        "Touching a ghost costs you one life.",
        "Big dots in the corners make the ghosts scared.",
        "Eat a scared ghost to get extra points.",
        "",
        "CHEATS",
        "F1: cheats on/off, then press a number key",
        "1: invincible    2: extra life    3: freeze ghosts",
        "4: faster Pac-Man    5: skip the level",
        "",
        "GAME OVER",
        "You lose when you have no lives left.",
        "You also lose when the level time is up.",
        "Type your name and click Save to join the highscores.",
    ]

    def __init__(self) -> None:
        self._title_font = pygame.font.Font(None, 70)
        self._font = pygame.font.Font(None, 30)

    def handle_input(self, command: InputCommand) -> None:
        if command.mouse_clicked:
            command.back = True

    def update(self, dt: float) -> None:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def render(self, render: Renderer) -> None:

        render.clear()
        render.draw_text(self._title_font, "HOW TO PLAY", 'yellow',
                         (self.middle_w, 40))

        for i, text in enumerate(self.LINES):
            color = 'yellow' if text.isupper() else 'white'
            render.draw_text(self._font, text, color,
                             (self.middle_w, 90 + i * 27))

        render.draw_text(self._font, "Click anywhere to go back", 'gray',
                         (self.middle_w, self.screen_h - 25))