from typing import Iterable, Optional, Protocol
import pygame


class _MazeRender(Protocol):
    """
    Class used to avoid cirulare import
    """
    @property
    def tile(self) -> int: ...

    @property
    def off_x(self) -> int: ...

    @property
    def off_y(self) -> int: ...


class _Direction(Protocol):
    """
    Class used to avoid cirulare import
    """
    @property
    def dx(self) -> int: ...

    @property
    def dy(self) -> int: ...


class _State(Protocol):
    """
    Class used to avoid cirulare import
    """
    @property
    def name(self) -> str: ...


class _Ghost(Protocol):
    """
    Class used to avoid cirulare import
    """
    @property
    def x(self) -> float: ...

    @property
    def y(self) -> float: ...

    @property
    def name(self) -> str: ...

    @property
    def state(self) -> _State: ...

    @property
    def cur_direction(self) -> _Direction: ...

    @property
    def frightened_duration(self) -> Optional[float]: ...


class RenderGhost:

    """
    Class rensponsible about rendring the ghosts
    """
    def __init__(self, screen: pygame.Surface):
        """
        Method that initialize all the attribute of the instance
        created from this class
        """
        self._screen = screen
        self._folder = "src/assets/entities/"
        self._names = ["Blinky", "Pinky", "Inky", "Clyde"]
        self._rows = {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}
        self._frames = 8
        self._fps = 20

        self._tile = 0
        self._off_x = 0
        self._off_y = 0
        self._sheets: dict[str, pygame.Surface] = {}

    def prepare(self, maze_render: _MazeRender) -> None:
        """
        Method that prepare the envirment for the ghost to be
        rendered
        """
        self._tile = maze_render.tile
        self._off_x = maze_render.off_x
        self._off_y = maze_render.off_y

        for name in self._names:
            self._sheets[name] = self._load(f"ghost_{name.lower()}.png", 4)
        self._sheets["eyes"] = self._load("ghost_eyes.png", 4)
        self._sheets["scared"] = self._load("ghost_frightened.png", 2)

    def render(self, ghosts: Iterable[_Ghost]) -> None:

        """
        Method that render the ghost
        """
        ms = pygame.time.get_ticks()
        frame = (ms * self._fps // 1000) % self._frames
        t = self._tile

        for ghost in ghosts:
            sheet, row = self._pick_sprite(ghost, ms)

            x = self._off_x + round(ghost.x * t)
            y = self._off_y + round(ghost.y * t)
            self._screen.blit(sheet, (x, y),
                              pygame.Rect(frame * t, row * t, t, t))

    def _load(self, file: str, rows: int) -> pygame.Surface:
        """
        Method that load the images
        of the ghosts
        """
        image = pygame.image.load(self._folder + file)
        return pygame.transform.scale(
            image, (self._frames * self._tile, rows * self._tile))

    def _pick_sprite(self, ghost: _Ghost,
                     ms: int) -> tuple[pygame.Surface, int]:
        """
        Method that choose the correct sheet to render
        the ghost depend on their stats
        """
        state = ghost.state.name

        if state == "FRIGHTENED":
            left = ghost.frightened_duration
            blink = left is not None and left <= 2 and (ms // 250) % 2 == 0
            return self._sheets["scared"], 1 if blink else 0

        d = ghost.cur_direction
        row = self._rows.get((d.dx, d.dy), 2)

        if state == "DIED":
            return self._sheets["eyes"], row

        return self._sheets[ghost.name], row
