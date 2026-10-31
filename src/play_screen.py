from .ui.screen import Screen
from .ui.renderer import Renderer
from .ui.inputhandler import InputCommand
from .entities import Direction
from .config import Config
from .engine import GameEngine, EngineState


class PlayScreen(Screen):

    def __init__(self, config: Config) -> None:

        self._change_style = False
        self._direction = Direction.NONE
        self._engine = GameEngine(config)
        self._frame = None          # latest data sent by the engine

    @property
    def is_paused(self) -> bool:
        return self._engine.state is EngineState.STOPPED

    def _toggle_pause(self) -> None:

        if self.is_paused:
            self._engine.resume()
        elif self._engine.state in (EngineState.PLAYING,
                                    EngineState.RESPAWNING):
            self._engine.stop()

    def handle_input(self, command: InputCommand) -> None:

        if command.pause:
            self._toggle_pause()

        if command.change_style:
            self._change_style = True

        if command.direction is not Direction.NONE:
            self._direction = command.direction

    def update(self, dt: int) -> None:

        if not self.is_paused and Screen.door_w >= 0:
            Screen.door_w -= 1100 * (dt / 1000)

        # while paused the engine does not move anything, it only
        # sends the same frame again, so the picture stays frozen
        self._frame = self._engine.tick(dt / 1000, self._direction)

    def render(self, render: Renderer) -> None:

        render.clear()

        if self._frame is not None:
            render.render_maze(self._frame.grid, self._change_style)
            render.render_entities(self._frame.pacman, self._frame.ghosts)

        self._change_style = False
        self.open_door(render)

        if self.is_paused:
            render.render_pause()

    def open_door(self, render: Renderer) -> None:

        render.draw_door(0, Screen.door_w)
        render.draw_door(Screen.screen_w - Screen.door_w, Screen.door_w)
