from src.game_state_manager import GameStateManager
from src.ui.inputhandler import InputHandler
from src.ui.renderer import Renderer
from src.ui.screen import Screen
from src.config import Config
from pathlib import Path
import pygame


class PacmanApp:

    def __init__(self, config, w: int, h: int) -> None:

        self.is_running: bool = True
        self.renderer = Renderer(w, h)
        Screen.screen_w = w
        Screen.screen_h = h
        self.input_handler = InputHandler()
        self.state_manager = GameStateManager(config)

    def run(self) -> None:

        self.state_manager.change_state('main_menu')
        clock = pygame.time.Clock()

        while self.is_running:

            command = self.input_handler.handle_events()
            self.state_manager.handle_input(command)

            if command.quit:
                return self.quit()

            elif command.play:
                self.state_manager.change_state('play')

            elif command.show_highscores:
                self.state_manager.change_state('highscores')

            elif command.back:
                self.state_manager.change_state('main_menu')

            elif command.show_highscores:
                self.state_manager.change_state('highscores')

            elif command.show_instructions:
                self.state_manager.change_state('instructions')

            dt = clock.tick(60)
            self.state_manager.update(dt)
            self.state_manager.render(self.renderer)
            self.renderer.update_display()

    def quit(self) -> None:
        self.is_running = False
        self.input_handler.clean()


if __name__ == "__main__":

<<<<<<< Updated upstream
    config = Config().from_file(Path("../config.json"))
    pac_man = PacmanApp(config, 1200, 800)
    pac_man.run()
=======
    config = Config().from_file(Path("config.json"))
    test = PacmanApp(config, 1200, 800)
    test.run()
>>>>>>> Stashed changes
