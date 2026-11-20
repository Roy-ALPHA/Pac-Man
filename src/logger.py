"""Asynchronous animated logging and notification system using Rich."""

from collections import deque
from enum import Enum, auto
from pathlib import Path
import threading
from typing import TextIO
from colorama import Fore, Style
from rich.console import Group, Console
from rich.live import Live
from rich.spinner import SPINNERS, Spinner
from .data_dir import LOGS_DIR


class LogType(Enum):
    """Categorization for log messages."""

    WARNING = auto()
    INFO = auto()

    def ansi(self) -> str:
        """Return ANSI colored representation of log level.

        Returns:
            str: Colorized string for console display.
        """
        match self:
            case LogType.INFO:
                return f"{Fore.LIGHTGREEN_EX}{Style.BRIGHT}Info{Fore.RESET}"
            case LogType.WARNING:
                return f"{Fore.LIGHTRED_EX}{Style.BRIGHT}Warning{Fore.RESET}"

    def text(self) -> str:
        """Return plain text label for file logging.

        Returns:
            str: Plain text label.
        """
        match self:
            case LogType.INFO:
                return "Info"
            case LogType.WARNING:
                return "Warning"


class WarningManager:
    """Thread-safe animated logger with live terminal spinners."""

    _spinners: int = 0
    BOX_WIDTH: int = 76
    MAX_MSG_LEN: int = 48
    MAX_TABLES: int = 3

    def __init__(self) -> None:
        """Initialize logger synchronization, file handler, and frames."""
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._warn)
        self._tables: deque[list[Spinner | str]] = deque([])
        self._log_path = LOGS_DIR / "logs.txt"
        self._logs_file: TextIO | None = None
        try:
            self._logs_file = open(self._log_path, "w", encoding="utf-8")
        except OSError:
            self._logs_file = None
        WarningManager._gen_box(self.BOX_WIDTH)

    @property
    def log_path(self) -> Path:
        """Return the path to the disk log file.

        Returns:
            Path: Path to logs.txt.
        """
        return Path(self._log_path)

    @classmethod
    def _gen_box(cls, width: int) -> None:
        """Precompute top and bottom animated border frames for box spinners.

        Args:
            width: Width of the box in characters.
        """
        box_top = list("┌" + "▱" * width + "┐")
        box_bottom = list("└" + "▱" * width + "┘")

        top_frames = []
        bottom_frames = []

        for i in range(width):
            box_top[i + 1] = "▰"
            box_bottom[width - i] = "▰"

            top_frames.append(
                Fore.LIGHTMAGENTA_EX + "".join(box_top) + Fore.RESET
            )
            bottom_frames.append(
                Fore.LIGHTMAGENTA_EX + "".join(box_bottom) + Fore.RESET
            )

        for i in range(width):
            box_top[width - i] = "▱"
            box_bottom[i + 1] = "▱"

            top_frames.append(
                Fore.LIGHTMAGENTA_EX + "".join(box_top) + Fore.RESET
            )
            bottom_frames.append(
                Fore.LIGHTMAGENTA_EX + "".join(box_bottom) + Fore.RESET
            )

        SPINNERS["b_top"] = {
            "interval": 50,
            "frames": top_frames,
        }

        SPINNERS["b_bottom"] = {
            "interval": 50,
            "frames": bottom_frames,
        }

        cls._spinners += 2

    @classmethod
    def _gen_title_spinner(cls, title: str) -> Spinner:
        """Generate animated title header spinner with Pac-Man frames.

        Args:
            title: Category title string.

        Returns:
            Spinner: Constructed Rich Spinner.
        """
        if title not in SPINNERS:
            width = cls.BOX_WIDTH - 2
            title_text = f"[{title}]"

            if len(title_text) > width:
                title_text = title_text[:width]

            line = ["•" if i % 2 else " " for i in range(width)]

            start = (width - len(title_text)) // 2
            end = start + len(title_text)
            line[start:end] = list(title_text)

            frames = []
            pacman_frames = "Cc"
            rotated_pacman = "Ɔɔ"
            colored_title = f"{Fore.LIGHTCYAN_EX}{title_text}{Fore.RESET}"

            for i in range(width // 2):
                left = i
                right = width - 1 - i

                if line[left] == "[" or line[right] == "]":
                    break

                line[left] = (
                    Fore.LIGHTYELLOW_EX
                    + pacman_frames[i % len(pacman_frames)]
                    + Fore.RESET
                )
                if left > 0:
                    line[left - 1] = " "

                line[right] = (
                    Fore.LIGHTYELLOW_EX
                    + rotated_pacman[i % len(rotated_pacman)]
                    + Fore.RESET
                )
                if right < width - 1:
                    line[right + 1] = " "

                rendered_line = (
                    "".join(line[:start])
                    + colored_title
                    + "".join(line[end:])
                )
                frames.append(
                    f"{Style.BRIGHT}  {rendered_line}{Style.RESET_ALL}"
                )

            SPINNERS[title] = {
                "interval": 50,
                "frames": frames,
            }

        return Spinner(title, speed=0.5)

    def stop(self) -> None:
        """Signal stop event, join background thread, and close log file."""
        self._stop_event.set()
        if self._worker.is_alive():
            self._worker.join(timeout=1.0)

        if self._logs_file is not None and not self._logs_file.closed:
            try:
                self._logs_file.close()
            except OSError:
                pass

    def _warn(self) -> None:
        """Worker loop that drives live terminal spinner animations."""
        try:
            with Live(
                self._get_spinners(),
                refresh_per_second=15,
                console=Console(stderr=True),
                vertical_overflow="crop",
                transient=True,
            ) as animation:
                while not self._stop_event.is_set():
                    animation.update(self._get_spinners())
                    self._stop_event.wait(0.05)
        except Exception:
            pass

    @classmethod
    def _create_spinner(cls, frames: list[str]) -> str:
        """Register a unique spinner sequence into the Rich SPINNERS registry.

        Args:
            frames: Sequence of rendered frame strings.

        Returns:
            str: Identifier key of the registered spinner.
        """
        spinner_name = f"spinner_{cls._spinners}"

        SPINNERS[spinner_name] = {
            "interval": 50,
            "frames": frames,
        }

        cls._spinners += 1

        return spinner_name

    @classmethod
    def _gen_line_spinner(cls, msg: str, log_type: LogType) -> Spinner:
        """Generate an animated typewriter spinner for a message line.

        Args:
            msg: Message text.
            log_type: Severity type of the message.

        Returns:
            Spinner: Constructed animated line spinner.
        """
        clean_msg = msg.replace("\n", " ").strip()
        if len(clean_msg) > cls.MAX_MSG_LEN:
            clean_msg = clean_msg[: cls.MAX_MSG_LEN - 3] + "..."
        if not clean_msg:
            clean_msg = " "

        arrows_frames = [
            "▹▹▹▹▹",
            "▸▹▹▹▹",
            "▹▸▹▹▹",
            "▹▹▸▹▹",
            "▹▹▹▸▹",
            "▹▹▹▹▸",
        ]

        frames = []
        spaces = "     " if log_type is LogType.INFO else "  "

        color = (
            Fore.LIGHTGREEN_EX
            if log_type is LogType.INFO
            else Fore.LIGHTRED_EX
        )

        for i in range(len(clean_msg)):
            arr = arrows_frames[i % len(arrows_frames)]
            log_str = (
                f"    {log_type.ansi()}{spaces}"
                f"{Fore.LIGHTCYAN_EX}{arr}{Fore.RESET}    "
            )

            char = (
                clean_msg[i].upper()
                if clean_msg[i].isalpha()
                else clean_msg[i]
            )

            animated_msg = (
                Fore.YELLOW
                + clean_msg[:i]
                + Fore.RESET
                + color
                + char
                + Style.RESET_ALL
                + clean_msg[i + 1:]
            )

            frames.append(log_str + animated_msg)

        spinner_name = WarningManager._create_spinner(frames)

        return Spinner(
            spinner_name,
            speed=0.5,
        )

    def _save_log(self, msg: str, title: str, log_type: LogType) -> None:
        """Append a formatted entry to the persistent disk log.

        Args:
            msg: Message string.
            title: Section title or component.
            log_type: Severity level.
        """
        if self._logs_file is None or self._logs_file.closed:
            return
        arrows = "▸▸▸▸▸"
        log = f"[{title}]{log_type.text()}   {arrows}   {msg}"
        try:
            print(log, file=self._logs_file, flush=True)
        except OSError:
            pass

    def log(self, msg: str, title: str, log_type: LogType) -> None:
        """Enqueue an animated log notification and persist it to disk.

        Args:
            msg: The message string to log.
            title: Section or component title.
            log_type: Severity category (INFO or WARNING).
        """
        self._save_log(msg, title, log_type)
        with self._lock:
            log_table: list[Spinner | str] = [
                Spinner("b_top"),
                self._gen_title_spinner(title),
                self._gen_line_spinner(msg, log_type),
                Spinner("b_bottom"),
                "",
            ]
            self._tables.append(log_table)

            while len(self._tables) > self.MAX_TABLES:
                self._tables.popleft()

    def _get_spinners(self) -> Group:
        """Combine all active spinners and separators into a renderable Group.

        Returns:
            Group: Renderable group containing all current spinner frames.
        """
        with self._lock:
            all_spinners = []
            for spinners in self._tables:
                all_spinners.extend(spinners)
            return Group(*all_spinners)

    def start(self) -> None:
        """Start the background live animation worker thread."""
        if not self._worker.is_alive():
            self._worker.start()

    def join(self) -> None:
        """Wait for the background worker thread to finish execution."""
        self._worker.join()


warning_manager = WarningManager()
log = warning_manager.log
