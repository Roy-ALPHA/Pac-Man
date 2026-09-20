# errors.py
import warnings

class PacmanConfigWarning(UserWarning):
    pass

class PacmanInfo(UserWarning):
    """Khas b les notifications w les infos dial l-config"""
    pass

def _pacman_warning_formatter(msg, category, filename, lineno, line=None):
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    pacman = f"{YELLOW}{BOLD}C{RESET} {CYAN}• • •{RESET}"
    box_top = f"{YELLOW}┌──────────────────────────────────────────────┐{RESET}"
    box_bottom = f"{YELLOW}└──────────────────────────────────────────────┘{RESET}"

    # Ila kant Category hiya PacmanInfo:
    if issubclass(category, PacmanInfo):
        tag_color = CYAN
        label = "Info: "
    else:
        tag_color = RED
        label = "Alert:"

    return (
        f"\n{box_top}\n"
        f"  {pacman}  {BOLD}{tag_color}[{category.__name__}]{RESET}\n"
        f"  {YELLOW}{label}{RESET}    {msg}\n"
        f"{box_bottom}\n\n"
    )

def setup_warnings():
    warnings.formatwarning = _pacman_warning_formatter


setup_warnings()

# Mnin t-bghi tgoul lih raka kat-parse l-fichier:
warnings.warn(
    "Parsing config file: config.json...",
    category=PacmanInfo,
    stacklevel=2
)

# W l-warning l-3adi kay-bqa b Alert w Red:
warnings.warn(
    "Ghost speed is over 10!",
    category=PacmanConfigWarning,
    stacklevel=2
)

