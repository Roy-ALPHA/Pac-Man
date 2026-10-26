import math

import pygame


class RenderPlayer:
    """Draws Pac-Man from the sprite sheet (pacman.png, 256x128).

    Sheet layout: 8 frames per row, each frame 32x32, one row per direction:
        row 0: facing RIGHT    row 1: facing DOWN
        row 2: facing LEFT     row 3: facing UP

    The engine keeps Pac-Man's exact position as floats in tile units
    (`_x`, `_y`), so the sprite is drawn exactly there.

    Smooth turns: when he turns, the engine snaps him to the middle of the
    tile in ONE frame (up to half a tile of jump). We don't draw that jump:
    we keep the sprite where it was and let it glide to the real position in
    a fraction of a second.

    Walls: the engine stops him as soon as the tile he is rounded to has a wall
    ahead, i.e. half a tile BEFORE the wall. We let the sprite finish that
    half tile so he touches the wall.
    """

    SHEET_PATH = "assets/entities/pacman.png"
    FRAMES = 8
    IDLE_FRAME = 3             # frame shown while he is standing still
    ROWS = {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}

    TURN_SMOOTH_S = 0.07       # glide time constant (bigger = softer turn)
    TELEPORT_TILES = 1.0       # a jump this big is a respawn: no glide
    MAX_DT_S = 0.1

    def __init__(self, screen: pygame.Surface):

        self._screen: pygame.Surface = screen
        self._anm_fps: int = 20
        self._sheet: pygame.Surface | None = None
        self._tile: int = 0
        self._off_x: int = 0
        self._off_y: int = 0
        self._row: int = 0          # last facing row (starts: right)

        self._last_pos: tuple[float, float] | None = None
        self._last_ms: int | None = None
        self._gap_x: float = 0.0    # drawn position minus real position
        self._gap_y: float = 0.0
        self._reach: float = 0.0    # extra tiles drawn ahead, up to the wall
        self._reach_dir: tuple[int, int] = (0, 0)
        self._at_wall: bool = False

    def prepare(self, maze_render) -> None:

        self._tile = maze_render.tile
        self._off_x = maze_render.off_x
        self._off_y = maze_render.off_y
        self._last_pos = None       # new maze: forget the old position
        self._gap_x = self._gap_y = 0.0
        self._reach = 0.0
        self._reach_dir = (0, 0)

        sheet = pygame.image.load(self.SHEET_PATH).convert_alpha()
        self._sheet = pygame.transform.smoothscale(
            sheet, (self.FRAMES * self._tile, 4 * self._tile)
        )

    def _smoothed_position(self, player, now_ms: int) -> tuple[float, float]:
        """Real position plus a gap that melts away (hides turn snaps)."""

        x, y = player._x, player._y             # entities.Entity floats

        dt = 0.0
        if self._last_ms is not None:
            dt = min((now_ms - self._last_ms) / 1000, self.MAX_DT_S)
        self._last_ms = now_ms

        moved = 0.0
        if self._last_pos is not None:
            dx = x - self._last_pos[0]
            dy = y - self._last_pos[1]
            moved = abs(dx) + abs(dy)
            normal_step = player._speed * dt

            if moved > self.TELEPORT_TILES:             # respawn
                self._gap_x = self._gap_y = 0.0
            elif moved > normal_step * 2 + 0.03:        # engine turn snap
                self._gap_x -= dx
                self._gap_y -= dy
        self._last_pos = (x, y)

        decay = math.exp(-dt / self.TURN_SMOOTH_S)
        self._gap_x *= decay
        self._gap_y *= decay

        reach_x, reach_y = self._wall_reach(player, x, y, dt, moved)
        return x + self._gap_x + reach_x, y + self._gap_y + reach_y

    def _wall_reach(self, player, x: float, y: float, dt: float,
                    moved: float) -> tuple[float, float]:
        """Slide the sprite forward to the wall the engine stopped short of."""

        d = player.cur_direction
        blocked = (d.dx, d.dy) in self.ROWS and not player.can_move(d)

        if not blocked:
            self._reach *= math.exp(-dt / 0.05)     # fade out quickly
            self._at_wall = False
            return (self._reach * self._reach_dir[0],
                    self._reach * self._reach_dir[1])

        self._reach_dir = (d.dx, d.dy)

        # distance from where he stopped to the middle of his tile, forward
        cx, cy = player.tile
        target = max(0.0, (cx - x) * d.dx + (cy - y) * d.dy)

        # only the part of this frame's travel he did not already move for real
        growth = max(0.0, player._speed * dt - moved)
        self._reach = min(target, self._reach + growth)
        self._at_wall = self._reach >= target - 1e-3
        return self._reach * d.dx, self._reach * d.dy

    def render(self, player) -> None:

        if self._sheet is None:
            return

        t = self._tile
        x, y = self._smoothed_position(player, pygame.time.get_ticks())

        # direction he is moving in; NONE (0, 0) means standing still
        direction = player.cur_direction
        moving = ((direction.dx, direction.dy) in self.ROWS
                  and not self._at_wall)
        if (direction.dx, direction.dy) in self.ROWS:
            self._row = self.ROWS[(direction.dx, direction.dy)]

        if moving:
            frame = (pygame.time.get_ticks()
                     * self._anm_fps // 1000) % self.FRAMES
        else:
            frame = self.IDLE_FRAME

        area = pygame.Rect(frame * t, self._row * t, t, t)
        self._screen.blit(
            self._sheet,
            (self._off_x + round(x * t), self._off_y + round(y * t)),
            area,
        )
