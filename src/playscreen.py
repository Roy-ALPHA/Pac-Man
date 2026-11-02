from src.ui.screen import Screen
from src.ui.renderer import Renderer
from src.ui.inputhandler import InputCommand
from .entities import Direction
from .config import Config
from .engine import GameEngine, EngineState, Cheat
from .highscore import HighscoreManager
import pygame


class PlayEngine(GameEngine):

    @property
    def is_level_loaded(self):
        return self._is_level_loaded

    @property
    def grid(self):
        return self._grid

    @property
    def pacman(self):
        return self._pacman

    @property
    def ghosts(self):
        return self._ghosts

    @property
    def lives(self):
        return self._pacman.lives

    @property
    def level(self):
        return self._cur_level

    @property
    def max_level(self):
        return 10

    @property
    def time_left(self):
        return max(0, self._level_time)


class PlayScreen(Screen):

    CHEATS = {1: Cheat.INVINCIBILITY, 2: Cheat.EXTRA_LIVES,
              3: Cheat.GHOST_FREEZE, 4: Cheat.INCREASE_SPEED,
              5: Cheat.LEVEL_SKIP}

    def __init__(self, config: Config, highscores: HighscoreManager) -> None:

        self._engine = PlayEngine(config)
        self._config = config
        self._highscores = highscores
        self._direction = Direction.NONE
        self._change_style = False
        self._paused = False
        self._cheats_on = False
        self._name = ""
        self._message = ""
        self._title_font = pygame.font.Font(None, 110)
        self._font = pygame.font.Font(None, 60)
        self._small_font = pygame.font.Font(None, 30)
        self._overlay = pygame.Surface((self.screen_w, self.screen_h))
        self._overlay.set_alpha(150)
        self._save_rect = self._make_rect(300, 70, 130)
        self._resume_rect = self._make_rect(500, 80, 0)
        self._menu_rect = self._make_rect(500, 80, 120)

    def handle_input(self, command: InputCommand) -> None:

        clicked = self._clicked_button(command)

        if self._game_ended():
            self._type_name(command)
            if clicked == "Save":
                self._save_score(command)
            return

        if command.pause:
            self._toggle_pause()

        if self._paused:
            if clicked == "Resume":
                self._toggle_pause()
            elif clicked == "Main Menu":
                command.back = True
            return

        if command.change_style:
            self._change_style = True
        
        if command.toggle_cheats:
            self._cheats_on = not self._cheats_on

        if command.cheat and self._cheats_on and self._engine.is_level_loaded:
            self._engine.activate_cheat(self.CHEATS[command.cheat])

        if command.direction is not Direction.NONE:
            self._direction = command.direction

    def update(self, dt: int) -> None:

        if Screen.door_w >= 0:
            Screen.door_w -= 1100 * (dt / 1000)

        self._engine.tick(dt / 1000, self._direction)

        mouse = pygame.mouse.get_pos()
        on_button = any(rect.collidepoint(mouse)
                        for rect in self._buttons().values())
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if on_button
                                else pygame.SYSTEM_CURSOR_ARROW)

    def _draw_cheat_status(self, render: Renderer) -> None:

        lines = []

        if self._cheats_on:
            lines.append("CHEATS ON")

        if self._engine.is_level_loaded:
            pacman = self._engine.pacman

            if pacman.is_invincible:
                lines.append("INVINCIBLE")
            if pacman.speed > self._config.pacman_speed:
                bonus = pacman.speed - self._config.pacman_speed
                lines.append(f"SPEED +{bonus:g}")
            if pacman.lives > self._config.lives:
                lines.append(f"EXTRA LIVES +{pacman.lives - self._config.lives}")
            if any(g.is_frozen for g in self._engine.ghosts):
                lines.append("GHOSTS FROZEN")

        for i, text in enumerate(lines):
            render.blit_window(
                self._small_font.render(text, True, 'red'),
                (self.screen_w - 190, self.screen_h - 40 - i * 30))
    
    def render(self, render: Renderer) -> None:

        render.clear()

        if self._engine.is_level_loaded:
            render.render_maze(self._engine.grid, self._change_style)
            render.render_entities(self._engine.pacman, self._engine.ghosts)
            render.render_hub(self._engine.score, self._engine.lives,
                              self._engine.level, self._engine.max_level,
                              self._engine.time_left)

        self._change_style = False

        if self._game_ended():
            self._draw_end_screen(render)
        elif self._paused:
            self._draw_pause_menu(render)

        self._draw_cheat_status(render)
        render.draw_door(0, Screen.door_w)
        render.draw_door(Screen.screen_w - Screen.door_w, Screen.door_w)

    def _make_rect(self, w: int, h: int, y_offset: int) -> pygame.Rect:
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (self.middle_w, self.middle_h + y_offset)
        return rect

    def _buttons(self) -> dict[str, pygame.Rect]:

        if self._game_ended():
            return {"Save": self._save_rect}
        if self._paused:
            return {"Resume": self._resume_rect,
                    "Main Menu": self._menu_rect}
        return {}

    def _clicked_button(self, command: InputCommand) -> str | None:

        if not command.mouse_clicked:
            return None

        mouse = pygame.mouse.get_pos()
        for text, rect in self._buttons().items():
            if rect.collidepoint(mouse):
                return text
        return None

    def _draw_buttons(self, render: Renderer) -> None:

        mouse = pygame.mouse.get_pos()

        for text, rect in self._buttons().items():
            hover = rect.collidepoint(mouse)

            button = pygame.Surface(rect.size)
            button.fill('yellow' if hover else 'blue')

            label = self._font.render(text, True,
                                      'black' if hover else 'white')
            button.blit(label, label.get_rect(
                center=(rect.w // 2, rect.h // 2)))

            render.blit_window(button, rect.topleft)

    def _toggle_pause(self) -> None:

        if self._paused:
            self._engine.resume()
        else:
            self._engine.stop()

        self._paused = not self._paused

    def _draw_pause_menu(self, render: Renderer) -> None:

        render.blit_window(self._overlay, (0, 0))
        self._draw_text(render, self._title_font, "PAUSED",
                        self.middle_h - 150, 'yellow')
        self._draw_buttons(render)

    def _game_ended(self) -> bool:
        return self._engine.state in (EngineState.GAME_OVER,
                                      EngineState.GAME_WON)

    def _type_name(self, command: InputCommand) -> None:

        command.back = False

        self._name += command.text

        if command.backspace:
            self._name = self._name[:-1]

    def _save_score(self, command: InputCommand) -> None:

        saved, message = self._highscores.save(self._name, self._engine.score)

        if saved:
            command.show_highscores = True
        else:
            self._message = message

    def _draw_end_screen(self, render: Renderer) -> None:

        render.blit_window(self._overlay, (0, 0))

        if self._engine.state is EngineState.GAME_WON:
            title, color, reason = "YOU WIN!", 'yellow', ""
        elif self._engine.lives <= 0:
            title, color, reason = "GAME OVER", 'red', "No lives left"
        else:
            title, color, reason = "GAME OVER", 'red', "Time is up"

        mid = self.middle_h
        self._draw_text(render, self._title_font, title, mid - 200, color)
        self._draw_text(render, self._font,
                        f"Score: {self._engine.score}", mid - 120, 'white')
        self._draw_text(render, self._small_font, reason, mid - 80, 'red')
        self._draw_text(render, self._font, "Enter your name:",
                        mid - 40, 'white')
        self._draw_text(render, self._font, self._name + "_",
                        mid + 30, 'yellow')
        self._draw_buttons(render)
        self._draw_text(render, self._small_font, self._message,
                        mid + 220, 'red')

    def _draw_text(self, render: Renderer, font: pygame.font.Font,
                   text: str, y: int, color: str) -> None:

        if not text:
            return

        image = font.render(text, True, color)
        render.blit_window(image, image.get_rect(
            center=(self.middle_w, y)).topleft)