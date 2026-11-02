from src.ui.screen import Screen
from src.ui.renderer import Renderer
from src.ui.inputhandler import InputCommand
import pygame


class MainMenuScreen(Screen):

    BUTTONS = {
        'play': ('play.png', (-55, -60), 'play'),
        'high': ('high.png', (-120, 40), 'show_highscores'),
        'instrcts': ('instruction.png', (-135, 150), 'show_instructions'),
        'quit': ('quit.png', (-60, 270), 'quit'),
    }

    def __init__(self) -> None:

        self._logo = self._load_img("main_mn/logo.png")
        self._logo_pos = (self.middle_w - 405, self.middle_h - 300)

        self._buttons: dict[str, tuple] = {}

        for key, (file, (off_x, off_y), _) in self.BUTTONS.items():
            image = self._load_img(f"main_mn/{file}")
            hover = self._load_img(f"main_mn/{file.replace('.png', '_hover.png')}")
            rect = image.get_rect(topleft=(self.middle_w + off_x,
                                           self.middle_h + off_y))
            self._buttons[key] = (image, hover, rect)

    def handle_input(self, command: InputCommand) -> None:

        if command.mouse_clicked and Screen.door_closed:
            key = self._hovered()

            if key:
                flag = self.BUTTONS[key][2]
                setattr(command, flag, True)

    def update(self, dt: float) -> None:

        if Screen.door_w < 600:
            Screen.door_w += 900 * (dt / 1000)
            return

        Screen.door_closed = True

        if self._hovered():
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def render(self, render: Renderer) -> None:

        render.clear()

        render.draw_door(0, Screen.door_w)
        render.draw_door(Screen.screen_w - Screen.door_w, Screen.door_w)

        if not Screen.door_closed:
            return

        render.blit_window(self._logo, self._logo_pos)

        hovered = self._hovered()
        for key, (image, hover, rect) in self._buttons.items():
            render.blit_window(hover if key == hovered else image,
                               rect.topleft)

    def _hovered(self) -> str | None:

        mouse_coord = pygame.mouse.get_pos()

        for key, (_, _, rect) in self._buttons.items():
            if rect.collidepoint(mouse_coord):
                return key

        return None