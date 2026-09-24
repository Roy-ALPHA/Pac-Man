from game_state_manager import GameStateManager
from ui.inputhandler import InputHandler
from ui.renderer import Renderer
from main_menu_screen import MainMenuScreen


class PacmanApp:

    def __init__(self, config) -> None:

        self.is_running: bool = True
        self.input_handler = InputHandler()
        self.state_manager = GameStateManager()
        self.state_manager.screens["main_menu"] = MainMenuScreen()
        self.state_manager.change_state("main_menu")
        self.renderer = Renderer()

    def run(self) -> None:

        while self.is_running:

            command = self.input_handler.handle_events()
            if self.state_manager.active_screen:
                self.state_manager.active_screen.handle_input(command)
            self.state_manager.update(0.016)
            self.state_manager.draw(self.renderer)

    def quit(self) -> None:
        self.is_running = False
