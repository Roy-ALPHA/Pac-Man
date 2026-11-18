from dataclasses import dataclass
from ..entities import Direction
import pygame


@dataclass
class InputCommand:

    """This class create and object with the default value
    each value is used for a specifique screen of feature
    """
    direction: Direction = Direction.NONE
    change_style: bool = False
    mouse_clicked: bool = False
    play: bool = False
    pause: bool = False
    restart: bool = False
    back: bool = False
    quit: bool = False
    show_highscores: bool = False
    show_instructions: bool = False
    continue_game: bool = False
    toggle_cheats: bool = False
    cheat: int = 0
    backspace: bool = False
    lettre: str = ""


class InputHandler:

    """This class Handle the user input and Translate it to
    input commande class.

    """
    CHEAT_KEYS = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3,
              pygame.K_4: 4, pygame.K_5: 5}

    def handle_events(self) -> InputCommand:

        """This method is the responsebile about translanting the user
        input to input commande.
        """
        command = InputCommand()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                command.quit = True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                command.mouse_clicked = True

            if event.type != pygame.KEYDOWN:
                continue

            if event.key in (pygame.K_UP, pygame.K_w):
                command.direction = Direction.UP
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                command.direction = Direction.DOWN
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                command.direction = Direction.RIGHT
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                command.direction = Direction.LEFT
            elif event.key == pygame.K_c:
                command.change_style = True
            elif event.key in (pygame.K_SPACE, pygame.K_p):
                command.pause = True
            elif event.key == pygame.K_r:
                command.restart = True
            elif event.key == pygame.K_F1:
                command.toggle_cheats = True
            elif event.key in InputHandler.CHEAT_KEYS:
                command.cheat = InputHandler.CHEAT_KEYS[event.key]
            elif event.key == pygame.K_BACKSPACE:
                command.backspace = True

            command.lettre += event.unicode

        return command

    def clean(self) -> None:
        """
        This methode clean the ressources of pygame.
        """
        pygame.quit()
