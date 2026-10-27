import pygame


class RenderPlayer:

    """Renders the pac-man player. All state lives in attributes."""

    def __init__(self, screen: pygame.Surface):
        self._screen = screen
        self._path = "assets/entities/pacman.png"
        self._rows = {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}
        self._frames = 8
        self._idle_frame = 3
        self._anm_fps = 20
        self._smooth_s = 0.07
        self._max_dt_s = 0.1
        self._teleport_tiles = 1

        self._sheet: pygame.Surface | None = None
        self._tile = 0
        self._off_x = 0
        self._off_y = 0

        self._now_ms = 0
        self._last_ms: int | None = None
        self._dt = 0.0
        self._x = 0.0
        self._y = 0.0
        self._last_x: float | None = None
        self._last_y = 0.0
        self._draw_x = 0.0
        self._draw_y = 0.0
        self._gap_x = 0.0
        self._gap_y = 0.0
        self._dir = (0, 0)
        self._row = 0
        self._frame = 0
        self._moving = False
        self._at_wall = False

    def prepare(self, maze_render) -> None:
        self._tile = maze_render.tile
        self._off_x = maze_render.off_x
        self._off_y = maze_render.off_y
        self._last_x = None
        self._gap_x = self._gap_y = 0.0

        sheet = pygame.image.load(self._path).convert_alpha()
        self._sheet = pygame.transform.smoothscale(
            sheet, (self._frames * self._tile, 4 * self._tile)
        )

    def _update_time(self) -> None:
        self._now_ms = pygame.time.get_ticks()
        self._dt = 0.0
        if self._last_ms is not None:
            self._dt = min((self._now_ms - self._last_ms) / 1000,
                           self._max_dt_s)
        self._last_ms = self._now_ms

    def _update_gap(self, player) -> None:
        """Cancel engine inside the gap."""
        if self._last_x is not None:
            dx = self._x - self._last_x
            dy = self._y - self._last_y
            jump = abs(dx) + abs(dy)
            if jump > self._teleport_tiles:
                self._gap_x = self._gap_y = 0.0
            elif jump > player._speed * self._dt * 2 + 0.03:
                self._gap_x -= dx
                self._gap_y -= dy
        self._last_x, self._last_y = self._x, self._y

    def _update_draw_position(self, player) -> None:
        direction = player.cur_direction
        self._dir = (direction.dx, direction.dy)

        blocked = (
            self._dir in self._rows
            and not player.can_move(direction)
        )

        if blocked:
            tile_x, tile_y = player.tile

            target_x = tile_x - self._x
            target_y = tile_y - self._y

            dx = target_x - self._gap_x
            dy = target_y - self._gap_y

            step = player._speed * self._dt

            if abs(dx) + abs(dy) <= step:
                self._gap_x = target_x
                self._gap_y = target_y
                self._at_wall = True
            else:
                self._gap_x += dx * 0.2
                self._gap_y += dy * 0.2
                self._at_wall = False
        else:
            self._gap_x *= 0.8
            self._gap_y *= 0.8
            self._at_wall = False

        self._draw_x = self._x + self._gap_x
        self._draw_y = self._y + self._gap_y
    
    def _update_animation(self) -> None:
        if self._dir in self._rows:
            self._row = self._rows[self._dir]
        self._moving = self._dir in self._rows and not self._at_wall
        if self._moving:
            self._frame = (self._now_ms * self._anm_fps // 1000) % self._frames
        else:
            self._frame = self._idle_frame

    def render(self, player) -> None:
        if self._sheet is None:
            return

        self._x, self._y = player._x, player._y
        self._update_time()
        self._update_gap(player)
        self._update_draw_position(player)
        self._update_animation()

        t = self._tile
        self._screen.blit(
            self._sheet,
            (self._off_x + round(self._draw_x * t),
             self._off_y + round(self._draw_y * t)),
            pygame.Rect(self._frame * t, self._row * t, t, t),
        )