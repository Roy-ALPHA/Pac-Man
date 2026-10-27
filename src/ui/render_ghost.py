import pygame


class RenderGhost:


    def __init__(self, screen: pygame.Surface):

        self._screen = screen

        self._paths = {
            "Blinky": "assets/entities/ghost_blinky.png",
            "Pinky": "assets/entities/ghost_pinky.png",
            "Inky": "assets/entities/ghost_inky.png",
            "Clyde": "assets/entities/ghost_clyde.png",
        }
    
        self._eyes_path = "assets/entities/ghost_eyes.png"
        self._scared_path = "assets/entities/ghost_frightened.png"
        self._rows = {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}
        self._default_dir = (-1, 0)
        self._frames = 8
        self._anm_fps = 10
        self._scared_row = 0
        self._flash_row = 1
        self._flash_time = 2
        self._flash_fps = 4
        self._smooth_s = 0.07
        self._max_dt_s = 0.1
        self._teleport_tiles = 1
    
        self._tile = 0
        self._off_x = 0
        self._off_y = 0
        self._sheets: dict[str, pygame.Surface] = {}
        self._eyes_sheet: pygame.Surface | None = None
        self._scared_sheet: pygame.Surface | None = None

        self._gaps: dict[str, list[float]] = {}
        self._last_pos: dict[str, tuple[float, float]] = {}
        self._last_dirs: dict[str, tuple[int, int]] = {}

        self._now_ms = 0
        self._last_ms: int | None = None
        self._dt = 0.0
        self._ghost = None
        self._x = 0.0
        self._y = 0.0
        self._draw_x = 0.0
        self._draw_y = 0.0
        self._dir = self._default_dir
        self._sheet: pygame.Surface | None = None
        self._row = 0
        self._frame = 0

    def _load(self, path: str, rows: int) -> pygame.Surface:

        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(
            image, (self._frames * self._tile, rows * self._tile)
        )

    def prepare(self, maze_render) -> None:
        self._tile = maze_render.tile
        self._off_x = maze_render.off_x
        self._off_y = maze_render.off_y
        self._gaps.clear()
        self._last_pos.clear()

        for name, path in self._paths.items():
            self._sheets[name] = self._load(path, 4)
        self._eyes_sheet = self._load(self._eyes_path, 4)
        self._scared_sheet = self._load(self._scared_path, 2)

    def _update_time(self) -> None:
        self._now_ms = pygame.time.get_ticks()
        self._dt = 0.0
        if self._last_ms is not None:
            self._dt = min((self._now_ms - self._last_ms) / 1000,
                           self._max_dt_s)
        self._last_ms = self._now_ms

    def _update_draw_position(self) -> None:
        name = self._ghost.name

        gap = self._gaps.setdefault(name, [0.0, 0.0])
        last = self._last_pos.get(name)

        if last is not None:
            dx = self._x - last[0]
            dy = self._y - last[1]

            jump = abs(dx) + abs(dy)

            if jump > self._teleport_tiles:
                gap[0] = 0.0
                gap[1] = 0.0

            elif jump > self._ghost.speed * self._dt * 2 + 0.03:
                gap[0] -= dx
                gap[1] -= dy

        self._last_pos[name] = (self._x, self._y)

        gap[0] *= 0.8
        gap[1] *= 0.8

        self._draw_x = self._x + gap[0]
        self._draw_y = self._y + gap[1]

    def _update_direction(self) -> None:
        d = self._ghost.cur_direction
        if (d.dx, d.dy) in self._rows:
            self._last_dirs[self._ghost.name] = (d.dx, d.dy)
        self._dir = self._last_dirs.get(self._ghost.name, self._default_dir)

    def _update_sprite(self) -> None:
        ghost = self._ghost
        self._frame = (self._now_ms * self._anm_fps // 1000) % self._frames
        state = ghost.state.name

        if state == "DIED":
            self._sheet = self._eyes_sheet
            self._row = self._rows[self._dir]

        elif state == "FRIGHTENED":
            left = ghost.frightened_duration
            blink = (left is not None and left <= self._flash_time
                     and (self._now_ms * self._flash_fps // 1000) % 2 == 0)
            self._sheet = self._scared_sheet
            self._row = self._flash_row if blink else self._scared_row

        else:
            self._sheet = self._sheets.get(ghost.name,
                                           next(iter(self._sheets.values())))
            self._row = self._rows[self._dir]

    def render(self, ghosts) -> None:
        if not self._sheets:
            return

        self._update_time()
        t = self._tile
        for ghost in ghosts:
            self._ghost = ghost
            self._x, self._y = ghost.x, ghost.y
            self._update_draw_position()
            self._update_direction()
            self._update_sprite()
            self._screen.blit(
                self._sheet,
                (self._off_x + round(self._draw_x * t),
                 self._off_y + round(self._draw_y * t)),
                pygame.Rect(self._frame * t, self._row * t, t, t),
            )
