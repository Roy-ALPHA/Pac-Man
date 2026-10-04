from game_state_manager import GameStateManager
from ui.inputhandler import InputHandler
from ui.renderer import Renderer
from ui.screen import Screen
import pygame


class PacmanApp:

    def __init__(self, config) -> None:

        self.is_running: bool = True
        self.renderer = Renderer(1200, 800)
        Screen.screen_w = 1200
        Screen.screen_h = 800
        Screen.renderer = self.renderer
        self.input_handler = InputHandler()
        self.state_manager = GameStateManager()

    def run(self) -> None:

        clock = pygame.time.Clock()

        while self.is_running:

            command = self.input_handler.handle_events()
            self.state_manager.handle_input(command)

            if command.quit:
                return self.quit()

            elif command.play:
                self.state_manager.change_state('play')

            dt = clock.tick(60)
            self.state_manager.update(dt)
            self.state_manager.render()
            self.renderer.update_display()

    def quit(self) -> None:
        self.is_running = False
        self.input_handler.clean()


test = PacmanApp(None)
test.run()
