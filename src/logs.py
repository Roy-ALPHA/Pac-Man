"""Asynchronous animated logging and notification system using Rich."""

from enum import Enum, auto
from pathlib import Path
import threading
from typing import Any
from colorama import Fore, Style
from rich.console import Group
from rich.live import Live
from rich.spinner import SPINNERS, Spinner

try:
    from .data_dir import DATA_DIR
except ImportError:
    from data_dir import DATA_DIR  # type: ignore[no-redef]


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

    def __init__(self) -> None:
        """Initialize logger synchronization, file handler, and frames."""
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._warn)
        self._tables: dict[str, list[Any]] = {}
        self._log_path = DATA_DIR / "logs.txt"
        self._logs_file = open(self._log_path, "w", encoding="utf-8")
        WarningManager._gen_box(100)

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

    @staticmethod
    def _gen_titel_spinner(titel: str) -> Spinner:
        """Generate animated title header spinner with Pac-Man frames.

        Args:
            titel: Category title string.

        Returns:
            Spinner: Constructed Rich Spinner.
        """
        if titel not in SPINNERS:
            width = 98
            title = f"{Fore.LIGHTCYAN_EX}[{titel}]{Fore.RESET}"

            if len(title) > width:
                title = title[:width]

            line = ["•" if i % 2 else " " for i in range(width)]

            start = (width - len(title)) // 2
            line[start:start + len(title)] = title

            frames = []
            pacman_frames = "Cc"
            rotated_pacman = "Ɔɔ"

            for i in range(width // 2):
                if line[i] == "[":
                    break

                left = i
                right = width - 1 - i

                if left < start or left >= start + len(title):
                    color_p = (
                        Fore.LIGHTYELLOW_EX
                        + pacman_frames[i % len(pacman_frames)]
                        + Fore.RESET
                    )
                    line[left] = color_p

                if left > 0:
                    line[left - 1] = " "

                if right < start or right >= start + len(title):
                    color_r = (
                        Fore.LIGHTYELLOW_EX
                        + rotated_pacman[i % len(rotated_pacman)]
                        + Fore.RESET
                    )
                    line[right] = color_r

                if right < width - 1:
                    line[right + 1] = " "

                frames.append(
                    Style.BRIGHT + "  " + "".join(line) + Style.RESET_ALL
                )

            SPINNERS[titel] = {
                "interval": 50,
                "frames": frames,
            }

        return Spinner(titel, speed=0.5)

    def stope(self) -> None:
        """Signal stop event, join background thread, and close log file."""
        self._stop_event.set()
        if self._worker.is_alive():
            self._worker.join(timeout=1.0)
        try:
            if not self._logs_file.closed:
                self._logs_file.close()
        except Exception:
            pass

    def _warn(self) -> None:
        """Worker loop that drives live terminal spinner animations."""
        with Live(
            self._get_spinners(),
            refresh_per_second=15,
            vertical_overflow="visible",
            transient=True,
        ) as animation:
            while not self._stop_event.is_set():
                animation.update(self._get_spinners())
                self._stop_event.wait(0.05)

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

    @staticmethod
    def _gen_line_spinner(msg: str, log_type: LogType) -> Spinner:
        """Generate an animated typewriter spinner for a message line.

        Args:
            msg: Message text.
            log_type: Severity type of the message.

        Returns:
            Spinner: Constructed animated line spinner.
        """
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

        for i in range(len(msg)):
            arr = arrows_frames[i % len(arrows_frames)]
            log_str = (
                f"    {log_type.ansi()}{spaces}"
                f"{Fore.LIGHTCYAN_EX}{arr}{Fore.RESET}    "
            )

            char = msg[i].upper() if msg[i].isalpha() else msg[i]

            animated_msg = (
                Fore.YELLOW
                + msg[:i]
                + Fore.RESET
                + color
                + char
                + Style.RESET_ALL
                + msg[i + 1:]
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
        arrows = "▸▸▸▸▸"
        log = f"[{title}]{log_type.text()}   {arrows}   {msg}"
        print(log, file=self._logs_file)
        self._logs_file.flush()

    def log(
        self,
        msg: str,
        titel: str = "Warning",
        log_type: LogType = LogType.WARNING,
    ) -> None:
        """Record and display a log message.

        Args:
            msg: The message content to log.
            titel: Component or context category.
            log_type: Log severity type (WARNING or INFO).
        """
        self._save_log(msg, titel, log_type)
        with self._lock:
            poped_box = None
            if titel in self._tables:
                poped_box = self._tables[titel].pop()
            else:
                self._tables[titel] = [
                    Spinner("b_top"),
                    self._gen_titel_spinner(titel),
                    "",
                ]

            spinners_counter = len(self._tables[titel]) - 1

            if spinners_counter // 2 >= 10:
                self._tables[titel] = [
                    Spinner("b_top"),
                    self._gen_titel_spinner(titel),
                    "",
                ]

            fallback_box = poped_box if poped_box else Spinner("b_bottom")
            self._tables[titel].extend([
                self._gen_line_spinner(msg, log_type),
                "",
                fallback_box,
            ])

    def stop(self) -> None:
        """Stop the background animation loop."""
        self.stope()

    def _get_spinners(self) -> Group:
        """Aggregate all active spinners into a Rich renderable Group.

        Returns:
            Group: Unified renderable console group.
        """
        with self._lock:
            all_spinners = []
            for spinners in self._tables.values():
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
