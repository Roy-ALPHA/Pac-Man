#!/usr/bin/env python3
"""
Pygame GUI test harness for the Pac-Man Engine and Backend.
Provides an interactive graphical replacement for terminal_test.py
with smooth rendering, telemetry diagnostics, and real-time cheat controls.
"""

import math
from pathlib import Path
import time
from typing import Optional, Tuple

import pygame

from src.config import Config
from src.maze_adapter import MazeAdapter
from src.engine import GameEngine, EngineState, Cheat
from src.entities import Direction, GhostState


# ==============================================================================
# Theme & Color Definitions
# ==============================================================================
COLOR_BG = (10, 12, 18)
COLOR_PANEL_BG = (18, 22, 34)
COLOR_PANEL_BORDER = (45, 55, 80)
COLOR_WALL_FILL = (18, 24, 70)
COLOR_WALL_OUTLINE = (38, 70, 220)
COLOR_CORRIDOR = (6, 8, 12)

COLOR_PELLET = (255, 225, 180)
COLOR_SUPER_PELLET = (255, 180, 80)
COLOR_ENTRY = (40, 200, 90)
COLOR_EXIT = (40, 210, 255)

COLOR_PACMAN = (255, 238, 0)
COLOR_PACMAN_INVINCIBLE = (255, 215, 0)

GHOST_COLORS = {
    "Blinky": (255, 40, 40),
    "Pinky": (255, 180, 220),
    "Inky": (0, 235, 255),
    "Clyde": (255, 175, 50),
}

COLOR_FRIGHTENED_BLUE = (38, 75, 255)
COLOR_FRIGHTENED_WHITE = (245, 245, 255)
COLOR_FROZEN = (160, 230, 255)

STATE_COLORS = {
    EngineState.PLAYING: (60, 220, 100),
    EngineState.RESPAWNING: (255, 210, 50),
    EngineState.STOPPED: (180, 180, 200),
    EngineState.GAME_OVER: (255, 60, 60),
    EngineState.GAME_WON: (255, 215, 0),
}


class PygameTestHarness:
    """Interactive GUI test runner for GameEngine and backend systems."""

    def __init__(self, config_path: str = "config.json") -> None:
        pygame.init()
        pygame.display.set_caption("Pac-Man Engine & Backend Visual Test Runner")

        self.clock = pygame.time.Clock()
        self.config_path = Path(config_path)
        self.config = Config.from_file(self.config_path)

        # Load fonts
        self.font_title = pygame.font.Font(None, 28)
        self.font_main = pygame.font.Font(None, 22)
        self.font_small = pygame.font.Font(None, 18)
        self.font_banner = pygame.font.Font(None, 48)

        # Engine & Navigation
        self.engine: GameEngine = None  # type: ignore
        self.current_dir = Direction.NONE
        self.show_debug_overlay = False
        self.toast_message = ""
        self.toast_timer = 0.0

        # Create engine instance and bootstrap first tick
        self.reset_engine()

        # Compute dynamic layout dimensions
        self.grid = self.engine._grid
        self.sidebar_width = 330
        self.hud_height = 64
        self.margin = 20

        # Calculate best tile size
        max_maze_w = 760
        max_maze_h = 700
        self.tile_size = max(
            18,
            min(36, max_maze_w // self.grid.width, max_maze_h // self.grid.height)
        )

        self.maze_width = self.grid.width * self.tile_size
        self.maze_height = self.grid.height * self.tile_size

        self.screen_width = self.maze_width + self.sidebar_width + self.margin * 3
        self.screen_height = max(self.maze_height + self.hud_height + self.margin * 2, 640)

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.is_running = True

    def reset_engine(self) -> None:
        """Instantiate a fresh GameEngine instance."""
        self.engine = GameEngine(self.config)
        # Advance 1 short tick so _load_level initializes entities immediately
        self.engine.tick(0.001, Direction.NONE)
        self.current_dir = Direction.NONE
        self.set_toast("Engine Restarted")

    def set_toast(self, message: str, duration: float = 2.0) -> None:
        """Display a temporary notification banner."""
        self.toast_message = message
        self.toast_timer = duration

    def handle_input(self) -> None:
        """Process keyboard events for movement, cheats, and testing."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                return

            if event.type == pygame.KEYDOWN:
                # Quit
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.is_running = False
                    return

                # Directions
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.current_dir = Direction.UP
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.current_dir = Direction.DOWN
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self.current_dir = Direction.LEFT
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.current_dir = Direction.RIGHT

                # Pause / Resume
                elif event.key in (pygame.K_SPACE, pygame.K_p):
                    if self.engine.state == EngineState.STOPPED:
                        self.engine.resume()
                        self.set_toast("Game Resumed")
                    else:
                        self.engine.stop()
                        self.set_toast("Game Paused")

                # Restart
                elif event.key == pygame.K_r:
                    self.reset_engine()

                # Toggle Debug Overlay
                elif event.key in (pygame.K_TAB, pygame.K_F1):
                    self.show_debug_overlay = not self.show_debug_overlay
                    status = "ON" if self.show_debug_overlay else "OFF"
                    self.set_toast(f"Debug Overlay: {status}")

                # Cheats Testing
                elif event.key in (pygame.K_1, pygame.K_i):
                    self.engine.activate_cheat(Cheat.INVINCIBILITY)
                    status = "ON" if self.engine._pacman.is_invincible else "OFF"
                    self.set_toast(f"Cheat: Invincibility {status}")

                elif event.key in (pygame.K_2, pygame.K_l):
                    self.engine.activate_cheat(Cheat.LEVEL_SKIP)
                    self.set_toast("Cheat: Level Skipped!")

                elif event.key in (pygame.K_3, pygame.K_f):
                    self.engine.activate_cheat(Cheat.GHOST_FREEZE)
                    self.set_toast("Cheat: Ghosts Frozen!")

                elif event.key in (pygame.K_4, pygame.K_e):
                    self.engine.activate_cheat(Cheat.EXTRA_LIVES)
                    self.set_toast(f"Cheat: +1 Life (Total: {self.engine._pacman._lives})")

                elif event.key in (pygame.K_5, pygame.K_PLUS, pygame.K_EQUALS):
                    self.engine.activate_cheat(Cheat.INCREASE_SPEED)
                    self.set_toast(f"Cheat: Speed Increased ({self.engine._pacman._speed:.1f})")

    def update(self, dt: float) -> None:
        """Step the game engine forward."""
        if self.toast_timer > 0:
            self.toast_timer -= dt

        # Update engine
        self.engine.tick(dt, self.current_dir)

        # If level changed, update grid reference and recalibrate size if needed
        if hasattr(self.engine, "_grid") and self.engine._grid != self.grid:
            self.grid = self.engine._grid

    def render_maze(self, origin_x: int, origin_y: int, time_now: float) -> None:
        """Render walls, corridors, pellets, and energizers."""
        grid = self.grid
        ts = self.tile_size

        for y in range(grid.height):
            for x in range(grid.width):
                px = origin_x + x * ts
                py = origin_y + y * ts
                cell = grid.grid[y][x]

                if cell.is_wall:
                    # Wall block fill
                    pygame.draw.rect(self.screen, COLOR_WALL_FILL, (px, py, ts, ts))

                    # Outer edge outlines
                    if not grid.is_wall(x, y - 1):  # North
                        pygame.draw.line(self.screen, COLOR_WALL_OUTLINE, (px, py), (px + ts - 1, py), 2)
                    if not grid.is_wall(x, y + 1):  # South
                        pygame.draw.line(self.screen, COLOR_WALL_OUTLINE, (px, py + ts - 1), (px + ts - 1, py + ts - 1), 2)
                    if not grid.is_wall(x - 1, y):  # West
                        pygame.draw.line(self.screen, COLOR_WALL_OUTLINE, (px, py), (px, py + ts - 1), 2)
                    if not grid.is_wall(x + 1, y):  # East
                        pygame.draw.line(self.screen, COLOR_WALL_OUTLINE, (px + ts - 1, py), (px + ts - 1, py + ts - 1), 2)
                else:
                    # Corridor fill
                    pygame.draw.rect(self.screen, COLOR_CORRIDOR, (px, py, ts, ts))

                    # Entry / Exit highlights
                    if hasattr(grid, "maze_entry") and (x, y) == grid.maze_entry:
                        pygame.draw.rect(self.screen, COLOR_ENTRY, (px + 2, py + 2, ts - 4, ts - 4), 1)
                    elif hasattr(grid, "maze_exit") and (x, y) == grid.maze_exit:
                        pygame.draw.rect(self.screen, COLOR_EXIT, (px + 2, py + 2, ts - 4, ts - 4), 1)

                    # Consumables
                    if cell.consumes:
                        consumable = cell.consumes[0]
                        cx = px + ts // 2
                        cy = py + ts // 2
                        if "SuperPacGum" in consumable.__class__.__name__:
                            # Pulsating energizer pellet
                            pulse = math.sin(time_now * 8) * (ts * 0.08)
                            r = max(4.0, ts * 0.28 + pulse)
                            pygame.draw.circle(self.screen, COLOR_SUPER_PELLET, (cx, cy), int(r))
                        else:
                            # Standard PacGum pellet
                            r = max(2.0, ts * 0.10)
                            pygame.draw.circle(self.screen, COLOR_PELLET, (cx, cy), int(r))

    def render_pacman(self, origin_x: int, origin_y: int, time_now: float) -> None:
        """Render Pac-Man with continuous sub-tile interpolation and chomp animation."""
        pacman = self.engine._pacman
        ts = self.tile_size
        r = ts * 0.44

        # Continuous floating-point coordinates for silky 60 FPS movement
        cx = origin_x + pacman._x * ts + ts / 2
        cy = origin_y + pacman._y * ts + ts / 2

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

        # Mouth opening animation
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

    def render_ghosts(self, origin_x: int, origin_y: int, time_now: float) -> None:
        """Render all ghosts with classic shapes, wavy frills, and directional eyes."""
        ts = self.tile_size
        r = ts * 0.42

        for ghost in self.engine._ghosts:
            # Continuous sub-tile position
            cx = origin_x + ghost._x * ts + ts / 2
            cy = origin_y + ghost._y * ts + ts / 2

            is_frightened = ghost.state == GhostState.FRIGHTENED
            is_died = ghost.state == GhostState.DIED
            is_frozen = ghost.state == GhostState.FROZEN

            # Determine body & eye styling
            if is_frightened:
                f_time = getattr(ghost, "_frightened_time", 5.0)
                if f_time < 2.5 and int(time_now * 5) % 2 == 1:
                    body_color = COLOR_FRIGHTENED_WHITE
                    eye_pupil_color = (255, 40, 40)
                else:
                    body_color = COLOR_FRIGHTENED_BLUE
                    eye_pupil_color = (255, 255, 255)
            elif is_frozen:
                body_color = COLOR_FROZEN
                eye_pupil_color = (0, 110, 210)
            else:
                body_color = GHOST_COLORS.get(ghost.name, (255, 0, 0))
                eye_pupil_color = (30, 40, 220)

            # 1. Draw Body (if not dead eyes returning to base)
            if not is_died:
                head_cy = cy - r * 0.15
                body_bottom = head_cy + r * 0.95
                left = cx - r
                right = cx + r

                # Top rounded head
                pygame.draw.circle(self.screen, body_color, (int(cx), int(head_cy)), int(r))

                # Middle torso
                pygame.draw.rect(
                    self.screen,
                    body_color,
                    (int(left), int(head_cy), int(r * 2), int(r * 0.85)),
                )

                # Bottom skirt wavy frills (animated)
                wave = math.sin(time_now * 12 + ghost._x) * (r * 0.15)
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

            # 2. Draw Eyes
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
                # Frightened face: small square-ish dots
                pygame.draw.circle(self.screen, eye_pupil_color, left_eye_pos, int(pupil_r))
                pygame.draw.circle(self.screen, eye_pupil_color, right_eye_pos, int(pupil_r))
            else:
                # White sclera
                pygame.draw.circle(self.screen, (255, 255, 255), left_eye_pos, int(eye_r))
                pygame.draw.circle(self.screen, (255, 255, 255), right_eye_pos, int(eye_r))

                # Directional pupils
                pupil_left = (int(left_eye_pos[0] + eye_offset_x), int(left_eye_pos[1] + eye_offset_y))
                pupil_right = (int(right_eye_pos[0] + eye_offset_x), int(right_eye_pos[1] + eye_offset_y))
                pygame.draw.circle(self.screen, eye_pupil_color, pupil_left, int(pupil_r))
                pygame.draw.circle(self.screen, eye_pupil_color, pupil_right, int(pupil_r))

            # Debug badge over ghost if enabled
            if self.show_debug_overlay:
                state_char = ghost.state.name[0]
                badge = self.font_small.render(state_char, True, (255, 255, 0))
                self.screen.blit(badge, (cx - 4, cy - r - 12))

    def render_hud(self, origin_x: int, origin_y: int) -> None:
        """Render top score, lives, level, and remaining timer."""
        # Top banner background
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
        lvl_val = self.font_title.render(str(getattr(self.engine, "_cur_level", 1)), True, (60, 220, 120))
        self.screen.blit(lvl_lbl, (origin_x + 160, origin_y + 8))
        self.screen.blit(lvl_val, (origin_x + 160, origin_y + 26))

        # 3. Remaining Time
        time_left = getattr(self.engine, "_level_time", 0.0)
        time_color = (255, 70, 70) if time_left < 15 else (255, 220, 80)
        time_lbl = self.font_small.render("TIME", True, (150, 160, 180))
        time_val = self.font_title.render(f"{max(0, int(time_left))}s", True, time_color)
        self.screen.blit(time_lbl, (origin_x + 260, origin_y + 8))
        self.screen.blit(time_val, (origin_x + 260, origin_y + 26))

        # 4. Lives
        lives_lbl = self.font_small.render("LIVES", True, (150, 160, 180))
        self.screen.blit(lives_lbl, (origin_x + 360, origin_y + 8))
        lives = getattr(self.engine._pacman, "_lives", 3)
        if lives <= 5:
            for i in range(max(0, lives)):
                lx = origin_x + 360 + i * 20
                ly = origin_y + 36
                pygame.draw.circle(self.screen, COLOR_PACMAN, (lx, ly), 7)
        else:
            lives_val = self.font_title.render(f"x{lives}", True, COLOR_PACMAN)
            self.screen.blit(lives_val, (origin_x + 360, origin_y + 26))

    def render_sidebar(self, origin_x: int, origin_y: int) -> None:
        """Render telemetry, ghost inspection table, and interactive cheat controls."""
        panel_w = self.sidebar_width
        panel_h = self.screen_height - self.margin * 2
        panel_rect = pygame.Rect(origin_x, origin_y, panel_w, panel_h)

        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, panel_rect, width=1, border_radius=8)

        cy = origin_y + 16

        # --- SECTION: Engine State ---
        title = self.font_title.render("ENGINE TELEMETRY", True, (255, 255, 255))
        self.screen.blit(title, (origin_x + 16, cy))
        cy += 32

        state = self.engine.state
        state_color = STATE_COLORS.get(state, (200, 200, 200))
        state_text = f"State: {state.name}"
        if state == EngineState.RESPAWNING:
            timer = getattr(self.engine, "_respawn_timer", 0.0)
            state_text += f" ({timer:.1f}s)"
        state_surf = self.font_main.render(state_text, True, state_color)
        self.screen.blit(state_surf, (origin_x + 16, cy))
        cy += 24

        # Pacman details
        pacman = self.engine._pacman
        inv_str = "ACTIVE (Gold)" if pacman.is_invincible else "Inactive"
        inv_col = (255, 215, 0) if pacman.is_invincible else (150, 150, 160)
        p_info = self.font_small.render(f"Pac-Man: Tile {pacman.tile} | Speed: {pacman._speed:.1f}", True, (200, 210, 220))
        p_inv = self.font_small.render(f"Invincibility: {inv_str}", True, inv_col)
        self.screen.blit(p_info, (origin_x + 16, cy))
        cy += 18
        self.screen.blit(p_inv, (origin_x + 16, cy))
        cy += 28

        # --- SECTION: Ghost Diagnostics ---
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (origin_x + 16, cy), (origin_x + panel_w - 16, cy), 1)
        cy += 12
        g_title = self.font_title.render("GHOST INSPECTION", True, (255, 255, 255))
        self.screen.blit(g_title, (origin_x + 16, cy))
        cy += 28

        for ghost in self.engine._ghosts:
            color = GHOST_COLORS.get(ghost.name, (255, 255, 255))
            pygame.draw.circle(self.screen, color, (origin_x + 22, cy + 8), 5)

            dist = math.dist(ghost.tile, pacman.tile)
            g_line = self.font_small.render(
                f"{ghost.name:<7} | {ghost.state.name:<10} | {dist:4.1f}t",
                True,
                (220, 225, 235),
            )
            self.screen.blit(g_line, (origin_x + 36, cy))
            cy += 20

        cy += 14

        # --- SECTION: Cheats & Keyboard Controls ---
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (origin_x + 16, cy), (origin_x + panel_w - 16, cy), 1)
        cy += 12
        ctrl_title = self.font_title.render("CONTROLS & CHEATS", True, (255, 255, 255))
        self.screen.blit(ctrl_title, (origin_x + 16, cy))
        cy += 26

        cheats = [
            ("[Arrows / WASD]", "Move Pac-Man"),
            ("[Space / P]", "Pause / Resume"),
            ("[1 / I]", "Cheat: Invincible"),
            ("[2 / L]", "Cheat: Skip Level"),
            ("[3 / F]", "Cheat: Freeze Ghosts"),
            ("[4 / E]", "Cheat: Extra Life"),
            ("[5 / +]", "Cheat: Speed Up"),
            ("[R]", "Restart Engine"),
            ("[Tab / F1]", "Toggle Debug Overlay"),
            ("[Q / Esc]", "Quit Visual Runner"),
        ]

        for key_str, desc in cheats:
            k_surf = self.font_small.render(key_str, True, (255, 210, 50))
            d_surf = self.font_small.render(desc, True, (170, 180, 195))
            self.screen.blit(k_surf, (origin_x + 16, cy))
            self.screen.blit(d_surf, (origin_x + 140, cy))
            cy += 20

        # FPS meter
        cy = origin_y + panel_h - 32
        fps = int(self.clock.get_fps())
        fps_surf = self.font_small.render(f"Framerate: {fps} FPS", True, (100, 110, 130))
        self.screen.blit(fps_surf, (origin_x + 16, cy))

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
            sub_text = f"Spawning in {max(0.1, timer):.1f}s..."
        elif state == EngineState.STOPPED:
            banner_text = "PAUSED"
            banner_color = (160, 200, 255)
            sub_text = "Press SPACE to Resume"
        elif state == EngineState.GAME_OVER:
            banner_text = "GAME OVER"
            banner_color = (255, 60, 60)
            sub_text = "Press 'R' to Restart"
        elif state == EngineState.GAME_WON:
            banner_text = "VICTORY!"
            banner_color = (255, 215, 0)
            sub_text = "All Levels Cleared! Press 'R' to Restart"

        if banner_text:
            # Darkened backdrop
            overlay = pygame.Surface((self.maze_width, self.maze_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            self.screen.blit(overlay, (origin_x, origin_y))

            # Main banner
            surf_main = self.font_banner.render(banner_text, True, banner_color)
            self.screen.blit(surf_main, (center_x - surf_main.get_width() // 2, center_y - 30))

            if sub_text:
                surf_sub = self.font_main.render(sub_text, True, (240, 240, 240))
                self.screen.blit(surf_sub, (center_x - surf_sub.get_width() // 2, center_y + 20))

        # Toast notification
        if self.toast_timer > 0 and self.toast_message:
            toast_surf = self.font_main.render(self.toast_message, True, (255, 255, 255))
            tw = toast_surf.get_width() + 24
            th = toast_surf.get_height() + 12
            tx = origin_x + (self.maze_width - tw) // 2
            ty = origin_y + self.maze_height - 50

            bg_rect = pygame.Rect(tx, ty, tw, th)
            pygame.draw.rect(self.screen, (24, 28, 44), bg_rect, border_radius=6)
            pygame.draw.rect(self.screen, (70, 110, 220), bg_rect, width=1, border_radius=6)
            self.screen.blit(toast_surf, (tx + 12, ty + 6))

    def run(self) -> None:
        """Main game and animation loop."""
        maze_origin_x = self.margin
        maze_origin_y = self.margin + self.hud_height
        sidebar_origin_x = maze_origin_x + self.maze_width + self.margin
        sidebar_origin_y = self.margin

        while self.is_running:
            dt = self.clock.tick(60) / 1000.0  # Normalized dt in seconds
            time_now = time.time()

            self.handle_input()
            self.update(dt)

            # Drawing
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
