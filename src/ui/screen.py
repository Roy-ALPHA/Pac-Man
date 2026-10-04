from abc import ABC, abstractmethod
from .inputhandler import InputCommand
from .renderer import Renderer


class Screen(ABC):

    door_w = 0
    door_fully_close = False
    screen_w = 0
    screen_h = 0
    renderer: None | Renderer = None

    @abstractmethod
    def handle_input(self, command: InputCommand) -> None:
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        pass

    @abstractmethod
    def render(self) -> None:
        pass
