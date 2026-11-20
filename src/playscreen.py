from typing import Any
from src.ui.screen import Screen
from src.ui.renderer import Renderer
from src.ui.inputhandler import InputCommand
from .entities import Direction
from .config import Config
from .engine import GameEngine, EngineState, Cheat
from .highscore import HighscoreManager
from .maze_adapter import MazeAdapter
from .data_dir import DATA_DIR
import pygame


class PlayEngine(GameEngine):

    """
    Class Used to act as the engine and retune all the data that
    we need from it and use its method.
    """
    @property
    def is_level_loaded(self) -> bool:
        """
        Method that check if the level loaded
        """
        return bool(self._is_level_loaded)

    @property
    def grid(self) -> Any:
        """
        Method that retune the grid
        """
        return self._grid

    @property
    def pacman(self) -> Any:
        """
        Method that return the pacman
        """
        return self._pacman

    @property
    def ghosts(self) -> Any:
        """
        Method that return the ghosts
        """
        return self._ghosts

    @property
    def lives(self) -> Any:
        """
        Method that return the lifes left for pacman
        """
        return self._pacman.lives

    @property
    def level(self) -> Any:
        """
        Method that return the current level
        """
        return self._cur_level

    @property
    def max_level(self) -> int:
        """
        Method that return  the max level for the game
        """
        return 10

    @property
    def time_left(self) -> Any:
        """
        Method that return  the time left for the game
        """
        return max(0, self._level_time)

    def save(self) -> bool:
        """
        Method  that check if the game saved successfuly
        """
        return self._save_states()

    def load_to_resume(self) -> bool:
        """
        Method that check check if the previous game state
        loaded succesfully
        """
        return self._load_states()

    def delete_save(self) -> None:
        """
        Method that delete if there is a saved game if it reach the end
        """
        (DATA_DIR / "pacman_states.json").unlink(missing_ok=True)


class PlayScreen(Screen):

    """
    Class that is responsible about the game rendering
    """
    PAUSE_BUTTON = "Pause (P)"
    RESTART_BUTTON = "Restart (R)"
    CHEATS_BUTTON = "Cheats (F1)"

    CHEATS = {"1 Invincible": Cheat.INVINCIBILITY,
              "2 Extra life": Cheat.EXTRA_LIVES,
              "3 Freeze ghosts": Cheat.GHOST_FREEZE,
              "4 Speed up": Cheat.INCREASE_SPEED,
              "5 Skip level": Cheat.LEVEL_SKIP}

    ONE_SHOT = (Cheat.EXTRA_LIVES, Cheat.LEVEL_SKIP)
    FLASH_MS = 400

    QUESTIONS = {"quit": "Save your game before closing?",
                 "restart": "Restart the game?"}

    def __init__(self, config: Config, highscores: HighscoreManager,
                 load_to_resume: bool = False) -> None:

        """
        Method that initialize all the attribute of the instance created
        from playscreen class
        """
        self._engine = PlayEngine(config)
        self._config = config
        self._highscores = highscores
        self._change_style = False
        self._reset_state()

        self._title_font = pygame.font.Font(None, 110)
        self._font = pygame.font.Font(None, 60)
        self._small_font = pygame.font.Font(None, 30)
        self._hub_font = pygame.font.Font(None, 26)

        self._overlay = pygame.Surface((self.screen_w, self.screen_h))
        self._overlay.set_alpha(150)
        self._panel = pygame.Surface((800, 300))
        self._panel.fill((10, 10, 50))

        self._save_rect = self._make_rect(300, 70, 130)
        self._resume_rect = self._make_rect(500, 80, 0)
        self._save_game_rect = self._make_rect(500, 80, 100)
        self._menu_rect = self._make_rect(500, 80, 200)
        self._yes_rect = self._make_rect(220, 80, 40, -150)
        self._no_rect = self._make_rect(220, 80, 40, 150)

        x = self.screen_w - Renderer.HUD_WIDTH + 20
        self._pause_rect = pygame.Rect(x, 410, 160, 40)
        self._restart_rect = pygame.Rect(x, 455, 160, 40)
        self._cheats_rect = pygame.Rect(x, 500, 160, 40)
        self._cheat_rects = {name: pygame.Rect(x, 550 + i * 42, 160, 36)
                             for i, name in enumerate(self.CHEATS)}

        self.loaded = load_to_resume and self._engine.load_to_resume()
        if self.loaded:
            self._owns_save = True
            self._paused = self._engine.state is EngineState.STOPPED

    def _reset_state(self) -> None:

        """
        Method that reset the state in the case
        if the user want to restart the game
        """
        self._direction = Direction.NONE
        self._paused = False
        self._question: str | None = None
        self._cheats_on = False
        self._save_cleared = False
        self._owns_save = False
        self._flash: dict[str, float] = {}
        self._name = ""
        self._message = ""

    def _mode(self) -> str:
        """
        Method that check the current
        stat of the game and return str refering
        to the active state
        """
        if self._question:
            return "question"
        if self._game_ended():
            return "end"
        if self._paused:
            return "pause"
        return "play"

    def _game_ended(self) -> bool:

        """
        Method that check if the current
        game if it reach the end
        """
        return self._engine.state in (EngineState.GAME_OVER,
                                      EngineState.GAME_WON)

    def _game_in_progress(self) -> bool:

        """
        Method that check if the game still in
        progress or it end
        """
        return self._engine.is_level_loaded and not self._game_ended()

    def handle_input(self, command: InputCommand) -> None:

        """
        Method that handle the user input
        """
        clicked = self._clicked_button(command)

        if command.quit and self._game_in_progress():
            command.quit = False
            self._start_question("quit")

        mode = self._mode()

        if mode == "question":
            self._handle_question(command, clicked)
        elif mode == "end":
            self._handle_end(command, clicked)
        elif mode == "pause":
            self._handle_pause(command, clicked)
        else:
            self._handle_play(command, clicked)

    def _handle_play(self, command: InputCommand, clicked: str | None) -> None:

        """
        Method that handle all input during normal gameplay
        in short it routes every player action during
        gameplay to the right response.
        """
        wants_restart = command.restart or clicked == self.RESTART_BUTTON
        if wants_restart and self._engine.is_level_loaded:
            self._start_question("restart")
            return

        if command.pause or clicked == self.PAUSE_BUTTON:
            self._toggle_pause()
            return

        if command.change_style:
            self._change_style = True

        if command.toggle_cheats or clicked == self.CHEATS_BUTTON:
            self._cheats_on = not self._cheats_on

        name: str | None = None
        if command.cheat:
            name = list(self.CHEATS)[command.cheat - 1]
        elif clicked is not None and clicked in self.CHEATS:
            name = clicked

        if name and self._cheats_on and self._engine.is_level_loaded:
            self._use_cheat(name)

        if command.direction is not Direction.NONE:
            self._direction = command.direction

    def _use_cheat(self, name: str) -> None:
        """
        Method that activate the cheat and use the flash
        for timr self.FLASH_MS
        """
        cheat = self.CHEATS[name]
        self._engine.activate_cheat(cheat)

        if cheat in self.ONE_SHOT:
            self._flash[name] = self.FLASH_MS

    def _handle_pause(self, command: InputCommand,
                      clicked: str | None) -> None:

        """
        Method that handle the pause screen
        """
        if command.restart and self._engine.is_level_loaded:
            self._start_question("restart")
            return

        if command.pause or clicked == "Resume":
            self._toggle_pause()
        elif clicked == "Save Game":
            saved = self.save_game()
            self._message = "Game saved" if saved else "Could not save"
        elif clicked == "Main Menu":
            command.back = True

    def _handle_question(self, command: InputCommand,
                         clicked: str | None) -> None:

        """
        Method that handle the question
        """
        if self._question == "restart":
            if clicked == "Yes":
                self._restart_game()
            elif clicked == "No":
                self._close_question()

        elif clicked == "Yes":
            if self.save_game():
                command.quit = True
            else:
                self._message = "Could not save the game"
        elif clicked == "No":
            command.quit = True

    def _handle_end(self, command: InputCommand, clicked: str | None) -> None:

        """
        Method that handle the end of the game
        """
        command.back = False

        if command.backspace:
            self._name = self._name[:-1]
        else:
            self._name += command.lettre

        if clicked == "Save":
            saved, message = self._highscores.save(self._name,
                                                   self._engine.score)
            if saved:
                command.show_highscores = True
            else:
                self._message = message

    def update(self, dt: float) -> None:

        """
        Method that update the state of the game during
        the game.
        """
        if self._game_ended() and not self._save_cleared:
            if self._owns_save:
                self._engine.delete_save()
            self._save_cleared = True

        self._flash = {name: left - dt for name, left in self._flash.items()
                       if left - dt > 0}

        if Screen.door_w >= 0:
            Screen.door_w -= 1100 * (dt / 1000)

        self._engine.tick(dt / 1000, self._direction)

    def save_game(self) -> bool:

        """
        Method that save the state of the game when the user
        ask for it
        """
        if not self._game_in_progress():
            return False

        if self._paused:
            self._engine.resume()

        saved = self._engine.save()

        if self._paused:
            self._engine.stop()

        if saved:
            self._owns_save = True

        return saved

    def _toggle_pause(self) -> None:

        """
        Method that switch between pause screen
        and play screen
        """
        self._message = ""

        if self._paused:
            self._engine.resume()
        else:
            self._engine.stop()

        self._paused = not self._paused

    def _restart_game(self) -> None:

        """
        Method that restart the game by creating new maze and
        and new engine then rested the previous state to default.
        """
        MazeAdapter.set_maze_size((self._config.width, self._config.height))
        self._engine = PlayEngine(self._config)
        self._reset_state()

    def _start_question(self, kind: str) -> None:

        """
        Method that set up the envirement
        for the specifique dialogue to be rendered
        """
        if self._question == "quit":
            return

        if self._question is None:
            if not self._paused:
                self._toggle_pause()

        self._question = kind
        self._message = ""

    def _close_question(self) -> None:

        """
        Method that close the dialog
        and clear the message and switch to play screen
        using toggle
        """
        self._question = None
        self._message = ""
        self._toggle_pause()

    def _make_rect(self, w: int, h: int, y_offset: int,
                   x_offset: int = 0) -> pygame.Rect:

        """
        Method that creat all buttons
        """
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (self.middle_w + x_offset, self.middle_h + y_offset)
        return rect

    def _hub_buttons(self) -> dict[str, pygame.Rect]:

        """
        Method that create all the hub buttons
        """
        buttons = {self.PAUSE_BUTTON: self._pause_rect,
                   self.RESTART_BUTTON: self._restart_rect,
                   self.CHEATS_BUTTON: self._cheats_rect}

        if self._cheats_on:
            buttons.update(self._cheat_rects)

        return buttons

    def _buttons(self) -> dict[str, pygame.Rect]:

        """
        Method that retunr the button to use depend on the current
        mode
        """
        mode = self._mode()

        if mode == "question":
            return {"Yes": self._yes_rect, "No": self._no_rect}
        if mode == "end":
            return {"Save": self._save_rect}
        if mode == "pause":
            return {"Resume": self._resume_rect,
                    "Save Game": self._save_game_rect,
                    "Main Menu": self._menu_rect}

        return self._hub_buttons()

    def _clicked_button(self, command: InputCommand) -> str | None:

        """
        Method that check which button was clicked
        """
        if not command.mouse_clicked:
            return None

        mouse = pygame.mouse.get_pos()
        for text, rect in self._buttons().items():
            if rect.collidepoint(mouse):
                return text

        return None

    def _is_on(self, text: str) -> bool:

        """
        Method that tell which button should be highlightd to
        green color
        """
        if text in self._flash:
            return True

        if text == self.CHEATS_BUTTON:
            return self._cheats_on

        if text not in self.CHEATS or not self._engine.is_level_loaded:
            return False

        cheat = self.CHEATS[text]
        pacman = self._engine.pacman

        if cheat is Cheat.INVINCIBILITY:
            return bool(pacman.is_invincible)
        if cheat is Cheat.INCREASE_SPEED:
            effects = pacman.get_effects_state()
            return "SPEED_BUFF" in effects and effects["SPEED_BUFF"] is None
        if cheat is Cheat.GHOST_FREEZE:
            return any(ghost.is_frozen for ghost in self._engine.ghosts)

        return False

    def render(self, render: Renderer) -> None:

        """
        Method that manage the rendring and the draw on the
        screen
        """
        render.clear()

        if self._engine.is_level_loaded:
            self._draw_game(render)

        mode = self._mode()

        if mode == "question":
            self._draw_question(render)
        elif mode == "end":
            self._draw_end_screen(render)
        elif mode == "pause":
            self._draw_pause_menu(render)

        if Screen.door_w > 0:
            render.draw_door(0, Screen.door_w)
            render.draw_door(Screen.screen_w - Screen.door_w, Screen.door_w)

    def _draw_game(self, render: Renderer) -> None:

        """
        Method that draw the game (maze, entities, hub ...)
        """
        engine = self._engine

        render.render_maze(engine.grid, self._change_style)
        render.render_entities(engine.pacman, engine.ghosts)
        render.render_hub(engine.score, engine.lives, engine.level,
                          engine.max_level, engine.time_left)

        self._draw_buttons(render, self._hub_buttons(), self._hub_font,
                           can_click=self._mode() == "play")

        self._change_style = False

    def _draw_buttons(self, render: Renderer, buttons: dict[str, pygame.Rect],
                      font: pygame.font.Font, can_click: bool = True) -> None:

        """
        Method that draw buttons
        """
        mouse = pygame.mouse.get_pos()

        for text, rect in buttons.items():
            hover = (can_click and rect.collidepoint(mouse)
                     and text not in self._flash)

            if hover:
                color = 'yellow'
            elif self._is_on(text):
                color = 'green'
            else:
                color = 'blue'

            button = pygame.Surface(rect.size)
            button.fill(color)
            render.blit_window(button, rect.topleft)

            text_color = 'white' if color == 'blue' else 'black'
            render.draw_text(font, text, text_color, rect.center)

    def _draw_question(self, render: Renderer) -> None:

        """
        Method that draw the dialog
        """
        question = self._question
        if question is None:
            return

        mid_w, mid_h = self.middle_w, self.middle_h

        render.blit_window(self._overlay, (0, 0))
        render.blit_window(self._panel,
                           self._panel.get_rect(center=(mid_w, mid_h)).topleft)
        render.draw_text(self._font, self.QUESTIONS[question],
                         'white', (mid_w, mid_h - 60))
        self._draw_buttons(render, self._buttons(), self._font)
        render.draw_text(self._small_font, self._message, 'red',
                         (mid_w, mid_h + 120))

    def _draw_pause_menu(self, render: Renderer) -> None:

        """
        Method that draw the pause screen
        """
        mid_w, mid_h = self.middle_w, self.middle_h

        render.blit_window(self._overlay, (0, 0))
        render.draw_text(self._title_font, "PAUSED", 'yellow',
                         (mid_w, mid_h - 150))
        self._draw_buttons(render, self._buttons(), self._font)
        render.draw_text(self._small_font, self._message, 'yellow',
                         (mid_w, mid_h + 290))

    def _draw_end_screen(self, render: Renderer) -> None:

        """
        Method that draw the end screen
        """
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
        self._draw_buttons(render, self._buttons(), self._font)
        render.draw_text(self._small_font, self._message, 'red',
                         (mid_w, mid_h + 220))
