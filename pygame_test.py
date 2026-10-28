#!/usr/bin/env python3
"""
Pygame Visual Test Harness for the Pac-Man Engine & Backend.
Provides a comprehensive GUI test bench with:
- Full real-time player & ghost movement controls
- Live Engine state inspection & frame-by-frame stepping
- Simulation speed control (0.25x to 10.0x)
- All 5 official 42 cheats (Invincible, Level Skip, Freeze, Extra Lives, Speed)
- Diagnostic triggers (Force Frighten, Kill Pac-Man, Drain Timer, Jump Level, Clear Pellets)
- Ghost AI target tile visualization & path inspection
- Quick-Save & Quick-Load state serialization testing
- Persistent Highscore leaderboard overlay
- Hover inspector for tile coordinates & contents
"""

import math
import os
from pathlib import Path
import sys
import time
from typing import Dict, List, Optional, Tuple

import pygame

from src.config import Config
from src.engine import GameEngine, EngineState, Cheat
from src.entities import Direction, GhostState
from src.consumables import Consumable, SuperPacGum, PacGum
from src.highscore import HighscoreManager
from src.errors import setup_warnings

setup_warnings()

# ==============================================================================
# Color Palette & Visual Theme
# ==============================================================================
COLOR_BG = (10, 12, 18)
COLOR_PANEL_BG = (18, 22, 34)
COLOR_PANEL_BORDER = (45, 55, 80)
COLOR_PANEL_HEADER = (26, 32, 48)

COLOR_WALL_FILL = (18, 24, 70)
COLOR_WALL_OUTLINE = (38, 70, 220)
COLOR_CORRIDOR = (6, 8, 12)

COLOR_PELLET = (255, 225, 180)
COLOR_SUPER_PELLET = (255, 180, 80)
COLOR_ENTRY = (40, 200, 90)
COLOR_EXIT = (40, 210, 255)

COLOR_PACMAN = (255, 238, 0)
COLOR_PACMAN_INVINCIBLE = (255, 215, 0)

GHOST_COLORS: Dict[str, Tuple[int, int, int]] = {
    "Blinky": (255, 45, 45),
    "Pinky": (255, 160, 215),
    "Inky": (0, 230, 255),
    "Clyde": (255, 175, 45),
}

COLOR_FRIGHTENED_BLUE = (38, 75, 255)
COLOR_FRIGHTENED_WHITE = (245, 245, 255)
COLOR_FROZEN = (160, 230, 255)

STATE_COLORS = {
    EngineState.PLAYING: (60, 220, 100),
    EngineState.RESPAWNING: (255, 210, 50),
    EngineState.STOPPED: (170, 180, 210),
    EngineState.GAME_OVER: (255, 60, 60),
    EngineState.GAME_WON: (255, 215, 0),
}


class PygameTestHarness:
    """Complete interactive visual test harness for GameEngine & backend features."""

    def __init__(self, config_path: str = "config.json") -> None:
        pygame.init()
        pygame.display.set_caption("Pac-Man Engine & Backend Feature Test Harness")

        self.clock = pygame.time.Clock()
        self.config_path = Path(config_path)
        self.config = Config.from_file(self.config_path)

        # Highscores manager
        highscore_path = Path(getattr(self.config, "highscore_filename", "highscores.json"))
        self.highscore_mgr = HighscoreManager(highscore_path)

        # Fonts
        self.font_title = pygame.font.Font(None, 24)
        self.font_main = pygame.font.Font(None, 20)
        self.font_small = pygame.font.Font(None, 16)
        self.font_banner = pygame.font.Font(None, 44)

        # Engine reference
        self.engine: GameEngine = None  # type: ignore
        self.current_dir = Direction.NONE
        self.total_pellets = 0

        # UI & Debug states
        self.show_debug_overlay = False
        self.show_highscores_modal = False
        self.toast_message = ""
        self.toast_timer = 0.0

        # Simulation Speed Multipliers (0.25x to 10.0x)
        self.speed_options = [0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
        self.speed_index = 2  # default 1.0x
        self.step_one_frame = False

        # Initialize engine
        self.reset_engine()

        # Layout metrics
        self.sidebar_width = 380
        self.hud_height = 60
        self.margin = 16

        # Calculate optimal tile size
        max_maze_w = 820
        max_maze_h = 720
        self.tile_size = max(
            16,
            min(34, max_maze_w // self.grid.width, max_maze_h // self.grid.height),
        )

        self.maze_width = self.grid.width * self.tile_size
        self.maze_height = self.grid.height * self.tile_size

        self.screen_width = self.maze_width + self.sidebar_width + self.margin * 3
        self.screen_height = max(self.maze_height + self.hud_height + self.margin * 2, 700)

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.is_running = True

    @property
    def speed_multiplier(self) -> float:
        return self.speed_options[self.speed_index]

    def reset_engine(self) -> None:
        """Instantiate a clean GameEngine instance and compute initial metrics."""
        self.engine = GameEngine(self.config)
        # Seed first tick to trigger initial level load
        self.engine.tick(0.001, Direction.NONE)
        self.current_dir = Direction.NONE
        self.grid = self.engine._grid
        self.total_pellets = sum(1 for row in self.grid.grid for cell in row if cell.consumes)
        self.set_toast("Engine Initialized: Level 1 Loaded")

    def set_toast(self, message: str, duration: float = 2.2) -> None:
        """Post a notification message to the on-screen banner."""
        self.toast_message = message
        self.toast_timer = duration

    def handle_input(self) -> None:
        """Process keyboard & mouse inputs for full engine feature testing."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                return

            if event.type == pygame.KEYDOWN:
                # 1. Quit
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.is_running = False
                    return

                # 2. Movement Directions (WASD / Arrows)
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.current_dir = Direction.UP
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.current_dir = Direction.DOWN
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self.current_dir = Direction.LEFT
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.current_dir = Direction.RIGHT

                # 3. Pause / Resume Execution
                elif event.key in (pygame.K_SPACE, pygame.K_p):
                    if self.engine.state == EngineState.STOPPED:
                        self.engine.resume()
                        self.set_toast("Simulation Resumed")
                    else:
                        self.engine.stop()
                        self.set_toast("Simulation Paused ([.] to step 1 frame)")

                # 4. Frame-by-Frame Stepping (while paused)
                elif event.key in (pygame.K_PERIOD, pygame.K_n):
                    if self.engine.state == EngineState.STOPPED:
                        self.step_one_frame = True
                    else:
                        self.engine.stop()
                        self.step_one_frame = True
                        self.set_toast("Paused & Stepped 1 Frame")

                # 5. Simulation Speed Controls
                elif event.key == pygame.K_RIGHTBRACKET:
                    self.speed_index = min(len(self.speed_options) - 1, self.speed_index + 1)
                    self.set_toast(f"Sim Speed: {self.speed_multiplier}x")
                elif event.key == pygame.K_LEFTBRACKET:
                    self.speed_index = max(0, self.speed_index - 1)
                    self.set_toast(f"Sim Speed: {self.speed_multiplier}x")
                elif event.key == pygame.K_0:
                    self.speed_index = 2
                    self.set_toast("Sim Speed: 1.0x (Normal)")

                # 6. Official Cheats (Chapter VI.5)
                elif event.key in (pygame.K_1, pygame.K_i):
                    self.engine.activate_cheat(Cheat.INVINCIBILITY)
                    status = "ON (Gold Aura)" if self.engine._pacman.is_invincible else "OFF"
                    self.set_toast(f"Cheat: Invincibility {status}")

                elif event.key in (pygame.K_2, pygame.K_l):
                    self.engine.activate_cheat(Cheat.LEVEL_SKIP)
                    self.set_toast("Cheat: Level Skipped!")

                elif event.key in (pygame.K_3, pygame.K_f):
                    self.engine.activate_cheat(Cheat.GHOST_FREEZE)
                    frozen = any(g.is_frozen for g in self.engine._ghosts)
                    status = "FROZEN" if frozen else "UNFROZEN"
                    self.set_toast(f"Cheat: Ghosts {status}")

                elif event.key in (pygame.K_4, pygame.K_e):
                    self.engine.activate_cheat(Cheat.EXTRA_LIVES)
                    self.set_toast(f"Cheat: +1 Life (Total: {self.engine._pacman.lives})")

                elif event.key in (pygame.K_5, pygame.K_PLUS, pygame.K_EQUALS):
                    self.engine.activate_cheat(Cheat.INCREASE_SPEED)
                    self.set_toast(f"Cheat: Speed Up (Pac-Man: {self.engine._pacman.speed:.1f})")

                # 7. Diagnostic Triggers
                elif event.key == pygame.K_t:
                    # Force trigger Frightened mode on all ghosts
                    dur = getattr(self.engine._levelconfig, "frightened_duration", 8.0)
                    self.engine.trigger_frightened_mode(dur)
                    self.set_toast(f"Triggered Frightened Mode ({dur:.1f}s)")

                elif event.key == pygame.K_k:
                    # Kill Pac-Man
                    if self.engine._pacman.is_alive:
                        self.engine._pacman.lose_life()
                        if self.engine._pacman.is_alive:
                            self.engine._respawn()
                            self.set_toast(f"Pac-Man Killed! Respawner active. Lives left: {self.engine._pacman.lives}")
                        else:
                            self.engine._is_game_over = True
                            self.engine._state = EngineState.GAME_OVER
                            self.set_toast("Pac-Man Killed! GAME OVER")

                elif event.key == pygame.K_y:
                    # Drain level time to 5s to test timeout Game Over
                    self.engine._level_time = 5.0
                    self.set_toast("Timer Drained to 5.0s (Timeout Test)")

                elif event.key == pygame.K_c:
                    # Clear remaining pellets to test natural level completion
                    for row in self.grid.grid:
                        for cell in row:
                            cell.remove_consumables()
                    Consumable.reset_counter()
                    self.set_toast("All Pellets Cleared! Level Complete Triggered")

                elif event.key == pygame.K_g:
                    # Cycle ghosts state (WANDER -> CHASE -> FRIGHTENED -> DIED)
                    states_cycle = [GhostState.WANDER, GhostState.CHASE, GhostState.FRIGHTENED, GhostState.DIED]
                    first_state = self.engine._ghosts[0].state
                    next_idx = (states_cycle.index(first_state) + 1) % len(states_cycle) if first_state in states_cycle else 0
                    new_st = states_cycle[next_idx]
                    for g in self.engine._ghosts:
                        g.switch_state(new_st)
                        if new_st == GhostState.FRIGHTENED:
                            g._frightened_time = 8.0
                    self.set_toast(f"Ghosts State Set: {new_st.name}")

                # 8. Level Jump Controls (Jump directly to Level 1..10)
                elif event.key == pygame.K_PAGEUP:
                    self.engine._cur_level = min(10, self.engine._cur_level + 1)
                    self.engine._is_level_loaded = False
                    self.engine._state = EngineState.RESPAWNING
                    self.engine.tick(0.001, Direction.NONE)
                    self.set_toast(f"Jumped to Level {self.engine._cur_level}")

                elif event.key == pygame.K_PAGEDOWN:
                    self.engine._cur_level = max(1, self.engine._cur_level - 1)
                    self.engine._is_level_loaded = False
                    self.engine._state = EngineState.RESPAWNING
                    self.engine.tick(0.001, Direction.NONE)
                    self.set_toast(f"Jumped to Level {self.engine._cur_level}")

                # 9. Serialization / State Persistence Testing
                elif event.key == pygame.K_F5:
                    self.test_save_state()

                elif event.key == pygame.K_F9:
                    self.test_load_state()

                # 10. Highscores & Overlays
                elif event.key == pygame.K_h:
                    self.show_highscores_modal = not self.show_highscores_modal
                    status = "OPEN" if self.show_highscores_modal else "CLOSED"
                    self.set_toast(f"Highscores Leaderboard: {status}")

                elif event.key in (pygame.K_TAB, pygame.K_F1):
                    self.show_debug_overlay = not self.show_debug_overlay
                    status = "ON (Targets + Lines)" if self.show_debug_overlay else "OFF"
                    self.set_toast(f"AI Target Overlay: {status}")

                elif event.key == pygame.K_r:
                    self.reset_engine()

    def test_save_state(self) -> None:
        """Test engine._save_states() serialization to disk."""
        try:
            self.engine._save_states()
            self.set_toast("Quick-Save Successful: State written to disk")
        except Exception as err:
            self.set_toast(f"Save Failed: {err}")

    def test_load_state(self) -> None:
        """Test engine._load_states() restoration from disk."""
        try:
            self.engine._load_states()
            self.grid = self.engine._grid
            self.total_pellets = sum(1 for row in self.grid.grid for cell in row if cell.consumes)
            self.set_toast("Quick-Load Successful: State restored from disk")
        except Exception as err:
            self.set_toast(f"Load Failed: {err}")

    def update(self, dt: float) -> None:
        """Advance game engine simulation."""
        if self.toast_timer > 0:
            self.toast_timer -= dt

        # Single frame stepping while paused
        if self.step_one_frame:
            prev = getattr(self.engine, "_prev_state", EngineState.PLAYING)
            self.engine._state = prev
            self.engine.tick(1.0 / 60.0, self.current_dir)
            self.engine._prev_state = prev
            self.engine._state = EngineState.STOPPED
            self.step_one_frame = False
            self.set_toast("Stepped 1 Frame (1/60s)")
        elif self.engine.state != EngineState.STOPPED:
            effective_dt = dt * self.speed_multiplier
            self.engine.tick(effective_dt, self.current_dir)

        # Handle grid update when advancing levels
        if hasattr(self.engine, "_grid") and self.engine._grid != self.grid:
            self.grid = self.engine._grid
            self.total_pellets = sum(1 for row in self.grid.grid for cell in row if cell.consumes)

    def render_maze(self, origin_x: int, origin_y: int, time_now: float) -> None:
        """Render walls, corridors, pellets, entry/exit, and hover highlight."""
        grid = self.grid
        ts = self.tile_size

        for y in range(grid.height):
            for x in range(grid.width):
                px = origin_x + x * ts
                py = origin_y + y * ts
                cell = grid.grid[y][x]

                if cell.is_wall:
                    pygame.draw.rect(self.screen, COLOR_WALL_FILL, (px, py, ts, ts))

                    # Subtle border outlines
                    if not grid.is_wall(x, y - 1):
                        pygame.draw.line(self.screen, COLOR_WALL_OUTLINE, (px, py), (px + ts - 1, py), 2)
                    if not grid.is_wall(x, y + 1):
                        pygame.draw.line(self.screen, COLOR_WALL_OUTLINE, (px, py + ts - 1), (px + ts - 1, py + ts - 1), 2)
                    if not grid.is_wall(x - 1, y):
                        pygame.draw.line(self.screen, COLOR_WALL_OUTLINE, (px, py), (px, py + ts - 1), 2)
                    if not grid.is_wall(x + 1, y):
                        pygame.draw.line(self.screen, COLOR_WALL_OUTLINE, (px + ts - 1, py), (px + ts - 1, py + ts - 1), 2)
                else:
                    pygame.draw.rect(self.screen, COLOR_CORRIDOR, (px, py, ts, ts))

                    # Entry / Exit highlights
                    if hasattr(grid, "maze_entry") and (x, y) == grid.maze_entry:
                        pygame.draw.rect(self.screen, COLOR_ENTRY, (px + 2, py + 2, ts - 4, ts - 4), 1)
                    elif hasattr(grid, "maze_exit") and (x, y) == grid.maze_exit:
                        pygame.draw.rect(self.screen, COLOR_EXIT, (px + 2, py + 2, ts - 4, ts - 4), 1)

                    # Pellets
                    if cell.consumes:
                        consumable = cell.consumes[0]
                        cx = px + ts // 2
                        cy = py + ts // 2
                        if "SuperPacGum" in consumable.__class__.__name__:
                            pulse = math.sin(time_now * 8) * (ts * 0.08)
                            r = max(4.0, ts * 0.28 + pulse)
                            pygame.draw.circle(self.screen, COLOR_SUPER_PELLET, (cx, cy), int(r))
                        else:
                            r = max(2.0, ts * 0.10)
                            pygame.draw.circle(self.screen, COLOR_PELLET, (cx, cy), int(r))

        # Mouse hover tile highlight
        mx, my = pygame.mouse.get_pos()
        hx = (mx - origin_x) // ts
        hy = (my - origin_y) // ts
        if 0 <= hx < grid.width and 0 <= hy < grid.height:
            h_rect = pygame.Rect(origin_x + hx * ts, origin_y + hy * ts, ts, ts)
            pygame.draw.rect(self.screen, (0, 230, 255), h_rect, 1)

    def render_pacman(self, origin_x: int, origin_y: int, time_now: float) -> None:
        """Render Pac-Man with continuous sub-tile interpolation and chomp animation."""
        pacman = self.engine._pacman
        ts = self.tile_size
        r = ts * 0.44

        cx = origin_x + pacman.x * ts + ts / 2
        cy = origin_y + pacman.y * ts + ts / 2

        # Invincibility aura
        if pacman.is_invincible:
            aura_pulse = math.sin(time_now * 10) * 3
            aura_r = r + 4 + aura_pulse
            aura_surf = pygame.Surface((int(aura_r * 2 + 4), int(aura_r * 2 + 4)), pygame.SRCALPHA)
            pygame.draw.circle(
                aura_surf,
                (255, 215, 0, 110),
                (int(aura_r + 2), int(aura_r + 2)),
                int(aura_r),
            )
            self.screen.blit(aura_surf, (cx - aura_r - 2, cy - aura_r - 2))

        # Direction angle
        angles = {
            Direction.RIGHT: 0.0,
            Direction.DOWN: math.pi / 2,
            Direction.LEFT: math.pi,
            Direction.UP: 3 * math.pi / 2,
            Direction.NONE: 0.0,
        }
        base_angle = angles.get(pacman.cur_direction, 0.0)

        # Mouth animation
        if pacman.cur_direction != Direction.NONE and self.engine.state == EngineState.PLAYING:
            mouth_angle = abs(math.sin(time_now * 15)) * 0.75
        else:
            mouth_angle = 0.2

        if mouth_angle < 0.08:
            pygame.draw.circle(self.screen, COLOR_PACMAN, (int(cx), int(cy)), int(r))
        else:
            start_a = base_angle + mouth_angle / 2
            end_a = base_angle + 2 * math.pi - mouth_angle / 2
            points = [(cx, cy)]
            steps = 22
            for i in range(steps + 1):
                a = start_a + (end_a - start_a) * (i / steps)
                points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            pygame.draw.polygon(self.screen, COLOR_PACMAN, points)

        # Debug tile indicator
        if self.show_debug_overlay:
            tx, ty = pacman.tile
            pygame.draw.rect(self.screen, (255, 238, 0), (origin_x + tx * ts, origin_y + ty * ts, ts, ts), 1)

    def render_ghosts(self, origin_x: int, origin_y: int, time_now: float) -> None:
        """Render ghosts, animated skirts, directional pupils, and AI target lines."""
        ts = self.tile_size
        r = ts * 0.42

        # 1. Target Tile & Path Overlay (when enabled)
        if self.show_debug_overlay:
            line_surf = pygame.Surface((self.maze_width, self.maze_height), pygame.SRCALPHA)
            for ghost in self.engine._ghosts:
                target = ghost.target_tile
                color = GHOST_COLORS.get(ghost.name, (255, 255, 255))
                if target and isinstance(target, tuple) and len(target) == 2:
                    tx, ty = target
                    if 0 <= tx < self.grid.width and 0 <= ty < self.grid.height:
                        # Target reticle box
                        t_px = origin_x + tx * ts
                        t_py = origin_y + ty * ts
                        pygame.draw.rect(self.screen, color, (t_px, t_py, ts, ts), 2)
                        pygame.draw.line(self.screen, color, (t_px, t_py), (t_px + ts, t_py + ts), 1)
                        pygame.draw.line(self.screen, color, (t_px + ts, t_py), (t_px, t_py + ts), 1)

                        # Connecting path line from ghost to target
                        g_cx = ghost.x * ts + ts / 2
                        g_cy = ghost.y * ts + ts / 2
                        t_cx = tx * ts + ts / 2
                        t_cy = ty * ts + ts / 2
                        pygame.draw.line(line_surf, (*color, 120), (g_cx, g_cy), (t_cx, t_cy), 2)
            self.screen.blit(line_surf, (origin_x, origin_y))

        # 2. Ghost Bodies & Eyes
        for ghost in self.engine._ghosts:
            cx = origin_x + ghost.x * ts + ts / 2
            cy = origin_y + ghost.y * ts + ts / 2

            is_frightened = ghost.state == GhostState.FRIGHTENED
            is_died = ghost.state == GhostState.DIED

            if is_frightened:
                f_time = getattr(ghost, "_frightened_time", 5.0)
                if f_time < 2.5 and int(time_now * 5) % 2 == 1:
                    body_color = COLOR_FRIGHTENED_WHITE
                    eye_pupil_color = (255, 40, 40)
                else:
                    body_color = COLOR_FRIGHTENED_BLUE
                    eye_pupil_color = (255, 255, 255)
            elif ghost.is_frozen:
                body_color = COLOR_FROZEN
                eye_pupil_color = (0, 100, 200)
            else:
                body_color = GHOST_COLORS.get(ghost.name, (255, 0, 0))
                eye_pupil_color = (30, 40, 220)

            # Draw body (if not dead eyes)
            if not is_died:
                head_cy = cy - r * 0.15
                body_bottom = head_cy + r * 0.95
                left = cx - r
                right = cx + r

                pygame.draw.circle(self.screen, body_color, (int(cx), int(head_cy)), int(r))
                pygame.draw.rect(
                    self.screen,
                    body_color,
                    (int(left), int(head_cy), int(r * 2), int(r * 0.85)),
                )

                wave = math.sin(time_now * 12 + ghost.x) * (r * 0.15)
                frill_pts = [
                    (left, body_bottom),
                    (left + r * 0.35, body_bottom - r * 0.3 + wave),
                    (left + r * 0.7, body_bottom),
                    (left + r * 1.0, body_bottom - r * 0.3 - wave),
                    (left + r * 1.3, body_bottom),
                    (left + r * 1.65, body_bottom - r * 0.3 + wave),
                    (right, body_bottom),
                    (right, head_cy),
                    (left, head_cy),
                ]
                pygame.draw.polygon(self.screen, body_color, frill_pts)

            # Eyes
            eye_offset_x = 0
            eye_offset_y = 0
            if ghost.cur_direction == Direction.UP:
                eye_offset_y = -r * 0.25
            elif ghost.cur_direction == Direction.DOWN:
                eye_offset_y = r * 0.25
            elif ghost.cur_direction == Direction.LEFT:
                eye_offset_x = -r * 0.25
            elif ghost.cur_direction == Direction.RIGHT:
                eye_offset_x = r * 0.25

            eye_r = r * 0.32
            pupil_r = eye_r * 0.48
            left_eye_pos = (int(cx - r * 0.38), int(cy - r * 0.22))
            right_eye_pos = (int(cx + r * 0.38), int(cy - r * 0.22))

            if is_frightened:
                pygame.draw.circle(self.screen, eye_pupil_color, left_eye_pos, int(pupil_r))
                pygame.draw.circle(self.screen, eye_pupil_color, right_eye_pos, int(pupil_r))
            else:
                pygame.draw.circle(self.screen, (255, 255, 255), left_eye_pos, int(eye_r))
                pygame.draw.circle(self.screen, (255, 255, 255), right_eye_pos, int(eye_r))
                pupil_left = (int(left_eye_pos[0] + eye_offset_x), int(left_eye_pos[1] + eye_offset_y))
                pupil_right = (int(right_eye_pos[0] + eye_offset_x), int(right_eye_pos[1] + eye_offset_y))
                pygame.draw.circle(self.screen, eye_pupil_color, pupil_left, int(pupil_r))
                pygame.draw.circle(self.screen, eye_pupil_color, pupil_right, int(pupil_r))

            # Debug state badge
            if self.show_debug_overlay:
                state_char = ghost.state.name[0]
                badge = self.font_small.render(state_char, True, (255, 255, 0))
                self.screen.blit(badge, (cx - 4, cy - r - 12))

    def render_hud(self, origin_x: int, origin_y: int) -> None:
        """Render score, level, time, lives, and sim speed indicator."""
        hud_rect = pygame.Rect(origin_x, origin_y, self.maze_width, self.hud_height - 10)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, hud_rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, hud_rect, width=1, border_radius=6)

        # 1. Score
        score_lbl = self.font_small.render("SCORE", True, (150, 160, 180))
        score_val = self.font_title.render(f"{self.engine.score:,}", True, (255, 255, 255))
        self.screen.blit(score_lbl, (origin_x + 16, origin_y + 8))
        self.screen.blit(score_val, (origin_x + 16, origin_y + 26))

        # 2. Level
        lvl_lbl = self.font_small.render("LEVEL", True, (150, 160, 180))
        cur_lvl = getattr(self.engine, "_cur_level", 1)
        lvl_val = self.font_title.render(f"{cur_lvl} / 10", True, (60, 220, 120))
        self.screen.blit(lvl_lbl, (origin_x + 130, origin_y + 8))
        self.screen.blit(lvl_val, (origin_x + 130, origin_y + 26))

        # 3. Remaining Time
        time_left = getattr(self.engine, "_level_time", 0.0)
        time_color = (255, 70, 70) if time_left < 15 else (255, 220, 80)
        time_lbl = self.font_small.render("TIME REMAINING", True, (150, 160, 180))
        time_val = self.font_title.render(f"{max(0, int(time_left))}s", True, time_color)
        self.screen.blit(time_lbl, (origin_x + 230, origin_y + 8))
        self.screen.blit(time_val, (origin_x + 230, origin_y + 26))

        # 4. Lives
        lives_lbl = self.font_small.render("LIVES", True, (150, 160, 180))
        self.screen.blit(lives_lbl, (origin_x + 360, origin_y + 8))
        lives = getattr(self.engine._pacman, "lives", 3)
        if lives <= 5:
            for i in range(max(0, lives)):
                lx = origin_x + 360 + i * 20
                ly = origin_y + 36
                pygame.draw.circle(self.screen, COLOR_PACMAN, (lx, ly), 7)
        else:
            lives_val = self.font_title.render(f"x{lives}", True, COLOR_PACMAN)
            self.screen.blit(lives_val, (origin_x + 360, origin_y + 26))

        # 5. Simulation Speed Badge
        speed_lbl = self.font_small.render("SIM SPEED", True, (150, 160, 180))
        speed_col = (255, 215, 0) if self.speed_multiplier != 1.0 else (170, 180, 200)
        speed_val = self.font_title.render(f"{self.speed_multiplier}x", True, speed_col)
        self.screen.blit(speed_lbl, (origin_x + self.maze_width - 110, origin_y + 8))
        self.screen.blit(speed_val, (origin_x + self.maze_width - 110, origin_y + 26))

    def render_sidebar(self, origin_x: int, origin_y: int) -> None:
        """Render comprehensive telemetry, diagnostics, and test hotkey legends."""
        panel_w = self.sidebar_width
        panel_h = self.screen_height - self.margin * 2
        panel_rect = pygame.Rect(origin_x, origin_y, panel_w, panel_h)

        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, panel_rect, width=1, border_radius=8)

        cy = origin_y + 14

        # Header
        title = self.font_title.render("ENGINE DIAGNOSTICS & TELEMETRY", True, (255, 255, 255))
        self.screen.blit(title, (origin_x + 14, cy))
        cy += 28

        # --- SECTION: Engine State & Progress ---
        state = self.engine.state
        state_color = STATE_COLORS.get(state, (200, 200, 200))
        state_text = f"Engine State: {state.name}"
        if state == EngineState.RESPAWNING:
            timer = getattr(self.engine, "_respawn_timer", 0.0)
            state_text += f" ({timer:.1f}s)"
        state_surf = self.font_main.render(state_text, True, state_color)
        self.screen.blit(state_surf, (origin_x + 14, cy))
        cy += 22

        # Pellets & Progress
        remaining = Consumable._counter
        eaten = max(0, self.total_pellets - remaining)
        pct = (eaten / self.total_pellets * 100) if self.total_pellets > 0 else 100.0
        pellet_str = f"Pellets: {remaining} left ({pct:.1f}% cleared)"
        p_surf = self.font_small.render(pellet_str, True, (200, 210, 225))
        self.screen.blit(p_surf, (origin_x + 14, cy))
        cy += 18

        # Mini Progress Bar
        bar_w = panel_w - 28
        bar_h = 6
        pygame.draw.rect(self.screen, (35, 42, 60), (origin_x + 14, cy, bar_w, bar_h), border_radius=3)
        fill_w = int(bar_w * (pct / 100.0))
        if fill_w > 0:
            pygame.draw.rect(self.screen, (40, 200, 110), (origin_x + 14, cy, fill_w, bar_h), border_radius=3)
        cy += 18

        # --- SECTION: Pac-Man Telemetry ---
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (origin_x + 14, cy), (origin_x + panel_w - 14, cy), 1)
        cy += 8
        pacman = self.engine._pacman
        inv_str = "ACTIVE (God Mode)" if pacman.is_invincible else "Off"
        inv_col = (255, 215, 0) if pacman.is_invincible else (140, 150, 165)
        p_info1 = self.font_small.render(f"Pac-Man Tile: {pacman.tile} | Sub: ({pacman.x:.1f}, {pacman.y:.1f})", True, (220, 225, 235))
        p_info2 = self.font_small.render(f"Dir: {pacman.cur_direction.name} | Next: {pacman.next_direction.name} | Spd: {pacman.speed:.1f}", True, (170, 180, 195))
        p_info3 = self.font_small.render(f"Invincibility: {inv_str}", True, inv_col)
        self.screen.blit(p_info1, (origin_x + 14, cy))
        cy += 16
        self.screen.blit(p_info2, (origin_x + 14, cy))
        cy += 16
        self.screen.blit(p_info3, (origin_x + 14, cy))
        cy += 22

        # --- SECTION: Ghosts Live Table ---
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (origin_x + 14, cy), (origin_x + panel_w - 14, cy), 1)
        cy += 8
        g_head = self.font_small.render("GHOST       STATE        TILE     TARGET   DIST", True, (150, 160, 180))
        self.screen.blit(g_head, (origin_x + 14, cy))
        cy += 16

        for ghost in self.engine._ghosts:
            color = GHOST_COLORS.get(ghost.name, (255, 255, 255))
            pygame.draw.circle(self.screen, color, (origin_x + 18, cy + 6), 4)

            dist = math.dist(ghost.tile, pacman.tile)
            target_str = f"{ghost.target_tile}" if ghost.target_tile else "None"
            g_line = f"{ghost.name:<9} {ghost.state.name:<11} {str(ghost.tile):<8} {target_str:<8} {dist:4.1f}t"
            row_col = COLOR_FROZEN if ghost.is_frozen else ((255, 220, 100) if ghost.is_frighten else (220, 225, 235))
            row_surf = self.font_small.render(g_line, True, row_col)
            self.screen.blit(row_surf, (origin_x + 28, cy))
            cy += 16

        cy += 10

        # --- SECTION: Controls & Engine Cheats ---
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (origin_x + 14, cy), (origin_x + panel_w - 14, cy), 1)
        cy += 8
        c_title = self.font_title.render("FEATURE TEST BENCH CONTROLS", True, (255, 255, 255))
        self.screen.blit(c_title, (origin_x + 14, cy))
        cy += 20

        controls = [
            ("[WASD / Arrows]", "Move Pac-Man", (255, 238, 0)),
            ("[Space / P]", "Pause / Resume", (160, 200, 255)),
            ("[.] (Period)", "Step 1 Frame (Pause mode)", (160, 200, 255)),
            ("[ [ / ] ]", "Sim Speed (0.25x - 10x)", (255, 215, 0)),
            ("[1 / I]", "Cheat: Toggle Invincible", (255, 215, 0)),
            ("[2 / L]", "Cheat: Skip Level", (255, 215, 0)),
            ("[3 / F]", "Cheat: Freeze Ghosts", (255, 215, 0)),
            ("[4 / E]", "Cheat: Extra Life (+1)", (255, 215, 0)),
            ("[5 / +]", "Cheat: Increase Speed (+2)", (255, 215, 0)),
            ("[T]", "Trigger Frightened Mode", (255, 120, 180)),
            ("[K]", "Kill Pac-Man (Life loss test)", (255, 80, 80)),
            ("[Y]", "Drain Timer to 5s (Timeout)", (255, 160, 80)),
            ("[C]", "Clear All Pellets (Win test)", (40, 210, 140)),
            ("[PgUp / PgDn]", "Jump Level (1..10)", (60, 220, 120)),
            ("[F5 / F9]", "Quick-Save / Quick-Load", (180, 140, 255)),
            ("[H]", "Toggle Highscores Modal", (255, 210, 50)),
            ("[Tab / F1]", "Toggle AI Targets Overlay", (0, 230, 255)),
            ("[R / Q]", "Restart Engine / Quit", (180, 180, 190)),
        ]

        for key_s, desc, col in controls:
            k_surf = self.font_small.render(key_s, True, col)
            d_surf = self.font_small.render(desc, True, (170, 180, 195))
            self.screen.blit(k_surf, (origin_x + 14, cy))
            self.screen.blit(d_surf, (origin_x + 130, cy))
            cy += 15

        # Footer diagnostics (FPS + Mouse hover info)
        cy = origin_y + panel_h - 22
        fps = int(self.clock.get_fps())
        mx, my = pygame.mouse.get_pos()
        hx = (mx - self.margin) // self.tile_size
        hy = (my - (self.margin + self.hud_height)) // self.tile_size
        hover_txt = f"Tile: ({hx}, {hy})" if (0 <= hx < self.grid.width and 0 <= hy < self.grid.height) else "Outside"
        footer_str = f"FPS: {fps} | Hover: {hover_txt} | Seed: {getattr(self.engine._levelconfig, 'seed', 42)}"
        f_surf = self.font_small.render(footer_str, True, (110, 125, 145))
        self.screen.blit(f_surf, (origin_x + 14, cy))

    def render_overlays(self, origin_x: int, origin_y: int) -> None:
        """Render banner overlays for RESPAWNING, PAUSED, GAME OVER, and WON."""
        state = self.engine.state
        center_x = origin_x + self.maze_width // 2
        center_y = origin_y + self.maze_height // 2

        banner_text: Optional[str] = None
        banner_color = (255, 255, 255)
        sub_text: Optional[str] = None

        if state == EngineState.RESPAWNING:
            timer = getattr(self.engine, "_respawn_timer", 0.0)
            banner_text = "READY!"
            banner_color = (255, 215, 0)
            sub_text = f"Spawning in {max(0.1, timer):.1f}s... (Press '.' to step frame)"
        elif state == EngineState.STOPPED:
            banner_text = "PAUSED"
            banner_color = (160, 200, 255)
            sub_text = "Press SPACE to Resume | [.] to Step 1 Frame"
        elif state == EngineState.GAME_OVER:
            banner_text = "GAME OVER"
            banner_color = (255, 60, 60)
            sub_text = f"Final Score: {self.engine.score} | Press [R] to Restart"
        elif state == EngineState.GAME_WON:
            banner_text = "VICTORY!"
            banner_color = (255, 215, 0)
            sub_text = f"All Levels Completed! Score: {self.engine.score} | Press [R] to Restart"

        if banner_text:
            overlay = pygame.Surface((self.maze_width, self.maze_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            self.screen.blit(overlay, (origin_x, origin_y))

            surf_main = self.font_banner.render(banner_text, True, banner_color)
            self.screen.blit(surf_main, (center_x - surf_main.get_width() // 2, center_y - 30))

            if sub_text:
                surf_sub = self.font_main.render(sub_text, True, (240, 240, 240))
                self.screen.blit(surf_sub, (center_x - surf_sub.get_width() // 2, center_y + 20))

        # Highscores Modal Overlay (when toggled via H)
        if self.show_highscores_modal:
            modal_w = 340
            modal_h = 320
            modal_x = origin_x + (self.maze_width - modal_w) // 2
            modal_y = origin_y + (self.maze_height - modal_h) // 2

            m_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
            pygame.draw.rect(self.screen, (22, 26, 42), m_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 215, 0), m_rect, width=2, border_radius=8)

            m_title = self.font_title.render("TOP 10 HIGHSCORES", True, (255, 215, 0))
            self.screen.blit(m_title, (modal_x + (modal_w - m_title.get_width()) // 2, modal_y + 14))

            top_scores = self.highscore_mgr.get_top_scores(10)
            my = modal_y + 48
            if not top_scores:
                no_s = self.font_main.render("No scores recorded yet", True, (160, 170, 185))
                self.screen.blit(no_s, (modal_x + 30, my))
            else:
                for idx, (p_name, p_score) in enumerate(top_scores, start=1):
                    rank_s = f"{idx:>2}. {p_name:<12} {p_score:>8} pts"
                    c = (255, 235, 100) if idx == 1 else (220, 225, 235)
                    s_surf = self.font_main.render(rank_s, True, c)
                    self.screen.blit(s_surf, (modal_x + 28, my))
                    my += 22

            hint = self.font_small.render("Press [H] to close", True, (140, 150, 170))
            self.screen.blit(hint, (modal_x + (modal_w - hint.get_width()) // 2, modal_y + modal_h - 26))

        # Toast notification
        if self.toast_timer > 0 and self.toast_message:
            toast_surf = self.font_main.render(self.toast_message, True, (255, 255, 255))
            tw = toast_surf.get_width() + 24
            th = toast_surf.get_height() + 12
            tx = origin_x + (self.maze_width - tw) // 2
            ty = origin_y + self.maze_height - 52

            bg_rect = pygame.Rect(tx, ty, tw, th)
            pygame.draw.rect(self.screen, (24, 28, 44), bg_rect, border_radius=6)
            pygame.draw.rect(self.screen, (70, 110, 220), bg_rect, width=1, border_radius=6)
            self.screen.blit(toast_surf, (tx + 12, ty + 6))

    def run(self) -> None:
        """Main testing game loop."""
        maze_origin_x = self.margin
        maze_origin_y = self.margin + self.hud_height
        sidebar_origin_x = maze_origin_x + self.maze_width + self.margin
        sidebar_origin_y = self.margin

        while self.is_running:
            dt = self.clock.tick(60) / 1000.0
            time_now = time.time()

            self.handle_input()
            self.update(dt)

            self.screen.fill(COLOR_BG)

            self.render_hud(maze_origin_x, self.margin)
            self.render_maze(maze_origin_x, maze_origin_y, time_now)
            self.render_pacman(maze_origin_x, maze_origin_y, time_now)
            self.render_ghosts(maze_origin_x, maze_origin_y, time_now)
            self.render_overlays(maze_origin_x, maze_origin_y)
            self.render_sidebar(sidebar_origin_x, sidebar_origin_y)

            pygame.display.flip()

        pygame.quit()


def main() -> None:
    harness = PygameTestHarness()
    harness.run()


if __name__ == "__main__":
    main()
