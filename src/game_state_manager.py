from ui.inputhandler import InputCommand
from ui.screen import Screen
from ui.renderer import Renderer
from main_menu_screen import MainMenuScreen
from playscreen import PlayScreen


class GameStateManager:

    def __init__(self) -> None:

        self._active_screen: Screen | None = None
        self._screens: dict[str, Screen] = {}
        self._create_screens()

    def handle_input(self, command: InputCommand) -> None:
        self._active_screen.handle_input(command)

    def change_state(self, new_state: str) -> None:
        if new_state in self._screens:
            self._active_screen = self._screens[new_state]

    def update(self, dt: float) -> None:
        self._active_screen.update(dt)

    def render(self, render: Renderer) -> None:
        self._active_screen.render(render)

    def _create_screens(self) -> None:

        self._screens['main_menu'] = MainMenuScreen()
        self._screens['play'] = PlayScreen()
