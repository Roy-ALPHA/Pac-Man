from ui.screen import Screen
from ui.inputhandler import InputCommand
from ui.renderer import Renderer


class MainMenuScreen(Screen):

    def __init__(self):
        self._selected_index: int = 0

    def handle_input(self, command: InputCommand) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self, renderer: Renderer) -> None:
        renderer.clear()
        color_start = (255, 255, 0) if self._selected_index == 0 else (
                      255, 255, 255)
        color_quit = (255, 255, 0) if self._selected_index == 1 else (
                      255, 255, 255)
