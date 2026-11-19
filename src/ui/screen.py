from abc import ABC, abstractmethod
from .inputhandler import InputCommand
from ..data_dir import ASSETS_DIR
from .renderer import Renderer
import pygame


class Screen(ABC):

    """
    Parent class for all the screen that i use for this game
    """
    door_w = 0.0
    screen_w = 0
    screen_h = 0
    door_closed = False

    @property
    def middle_w(self) -> int:
        """
        Method that return the middle of the window
        """
        return self.screen_w // 2

    @property
    def middle_h(self) -> int:
        """
        Method that return the middle of the window
        """
        return self.screen_h // 2

    @staticmethod
    def _load_img(path: str) -> pygame.Surface:
        """
        Method that load the image
        """
        return pygame.image.load(ASSETS_DIR / path)

    @abstractmethod
    def handle_input(self, command: InputCommand) -> None:
        """
        Method that each screen must use to handle input
        """
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Method that each screen must use to update the calculations
        """
        pass

    @abstractmethod
    def render(self, render: Renderer) -> None:
        """
        Method that each screen must use to render to the screen
        """
        pass
