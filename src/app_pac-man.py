from game_state_manager import GameStateManager
from ui.inputhandler import InputHandler
from ui.renderer import Renderer
from ui.screen import Screen
import pygame


class PacmanApp:

    def __init__(self, w: int, h: int) -> None:

        self.is_running: bool = True
        self.renderer = Renderer(w, h)
        Screen.screen_w = w
        Screen.screen_h = h
        self.input_handler = InputHandler()
        self.state_manager = GameStateManager()

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

            dt = clock.tick(60)
            self.state_manager.update(dt)
            self.state_manager.render(self.renderer)
            self.renderer.update_display()

    def quit(self) -> None:
        self.is_running = False
        self.input_handler.clean()


if __name__ == "__main__":
    test = PacmanApp(1200, 800)
    test.run()
