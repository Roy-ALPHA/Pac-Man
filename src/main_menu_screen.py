from ui.screen import Screen
from ui.inputhandler import InputCommand
import pygame


class MainMenuScreen(Screen):

    def __init__(self):

        self.images: dict[str, pygame.Surface] = {}
        self.image_positions: dict[str, tuple[int, int]] = {}
        self.button_rects: dict[str, pygame.Rect] = {}
        self.get_images()
        self.calculate_positions()
        self.create_hitboxes()

    def handle_input(self, command: InputCommand) -> None:

        mouse_coord = pygame.mouse.get_pos()

        if command.mouse_clicked and Screen.door_fully_close:

            if self.button_rects['quit'].collidepoint(mouse_coord):
                command.quit = True

            elif self.button_rects['play'].collidepoint(mouse_coord):
                command.play = True

    def update(self, dt: float) -> None:

        if Screen.door_w < 600:
            Screen.door_w += 900 * (dt / 1000)
        else:
            self.update_mouse_cursor()
            Screen.door_fully_close = True

    def render(self) -> None:

        Screen.renderer.clear()
        self.close_door()
        if Screen.door_fully_close:
            self.draw_ui_elements()

    def get_images(self) -> None:

        renderer = Screen.renderer
        self.images['logo'] = renderer.get_image('menu_logo.png')
        self.images['play'] = renderer.get_image('play_button.png')
        self.images['high'] = renderer.get_image('highscores_button.png')
        self.images['quit'] = renderer.get_image('quit_button.png')

    def calculate_positions(self) -> None:

        self.image_positions['logo'] = (Screen.screen_w // 2 - 400,
                                        Screen.screen_h // 2 - 300)
        self.image_positions['play'] = (Screen.screen_w // 2 - 60,
                                        Screen.screen_h // 2 - 100)
        self.image_positions['high'] = (Screen.screen_w // 2 - 105,
                                        Screen.screen_h // 2 - 20)
        self.image_positions['quit'] = (Screen.screen_w // 2 - 60,
                                        Screen.screen_h // 2 + 300)

    def close_door(self) -> None:

        Screen.renderer.draw_door(0, Screen.door_w)
        Screen.renderer.draw_door(Screen.screen_w - Screen.door_w,
                                  Screen.door_w)

    def draw_ui_elements(self) -> None:

        renderer = Screen.renderer
        renderer.blit_window(self.images['logo'], self.image_positions['logo'])
        renderer.blit_window(self.images['play'], self.image_positions['play'])
        renderer.blit_window(self.images['high'], self.image_positions['high'])
        renderer.blit_window(self.images['quit'], self.image_positions['quit'])

    def create_hitboxes(self) -> None:

        self.button_rects['play'] = pygame.Rect(
            self.image_positions['play'][0], self.image_positions['play'][1],
            self.images['play'].get_width(), self.images['play'].get_height())

        self.button_rects['high'] = pygame.Rect(
            self.image_positions['high'][0], self.image_positions['high'][1],
            self.images['high'].get_width(), self.images['high'].get_height())

        self.button_rects['quit'] = pygame.Rect(
            self.image_positions['quit'][0], self.image_positions['quit'][1],
            self.images['quit'].get_width(), self.images['quit'].get_height())

    def is_hovering_any_button(self, mouse_coord: tuple[int, int]) -> bool:
        return (self.button_rects['play'].collidepoint(mouse_coord) or
                self.button_rects['high'].collidepoint(mouse_coord) or
                self.button_rects['quit'].collidepoint(mouse_coord))

    def update_mouse_cursor(self) -> None:

        mouse_coord = pygame.mouse.get_pos()

        if self.is_hovering_any_button(mouse_coord):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
