from ui.renderer import Renderer
from ui.screen import Screen


class GameStateManager:

    def __init__(self) -> None:

        self.active_screen: Screen | None = None
        self.screens: dict[str, Screen] = {}

    def change_state(self, new_state: str) -> None:
        if new_state in self.screens:
            self.active_screen = self.screens[new_state]

    def update(self, dt: float) -> None:
        if self.active_screen:
            self.active_screen.update(dt)

    def draw(self, renderer: Renderer) -> None:

        if self.active_screen:
            self.active_screen.render(renderer)
