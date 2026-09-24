from abc import ABC, abstractmethod
from inputhandler import InputCommand
from renderer import Renderer


class Screen(ABC):

    @abstractmethod
    def handle_input(self, command: InputCommand) -> None:
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        pass

    @abstractmethod
    def render(self, renderer: Renderer) -> None:
        pass
