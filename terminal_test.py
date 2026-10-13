import curses
import time
from src import entities
from src.engine import EngineState, GameEngine

# Mapping dyal les touches l Direction
KEY_MAPPINGS = {
    curses.KEY_UP: entities.Direction.UP,
    curses.KEY_DOWN: entities.Direction.DOWN,
    curses.KEY_LEFT: entities.Direction.LEFT,
    curses.KEY_RIGHT: entities.Direction.RIGHT,
    ord("w"): entities.Direction.UP,
    ord("s"): entities.Direction.DOWN,
    ord("a"): entities.Direction.LEFT,
    ord("d"): entities.Direction.RIGHT,
}


def run_terminal_ui(stdscr, config, maze_adapter):
    # Setup curses
    curses.curs_set(0)  # Khbbi l-cursor
    stdscr.nodelay(True)  # Non-blocking getch()
    stdscr.timeout(0)

    # Setup Colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_YELLOW, -1)  # Pac-Man
    curses.init_pair(2, curses.COLOR_RED, -1)  # Blinky
    curses.init_pair(3, curses.COLOR_MAGENTA, -1)  # Pinky
    curses.init_pair(4, curses.COLOR_CYAN, -1)  # Inky
    curses.init_pair(5, curses.COLOR_GREEN, -1)  # Clyde
    curses.init_pair(6, curses.COLOR_BLUE, -1)  # Walls / Frightened
    curses.init_pair(7, curses.COLOR_WHITE, -1)  # PacGums

    engine = GameEngine(config, maze_adapter)

    current_dir = entities.Direction.UP
    last_time = time.time()
    # f = open("logs.txt", "w")
    while True:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time

        # 1. Input Handling
        try:
            key = stdscr.getch()
            if key in KEY_MAPPINGS:
                current_dir = KEY_MAPPINGS[key]
            elif key == ord("q") or key == 27:  # 'q' aw ESC bach tkhrej
                break
        except Exception:
            pass

        # 2. Engine Step

        engine.tick(dt, current_dir)
        # print(*[g.state for g in engine._ghosts], file=f)

        # 3. Render
        stdscr.erase()

        # HUD Info
        stdscr.addstr(0, 0, f"Score: {engine.score} | Level: {engine._cur_level}")
        stdscr.addstr(1, 0, f"State: {engine.state.name} | [Q to Quit]")

        # Render Maze w Consumables
        if hasattr(engine, "_grid") and engine._grid:
            grid = engine._grid
            for y, row in enumerate(grid.grid):
                for x, cell in enumerate(row):
                    draw_y = y + 3
                    draw_x = x * 2  # * 2 7it les caractères dial terminal twaylin

                    if grid.is_wall(x, y):
                        stdscr.addstr(draw_y, draw_x, "██", curses.color_pair(6))
                    elif cell.consumes:
                        consumable = cell.consumes[0]
                        # SuperPacGum vs Normal PacGum
                        if "SuperPacGum" in consumable.__class__.__name__:
                            stdscr.addstr(draw_y, draw_x, "● ", curses.color_pair(1))
                        else:
                            stdscr.addstr(draw_y, draw_x, "· ", curses.color_pair(7))

            # Render Ghosts
            ghost_colors = [2, 3, 4, 5]  # Red, Magenta, Cyan, Green
            for idx, ghost in enumerate(engine._ghosts):
                gx, gy = ghost.tile
                char = "ᗣ "
                color_idx = (
                    6
                    if ghost.state == entities.GhostState.FRIGHTENED
                    else ghost_colors[idx % 4]
                )
                stdscr.addstr(gy + 3, gx * 2, char, curses.color_pair(color_idx))

            # Render Pac-Man
            px, py = engine._pacman.tile
            stdscr.addstr(py + 3, px * 2, "C ", curses.color_pair(1) | curses.A_BOLD)

        # Game Over / Win messages
        if engine.state == EngineState.GAME_OVER:
            stdscr.addstr(2, 0, "=== GAME OVER ===", curses.A_BOLD | curses.color_pair(2))
        elif engine.state == EngineState.GAME_WON:
            stdscr.addstr(2, 0, "=== YOU WON! ===", curses.A_BOLD | curses.color_pair(5))

        stdscr.refresh()
        time.sleep(0.03)  # Taqriban ~30 FPS


def main():
    # Mock aw import dial config w maze_adapter dialk hna
    from src.config import Config
    from src.maze_adapter import MazeAdapter
    from pathlib import Path

    config = Config.from_file(Path("config.json"))
    adapter = MazeAdapter()

    # curses.wrapper kat-handle terminal setup w cleanup bla ma t-khser lik bash/fish ila tra crash
    curses.wrapper(lambda stdscr: run_terminal_ui(stdscr, config, adapter))


if __name__ == "__main__":
    main()
