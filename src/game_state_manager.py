from pathlib import Path
from src.ui.inputhandler import InputCommand
from src.ui.screen import Screen
from src.ui.renderer import Renderer
from src.ui.instructions_screen import InstructionsScreen
from src.ui.highscore_screen import HighscoreScreen
from src.main_menu_screen import MainMenuScreen
from src.playscreen import PlayScreen
from src.highscore import HighscoreManager


class GameStateManager:

    def __init__(self, config) -> None:

        self._config = config
        self._highscores = HighscoreManager(Path("../highscores.json"))
        self._active_screen: Screen | None = None
        self._screens: dict[str, Screen] = {
            'main_menu': MainMenuScreen(),
            'highscores': HighscoreScreen(self._highscores),
            'instructions': InstructionsScreen(),
        }

    def handle_input(self, command: InputCommand) -> None:
        self._active_screen.handle_input(command)

    def update(self, dt: float) -> None:
        self._active_screen.update(dt)

    def render(self, render: Renderer) -> None:
        self._active_screen.render(render)

    def save_game(self) -> None:
        if isinstance(self._active_screen, PlayScreen):
            self._active_screen.save_game()

    def change_state(self, new_state: str) -> None:

        if new_state == 'main_menu':
            Screen.door_closed = False

        elif new_state == 'play':
            self._screens['play'] = PlayScreen(self._config, self._highscores)

        elif new_state == 'continue':
            screen = PlayScreen(self._config, self._highscores, load=True)

            if not screen.loaded:
                self._screens['main_menu'].show_message("No game to resume")
                return

            self._screens['play'] = screen
            new_state = 'play'

        self._active_screen = self._screens[new_state]