from typing import Any, cast
from src.ui.inputhandler import InputCommand
from src.ui.screen import Screen
from src.ui.renderer import Renderer
from src.ui.instructions_screen import InstructionsScreen
from src.ui.highscore_screen import HighscoreScreen
from src.main_menu_screen import MainMenuScreen
from src.playscreen import PlayScreen
from src.highscore import HighscoreManager


class GameStateManager:

    def __init__(self, config: Any) -> None:

        """Method that initialize all the attribute of the
        instance created from this class.
        """
        self._config = config
        self._highscores = HighscoreManager()
        self._active_screen: Screen | None = None
        self._screens: dict[str, Screen] = {
            'main_menu': MainMenuScreen(),
            'highscores': HighscoreScreen(self._highscores),
            'instructions': InstructionsScreen(),
        }

    def handle_input(self, command: InputCommand) -> None:
        """
        Method that call the input handler method of the active screen
        """
        if self._active_screen:
            self._active_screen.handle_input(command)

    def update(self, dt: float) -> None:
        """
        Method that call the update method of the active screen
        """
        if self._active_screen:
            self._active_screen.update(dt)

    def render(self, render: Renderer) -> None:
        """
        Method that call the render method of the active screen
        """
        if self._active_screen:
            self._active_screen.render(render)

    def save_game(self) -> None:
        if isinstance(self._active_screen, PlayScreen):
            self._active_screen.save_game()

    def change_state(self, new_state: str) -> None:

        """Method that change the screen to the new state
        new state is a key of the new screen that will be
        rendered instead of the current one
        """
        if new_state == 'main_menu':
            Screen.door_closed = False

        elif new_state == 'play':
            self._screens['play'] = PlayScreen(self._config, self._highscores)

        elif new_state == 'continue':
            screen = PlayScreen(self._config, self._highscores,
                                load_to_resume=True)

            if not screen.loaded:
                cast(MainMenuScreen,
                     self._screens['main_menu']).time_to_appear = 2000
                return

            self._screens['play'] = screen
            new_state = 'play'

        self._active_screen = self._screens[new_state]
