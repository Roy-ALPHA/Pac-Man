from src.ui.screen import Screen
from src.ui.renderer import Renderer
from src.ui.inputhandler import InputCommand
import pygame


class MainMenuScreen(Screen):

    BUTTONS = {
        'play': ('play.png', -90, 'play'),
        'resume': ('resume.png', 10, 'continue_game'),
        'high': ('high.png', 110, 'show_highscores'),
        'instrcts': ('instruction.png', 210, 'show_instructions'),
        'quit': ('quit.png', 310, 'quit'),
    }

    def __init__(self) -> None:

        self._logo = self._load_img("main_mn/logo.png")
        self._logo_pos = (self.middle_w - 405, self.middle_h - 300)

        self.can_continue = False  # set by GameStateManager
        self._font = pygame.font.Font(None, 50)
        self._continue_rect = pygame.Rect(20, self.screen_h - 70, 260, 50)

        self._font = pygame.font.Font(None, 50)
        self._message = ""
        self._message_time = 0.0

        self._buttons: dict[str, tuple] = {}

        for key, (file, y_offset, _) in self.BUTTONS.items():
            image = self._load_img(f"main_mn/{file}")
            hover = self._load_img("main_mn/"
                                   f"{file.replace('.png', '_hover.png')}")
            rect = image.get_rect(midtop=(self.middle_w,
                                          self.middle_h + y_offset))
            self._buttons[key] = (image, hover, rect)

    def show_message(self, text: str) -> None:
        """Show a short message for 2 seconds."""
        self._message = text
        self._message_time = 2000

    def handle_input(self, command: InputCommand) -> None:

        if command.mouse_clicked and Screen.door_closed:
            if (self.can_continue and
                    self._continue_rect.collidepoint(pygame.mouse.get_pos())):
                command.continue_game = True
                return
            key = self._hovered()

            if key:
                setattr(command, self.BUTTONS[key][2], True)

    def update(self, dt: float) -> None:

        self._message_time -= dt

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

        if self.can_continue:
            hover = self._continue_rect.collidepoint(pygame.mouse.get_pos())
            color = 'white' if hover else 'yellow'
            render.blit_window(self._font.render("Continue", True, color),
                               self._continue_rect.topleft)

        if self._message_time > 0:
            text = self._font.render(self._message, True, 'red')
            render.blit_window(text, text.get_rect(
                center=(self.middle_w, self.screen_h - 30)).topleft)

    def _hovered(self) -> str | None:
        """Name of the button under the mouse, or None."""

        mouse_coord = pygame.mouse.get_pos()

        for key, (_, _, rect) in self._buttons.items():
            if rect.collidepoint(mouse_coord):
                return key

        return None
