from .ui.screen import Screen
from .ui.renderer import Renderer
from .ui.inputhandler import InputCommand
from .entities import Direction
from .config import Config
from .engine import GameEngine



class PlayEngine(GameEngine):

    def _load_level(self):
        super()._load_level()

    @property
    def is_level_loaded(self):
        return self._is_level_loaded

    @property
    def grid(self):
        return self._grid

    @property
    def pacman(self):
        return self._pacman

    @property
    def ghosts(self):
        return self._ghosts


class PlayScreen(Screen):

    def __init__(self, config: Config) -> None:

        self._change_style = False
        self._direction = Direction.NONE
        self._engine = PlayEngine(config)

    @staticmethod
    def open_door(render: Renderer) -> None:

        render.draw_door(0, Screen.door_w)
        render.draw_door(Screen.screen_w - Screen.door_w, Screen.door_w)

    def handle_input(self, command: InputCommand) -> None:

        if command.change_style:
            self._change_style = True

        if command.direction is not Direction.NONE:
            self._direction = command.direction

    def update(self, dt: int) -> None:

        if Screen.door_w >= 0:
            Screen.door_w -= 1100 * (dt / 1000)

        self._engine.tick(dt / 1000, self._direction)

    def render(self, render: Renderer) -> None:

        render.clear()

        if self._engine.is_level_loaded:
            render.render_maze(self._engine.grid, self._change_style)
            render.render_entities(self._engine.pacman, self._engine.ghosts)

        self._change_style = False
        self.open_door(render)
