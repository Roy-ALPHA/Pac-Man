import warnings


class MazeAdapterWarning(UserWarning):
    pass


class PacmanConfigWarning(UserWarning):
    pass


class HighscoreManagerWarning(UserWarning):
    pass


class EngineWarning(UserWarning):
    pass


def _pacman_warning_formatter(msg, category, filename, lineno, line=None):
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    pacman = f"{YELLOW}{BOLD}C{RESET} {CYAN}• • •{RESET}"

    box_top = f"{YELLOW}┌" + "─" * (len(str(msg)) + 12) + f"┐{RESET}"
    box_bottom = f"{YELLOW}└" + "─" * (len(str(msg)) + 12) + f"┘{RESET}"

    return (
        f"\n{box_top}\n"
        f"  {pacman}  {BOLD}{RED}[{category.__name__}]{RESET}\n"
        f"  {YELLOW}Alert › {RESET}    {msg}\n"
        f"{box_bottom}\n\n"
    )


def setup_warnings():
    warnings.formatwarning = _pacman_warning_formatter
