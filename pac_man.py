from src.errors import setup_warnings
from pathlib import Path
from src.config import Config
from src.highscore import HighscoreManager
from src.maze_adapter import MazeAdapter, CellType, MazeGrid

setup_warnings()


class TerminalRenderer:
    # ANSI escape sequences
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    BLUE = "\033[34m"
    BRIGHT_BLUE = "\033[94m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    PINK = "\033[95m"
    WHITE = "\033[97m"

    # Unicode symbols (double-width characters for square grid aspect ratio)
    WALL_CHAR = "██"
    PATH_CHAR = "  "
    PELLET_CHAR = " ·"
    SUPER_PELLET_CHAR = " ●"
    ENTRY_CHAR = " E"
    EXIT_CHAR = " X"
    PLAYER_CHAR = " C"
    GHOST_CHAR = " M"

    @classmethod
    def render(
        cls,
        grid: MazeGrid,
        player_pos: tuple[int, int] | None = None,
        ghost_positions: list[tuple[int, int]] | None = None,
    ) -> str:
        lines: list[str] = []
        ghost_set = set(ghost_positions or [])

        # Top border coordinate ruler
        ruler = "   " + "".join(f"{x % 10:2}" for x in range(grid.width))
        lines.append(f"{cls.DIM}{ruler}{cls.RESET}")

        for y in range(grid.height):
            row_str = [f"{cls.DIM}{y:2} {cls.RESET}"]

            for x in range(grid.width):
                pos = (x, y)
                cell = grid.get_cell(x, y)

                # 1. Dynamic Entities (Player & Ghosts)
                if player_pos and pos == player_pos:
                    row_str.append(
                        f"{cls.YELLOW}{cls.BOLD}{cls.PLAYER_CHAR}{cls.RESET}"
                    )
                elif pos in ghost_set:
                    row_str.append(
                        f"{cls.RED}{cls.BOLD}{cls.GHOST_CHAR}{cls.RESET}"
                    )

                # 2. Level Entry & Exit points
                elif hasattr(grid, "maze_entry") and pos == grid.maze_entry:
                    row_str.append(
                        f"{cls.GREEN}{cls.BOLD}{cls.ENTRY_CHAR}{cls.RESET}"
                    )
                elif hasattr(grid, "maze_exit") and pos == grid.maze_exit:
                    row_str.append(
                        f"{cls.CYAN}{cls.BOLD}{cls.EXIT_CHAR}{cls.RESET}"
                    )

                # 3. Walls
                elif cell.cell_type == CellType.WALL:
                    row_str.append(f"{cls.BLUE}{cls.WALL_CHAR}{cls.RESET}")

                # 5. Empty Open Corridor
                else:
                    row_str.append(cls.PATH_CHAR)

            lines.append("".join(row_str))

        # Bottom Legend
        legend = (
            f"\n{cls.DIM}Legend:{cls.RESET} "
            f"{cls.BLUE}██{cls.RESET} Wall  "
            f"{cls.GREEN} E{cls.RESET} Entry  "
            f"{cls.CYAN} X{cls.RESET} Exit  "
            f"{cls.WHITE} ·{cls.RESET} Pellet  "
            f"{cls.YELLOW} ●{cls.RESET} Energizer  "
            f"{cls.YELLOW} C{cls.RESET} Player"
        )
        lines.append(legend)

        return "\n".join(lines)

def main() -> None:
    path = Path("config.json")
    config = Config.from_file(path)
    # highscoremanager = HighscoreManager(config.highscore_filename)
    # highscoremanager.save("yssuiui", 909090)
    # print(highscoremanager.get_top_scores())
    mazegrid = MazeAdapter().generate_level_maze(config.generate_level(1))
    print(mazegrid)
    print(TerminalRenderer.render(mazegrid))

if __name__ == "__main__":
    main()
