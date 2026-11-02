from pathlib import Path
from src.ui.inputhandler import InputCommand
from src.ui.screen import Screen
from src.ui.renderer import Renderer
from src.ui.instructions_screen import InstructionsScreen
from src.main_menu_screen import MainMenuScreen
from src.playscreen import PlayScreen
from src.ui.highscore_screen import HighscoreScreen
from src.highscore import HighscoreManager


class GameStateManager:

    def __init__(self, config) -> None:

        self._config = config
        self._active_screen: Screen | None = None
        self._screens: dict[str, Screen] = {}
        self._highscores = HighscoreManager(Path("../highscores.json"))
        self._create_screens(config)

    def handle_input(self, command: InputCommand) -> None:
        self._active_screen.handle_input(command)

    def change_state(self, new_state: str) -> None:

        if new_state == 'play':
            self._screens['play'] = PlayScreen(self._config, self._highscores)

        elif new_state == 'main_menu':
            Screen.door_closed = False

        if new_state in self._screens:
            self._active_screen = self._screens[new_state]

    def update(self, dt: float) -> None:
        self._active_screen.update(dt)

    def render(self, render: Renderer) -> None:
        self._active_screen.render(render)

    def _create_screens(self, config) -> None:

        self._screens['main_menu'] = MainMenuScreen()
        self._screens['play'] = PlayScreen(config, self._highscores)
        self._screens['highscores'] = HighscoreScreen(self._highscores)
        self._screens['instructions'] = InstructionsScreen()