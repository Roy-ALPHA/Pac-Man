from src.ui.screen import Screen
from src.ui.renderer import Renderer
from src.ui.inputhandler import InputCommand
import pygame


class MainMenuScreen(Screen):

    """Class Responsible about rendring the screen of main menu and load
    all its images
    """
    BUTTONS = {
        'play': ('play.png', -90, 'play'),
        'resume': ('resume.png', 10, 'continue_game'),
        'high': ('high.png', 110, 'show_highscores'),
        'instrcts': ('instruction.png', 210, 'show_instructions'),
        'quit': ('quit.png', 310, 'quit'),
    }

    def __init__(self) -> None:

        """
        Method that initialize all the attribute of the instance created
        by this class
        """
        self._logo = self._load_img("main_mn/logo.png")
        self._logo_pos = (self.middle_w - 405, self.middle_h - 300)

        self._font = pygame.font.Font(None, 50)
        self.time_to_appear = 0

        self._buttons: dict[str, tuple] = {}

        for key, (file, y_offset, _) in self.BUTTONS.items():
            image = self._load_img(f"main_mn/{file}")
            hover = self._load_img("main_mn/"
                                   f"{file.replace('.png', '_hover.png')}")
            rect = image.get_rect(midtop=(self.middle_w,
                                          self.middle_h + y_offset))
            self._buttons[key] = (image, hover, rect)

    def handle_input(self, command: InputCommand) -> None:

        """
        This method check if the mouse is clicked and see which image
        is hoved and then set the flag of the hovred and clicked image to true
        so we rotate the screen to the clicked screen.
        """
        if command.mouse_clicked and Screen.door_closed:
            key = self._hovered()

            if key:
                setattr(command, self.BUTTONS[key][2], True)

    def update(self, dt: float) -> None:

        """
        This method update if there is a message to appear it decrease it time
        also is change the mouse hand if its on a specifique image.
        """
        self.time_to_appear -= dt

        if Screen.door_w < 600:
            Screen.door_w += 900 * (dt / 1000)
            return

        Screen.door_closed = True

        if self._hovered():
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def render(self, render: Renderer) -> None:
        
        """This method is responsible about rendering to the window
        all images.
        """
        render.clear()

        render.draw_door(0, Screen.door_w)
        render.draw_door(Screen.screen_w - Screen.door_w, Screen.door_w)

        if not Screen.door_closed:
            return

        render.blit_window(self._logo, self._logo_pos)

        hovered = self._hovered()
        for key, (image, hover, rect) in self._buttons.items():
            render.blit_window(hover if key == hovered else image,
                               rect)
        if self.time_to_appear > 0:
            text = self._font.render("No Game To Resume", True, 'red')
            render.blit_window(text, text.get_rect(
                center=(self.middle_w, 50)))

    def _hovered(self) -> str | None:

        """This method check if the mouse hand is on a image if yes it return the
        key of that image.
        """
        mouse_coord = pygame.mouse.get_pos()

        for key, (_, _, rect) in self._buttons.items():
            if rect.collidepoint(mouse_coord):
                return key

        return None
