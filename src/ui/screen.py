from abc import ABC, abstractmethod
from .inputhandler import InputCommand
from .renderer import Renderer


class Screen(ABC):

    door_w = 0
    screen_w = 0
    screen_h = 0
    door_closed = False

    @property
    def middle_w(self) -> int:
        return self.screen_w // 2

    @property
    def middle_h(self) -> int:
        return self.screen_h // 2

    @abstractmethod
    def handle_input(self, command: InputCommand) -> None:
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        pass

    @abstractmethod
    def render(self, render: Renderer) -> None:
        pass
