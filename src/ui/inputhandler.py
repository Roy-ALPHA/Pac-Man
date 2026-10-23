from dataclasses import dataclass
from entities import Direction
import pygame


@dataclass
class InputCommand:

    direction: Direction = Direction.NONE
    change_style = False
    mouse_clicked: bool = False
    play: bool = False
    pause: bool = False
    quit: bool = False


class InputHandler:

    def handle_events(self) -> InputCommand:

        command: InputCommand = InputCommand()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                command.quit = True

            if event.type == pygame.KEYDOWN:

                if event.key in (pygame.K_UP, pygame.K_w):
                    command.direction = Direction.UP

                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    command.direction = Direction.DOWN

                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    command.direction = Direction.RIGHT

                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    command.direction = Direction.LEFT

                elif event.key is pygame.K_c:
                    command.change_style = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                command.mouse_clicked = True

        return command

    def clean(self) -> None:
        pygame.quit()
