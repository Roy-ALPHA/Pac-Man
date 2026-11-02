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

    def save(self):
        return self._save_states()

    def load(self):
        return self._load_states()

    def delete_save(self):
        (self._data_dir / "pacman_states.json").unlink(missing_ok=True)


class PlayScreen(Screen):

    CHEATS = {1: Cheat.INVINCIBILITY, 2: Cheat.EXTRA_LIVES,
              3: Cheat.GHOST_FREEZE, 4: Cheat.INCREASE_SPEED,
              5: Cheat.LEVEL_SKIP}

    def __init__(self, config: Config, highscores: HighscoreManager,
                 load: bool = False) -> None:

        self._engine = PlayEngine(config)
        self._config = config
        self._highscores = highscores

        self._direction = Direction.NONE
        self._change_style = False
        self._paused = False
        self._cheats_on = False
        self._save_cleared = False
        self._name = ""
        self._message = ""

        self._title_font = pygame.font.Font(None, 110)
        self._font = pygame.font.Font(None, 60)
        self._small_font = pygame.font.Font(None, 30)

        self._overlay = pygame.Surface((self.screen_w, self.screen_h))
        self._overlay.set_alpha(150)

        self._save_rect = self._make_rect(300, 70, 130)
        self._resume_rect = self._make_rect(500, 80, 0)
        self._save_game_rect = self._make_rect(500, 80, 100)
        self._menu_rect = self._make_rect(500, 80, 200)

        self.loaded = load and self._engine.load()
        if self.loaded:
            self._paused = self._engine.state is EngineState.STOPPED

    def handle_input(self, command: InputCommand) -> None:

        clicked = self._clicked_button(command)

        if self._game_ended():
            self._handle_end(command, clicked)
            return

        if command.pause:
            self._toggle_pause()

        if self._paused:
            self._handle_pause(command, clicked)
        else:
            self._handle_play(command)

    def _handle_play(self, command: InputCommand) -> None:

        if command.change_style:
            self._change_style = True

        if command.toggle_cheats:
            self._cheats_on = not self._cheats_on

        if command.cheat and self._cheats_on and self._engine.is_level_loaded:
            self._engine.activate_cheat(self.CHEATS[command.cheat])

        if command.direction is not Direction.NONE:
            self._direction = command.direction

    def _handle_pause(self, command: InputCommand, clicked: str | None) -> None:

        if clicked == "Resume":
            self._toggle_pause()
        elif clicked == "Save Game":
            saved = self.save_game()
            self._message = "Game saved" if saved else "Could not save the game"
        elif clicked == "Main Menu":
            command.back = True

    def _handle_end(self, command: InputCommand, clicked: str | None) -> None:

        command.back = False

        self._name += command.text
        if command.backspace:
            self._name = self._name[:-1]

        if clicked == "Save":
            saved, message = self._highscores.save(self._name,
                                                   self._engine.score)
            if saved:
                command.show_highscores = True
            else:
                self._message = message

    def update(self, dt: int) -> None:

        if self._game_ended() and not self._save_cleared:
            self._engine.delete_save()
            self._save_cleared = True

        if Screen.door_w >= 0:
            Screen.door_w -= 1100 * (dt / 1000)

        self._engine.tick(dt / 1000, self._direction)
        self._update_cursor()

    def _update_cursor(self) -> None:

        mouse = pygame.mouse.get_pos()
        on_button = any(rect.collidepoint(mouse)
                        for rect in self._buttons().values())
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if on_button
                                else pygame.SYSTEM_CURSOR_ARROW)

    def save_game(self) -> bool:

        if self._game_ended() or not self._engine.is_level_loaded:
            return False

        if self._paused:
            self._engine.resume()

        saved = self._engine.save()

        if self._paused:
            self._engine.stop()

        return saved

    def _toggle_pause(self) -> None:

        self._message = ""

        if self._paused:
            self._engine.resume()
        else:
            self._engine.stop()

        self._paused = not self._paused

    def _game_ended(self) -> bool:
        return self._engine.state in (EngineState.GAME_OVER,
                                      EngineState.GAME_WON)

    def _make_rect(self, w: int, h: int, y_offset: int) -> pygame.Rect:

        rect = pygame.Rect(0, 0, w, h)
        rect.center = (self.middle_w, self.middle_h + y_offset)
        return rect

    def _buttons(self) -> dict[str, pygame.Rect]:

        if self._game_ended():
            return {"Save": self._save_rect}

        if self._paused:
            return {"Resume": self._resume_rect,
                    "Save Game": self._save_game_rect,
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

    def render(self, render: Renderer) -> None:

        render.clear()

        if self._engine.is_level_loaded:
            self._draw_game(render)

        if self._game_ended():
            self._draw_end_screen(render)
        elif self._paused:
            self._draw_pause_menu(render)

        self._draw_cheat_status(render)

        render.draw_door(0, Screen.door_w)
        render.draw_door(Screen.screen_w - Screen.door_w, Screen.door_w)

    def _draw_game(self, render: Renderer) -> None:

        engine = self._engine

        render.render_maze(engine.grid, self._change_style)
        render.render_entities(engine.pacman, engine.ghosts)
        render.render_hub(engine.score, engine.lives, engine.level,
                          engine.max_level, engine.time_left)

        self._change_style = False

    def _draw_buttons(self, render: Renderer) -> None:

        mouse = pygame.mouse.get_pos()

        for text, rect in self._buttons().items():
            hover = rect.collidepoint(mouse)

            button = pygame.Surface(rect.size)
            button.fill('yellow' if hover else 'blue')
            render.blit_window(button, rect.topleft)

            render.draw_text(self._font, text, 'black' if hover else 'white',
                             rect.center)

    def _draw_pause_menu(self, render: Renderer) -> None:

        mid_w, mid_h = self.middle_w, self.middle_h

        render.blit_window(self._overlay, (0, 0))
        render.draw_text(self._title_font, "PAUSED", 'yellow',
                         (mid_w, mid_h - 150))
        self._draw_buttons(render)
        render.draw_text(self._small_font, self._message, 'yellow',
                         (mid_w, mid_h + 290))

    def _draw_end_screen(self, render: Renderer) -> None:

        if self._engine.state is EngineState.GAME_WON:
            title, color, reason = "YOU WIN!", 'yellow', ""
        elif self._engine.lives <= 0:
            title, color, reason = "GAME OVER", 'red', "No lives left"
        else:
            title, color, reason = "GAME OVER", 'red', "Time is up"

        mid_w, mid_h = self.middle_w, self.middle_h

        render.blit_window(self._overlay, (0, 0))
        render.draw_text(self._title_font, title, color, (mid_w, mid_h - 200))
        render.draw_text(self._font, f"Score: {self._engine.score}", 'white',
                         (mid_w, mid_h - 120))
        render.draw_text(self._small_font, reason, 'red', (mid_w, mid_h - 80))
        render.draw_text(self._font, "Enter your name:", 'white',
                         (mid_w, mid_h - 40))
        render.draw_text(self._font, self._name + "_", 'yellow',
                         (mid_w, mid_h + 30))
        self._draw_buttons(render)
        render.draw_text(self._small_font, self._message, 'red',
                         (mid_w, mid_h + 220))

    def _draw_cheat_status(self, render: Renderer) -> None:

        for i, text in enumerate(self._cheat_lines()):
            render.draw_text(self._small_font, text, 'red',
                             (self.screen_w - 190,
                              self.screen_h - 40 - i * 30), center=False)

    def _cheat_lines(self) -> list[str]:

        lines = []

        if self._cheats_on:
            lines.append("CHEATS ON")

        if not self._engine.is_level_loaded:
            return lines

        pacman = self._engine.pacman
        extra_speed = pacman.speed - self._config.pacman_speed
        extra_lives = pacman.lives - self._config.lives

        if pacman.is_invincible:
            lines.append("INVINCIBLE")
        if extra_speed > 0:
            lines.append(f"SPEED +{extra_speed:g}")
        if extra_lives > 0:
            lines.append(f"EXTRA LIVES +{extra_lives}")
        if any(ghost.is_frozen for ghost in self._engine.ghosts):
            lines.append("GHOSTS FROZEN")

        return lines