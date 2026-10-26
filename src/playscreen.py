from ui.screen import Screen
from ui.renderer import Renderer
from ui.inputhandler import InputCommand
from config import Config
from maze_adapter import MazeAdapter


class PlayScreen(Screen):

    def __init__(self, config: Config) -> None:

        self._change_style = False
        level = config.generate_level(1)
        self._maze = MazeAdapter().generate_maze(level)

    def handle_input(self, command: InputCommand) -> None:

        if command.change_style:
            self._change_style = True

    def update(self, dt: int) -> None:

        if Screen.door_w >= 0:
            Screen.door_w -= 1100 * (dt / 1000)

    def render(self, render: Renderer) -> None:

        render.clear()
        render.render_maze(self._maze, self._change_style)
        self._change_style = False
        self.open_door(render)

    def open_door(self, render: Renderer) -> None:

        render.draw_door(0, Screen.door_w)
        render.draw_door(Screen.screen_w - Screen.door_w, Screen.door_w)
