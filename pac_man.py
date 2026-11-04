from src.game_state_manager import GameStateManager
from src.ui.inputhandler import InputHandler
from src.ui.renderer import Renderer
from src.ui.screen import Screen
from src.config import Config
from pathlib import Path
import pygame


class PacmanApp:

    SCREENS = {'play': 'play', 'continue_game': 'continue',
               'show_highscores': 'highscores',
               'show_instructions': 'instructions', 'back': 'main_menu'}

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
                self.state_manager.save_game()
                return self.quit()

            for flag, screen in self.SCREENS.items():
                if getattr(command, flag):
                    self.state_manager.change_state(screen)
                    break

            dt = clock.tick(60)
            self.state_manager.update(dt)
            self.state_manager.render(self.renderer)
            self.renderer.update_display()

    def quit(self) -> None:
        self.is_running = False
        self.input_handler.clean()


if __name__ == "__main__":

    config = Config().from_file(Path("../config.json"))
    pac_man = PacmanApp(config, 1200, 800)
    pac_man.run()