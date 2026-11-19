from typing import Any
from ..data_dir import ASSETS_DIR
import pygame


class RenderPlayer:

    def __init__(self, screen: pygame.Surface):
        """
        Method that initialize all the attribute of the
        instance created from render player class
        """
        self._screen = screen
        self._path = ASSETS_DIR / "entities" / "pacman.png"
        self._rows = {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}
        self._frames = 8
        self._idle_frame = 3
        self._fps = 20

        self._sheet: pygame.Surface | None = None
        self._tile = 0
        self._off_x = 0
        self._off_y = 0
        self._row = 0

    def prepare(self, maze_render: Any) -> None:
        """
        Method that prepare the envirment
        to the player to be rendred
        """
        self._tile = maze_render.tile
        self._off_x = maze_render.off_x
        self._off_y = maze_render.off_y

        sheet = pygame.image.load(self._path)
        self._sheet = pygame.transform.scale(
            sheet, (self._frames * self._tile, 4 * self._tile))

    def render(self, player: Any) -> None:
        """
        Method that render the player using a sheet
        """
        if player.is_invincible and (pygame.time.get_ticks() // 150) % 2:
            return

        direction = player.cur_direction
        key = (direction.dx, direction.dy)

        if key in self._rows:
            self._row = self._rows[key]

        if key in self._rows and player.can_move(direction):
            ms = pygame.time.get_ticks()
            frame = (ms * self._fps // 1000) % self._frames
        else:
            frame = self._idle_frame

        t = self._tile
        x = self._off_x + round(player.x * t)
        y = self._off_y + round(player.y * t)
        area = pygame.Rect(frame * t, self._row * t, t, t)
        if self._sheet:
            self._screen.blit(self._sheet, (x, y), area)
