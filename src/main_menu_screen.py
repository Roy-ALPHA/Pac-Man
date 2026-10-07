from ui.screen import Screen
from ui.renderer import Renderer
from ui.inputhandler import InputCommand
import pygame


class MainMenuScreen(Screen):

    def __init__(self):

        self._keys = ['logo', 'play', 'high', 'instrcts', 'quit']
        self._imgs: dict[str, pygame.Surface] = {}
        self._hover_imgs: dict[str: pygame.Surface] = {}
        self._img_x_y: dict[str, tuple[int, int]] = {}
        self._button_rects: dict[str, pygame.Rect] = {}
        self._get_images()
        self._calculate_pos()
        self._create_hitboxes()

    def handle_input(self, command: InputCommand) -> None:

        mouse_coord = pygame.mouse.get_pos()

        if command.mouse_clicked and Screen.door_closed:

            if self._button_rects['quit'].collidepoint(mouse_coord):
                command.quit = True

            elif self._button_rects['play'].collidepoint(mouse_coord):
                command.play = True

    def update(self, dt: float) -> None:

        if Screen.door_w < 600:
            Screen.door_w += 900 * (dt / 1000)

        else:
            self._update_cursor()
            Screen.door_closed = True

    def render(self, render: Renderer) -> None:

        render.clear()
        self.close_door(render)

        if Screen.door_closed:
            self._draw_ui(render)

    def close_door(self, render: Renderer) -> None:

        render.draw_door(0, Screen.door_w)
        render.draw_door(Screen.screen_w - Screen.door_w, Screen.door_w)

    @staticmethod
    def _load_img(name: str) -> pygame.Surface:
        return pygame.image.load(f"assets/{name}")

    def _get_images(self) -> None:

        img_names = ['logo.png', 'play.png', 'high.png',
                     'instruction.png', 'quit.png']

        for key, name in zip(self._keys, img_names):
            self._imgs[key] = self._load_img(name)

        for key, name in zip(self._keys[1:], img_names[1:]):
            hover_name = name.replace('.png', '_hover.png')
            self._hover_imgs[key] = self._load_img(hover_name)

    def _calculate_pos(self) -> None:

        offsets = {
            'logo': (-405, -300),
            'play': (-55, -60),
            'high': (-120, 40),
            'instrcts': (-135, 150),
            'quit': (-60, 270)
        }

        for key in self._keys:
            offset_x, offset_y = offsets[key]
            self._img_x_y[key] = (
                self.middle_w + offset_x,
                self.middle_h + offset_y)

    def _is_hover(self, key: str) -> bool:
        
        mouse_coord = pygame.mouse.get_pos()
    
        return key != 'logo' and self._button_rects[key].collidepoint(mouse_coord)

    def _draw_ui(self, render: Renderer) -> None:

        for key in self._keys:
            if self._is_hover(key):
                render.blit_window(self._hover_imgs[key], self._img_x_y[key])
            else:
                render.blit_window(self._imgs[key], self._img_x_y[key])

    def _img_info(self, key: str, x_y_flag: bool = False) -> tuple[int, int]:

        if x_y_flag:
            return self._img_x_y[key]
        return (self._imgs[key].get_width(), self._imgs[key].get_height())

    def _create_hitboxes(self) -> None:

        for key in self._keys[1:]:
            x, y = self._img_info(key, True)
            w, h = self._img_info(key)
            self._button_rects[key] = pygame.Rect(x, y, w, h)

    def _hovering_button(self, mouse_coord: tuple[int, int]) -> bool:

        for key in self._keys[1:]:

            if self._button_rects[key].collidepoint(mouse_coord):
                return True

        return False

    def _update_cursor(self) -> None:

        mouse_coord = pygame.mouse.get_pos()

        if self._hovering_button(mouse_coord):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
