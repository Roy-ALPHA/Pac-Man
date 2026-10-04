from ui.screen import Screen
from ui.inputhandler import InputCommand


class PlayScreen(Screen):

    def __init__(self) -> None:
        pass

    def handle_input(self, command: InputCommand) -> None:
        pass

    def update(self, dt: int) -> None:

        if Screen.door_w >= 0:
            Screen.door_w -= 1100 * (dt / 1000)

    def render(self) -> None:
        Screen.renderer.clear()
        self.open_door()

    def open_door(self) -> None:

        Screen.renderer.draw_door(0, Screen.door_w)
        Screen.renderer.draw_door(Screen.screen_w - Screen.door_w,
                                  Screen.door_w)
