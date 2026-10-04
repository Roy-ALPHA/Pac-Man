from ui.inputhandler import InputCommand
from ui.screen import Screen
from main_menu_screen import MainMenuScreen
from playscreen import PlayScreen


class GameStateManager:

    def __init__(self) -> None:

        self.active_screen: Screen | None = None
        self.screens: dict[str, Screen] = {}
        self.set_screens()

    def handle_input(self, command: InputCommand) -> None:
        self.active_screen.handle_input(command)

    def change_state(self, new_state: str) -> None:
        if new_state in self.screens:
            self.active_screen = self.screens[new_state]

    def update(self, dt: float) -> None:
        self.active_screen.update(dt)

    def render(self) -> None:
        self.active_screen.render()

    def set_screens(self) -> None:

        self.screens['main_menu'] = MainMenuScreen()
        self.screens['play'] = PlayScreen()
        self.active_screen = self.screens['main_menu']
