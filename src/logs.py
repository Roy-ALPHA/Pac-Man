from rich.live import Live
from rich.spinner import Spinner, SPINNERS
from rich.console import Group
from colorama import Fore, Style
from enum import Enum, auto
import threading

class LogType(Enum):
    WARNING = auto()
    INFO = auto()

    def ansi(self):
        match self:
            case LogType.INFO:
                return f"{Fore.LIGHTGREEN_EX}{Style.BRIGHT}Info{Fore.RESET}"
            case LogType.WARNING:
                return f"{Fore.LIGHTRED_EX}{Style.BRIGHT}Warning{Fore.RESET}"

    def text(self):
        match self:
            case LogType.INFO:
                return "Info"
            case LogType.WARNING:
                return "Warning"


class WarningManager:
    _spinners = 0

    def __init__(self):
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._warn)
        self._tables = dict()
        self._logs_file = open("logs.txt", "w")
        WarningManager._gen_box(100)

    @classmethod
    def _gen_box(cls, width):
        box_top = list("┌" + "▱" * width + "┐")
        box_bottom = list("└" + "▱" * width + "┘")

        top_frames = []
        bottom_frames = []

        for i in range(width):

            box_top[i + 1] = "▰"
            box_bottom[width - i] = "▰"

            top_frames.append(Fore.LIGHTMAGENTA_EX + "".join(box_top) + Fore.RESET)
            bottom_frames.append(Fore.LIGHTMAGENTA_EX + "".join(box_bottom) + Fore.RESET)

        for i in range(width):

            box_top[width - i] = "▱"
            box_bottom[i + 1] = "▱"

            top_frames.append(Fore.LIGHTMAGENTA_EX + "".join(box_top) + Fore.RESET)
            bottom_frames.append(Fore.LIGHTMAGENTA_EX + "".join(box_bottom) + Fore.RESET)

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
    def _gen_titel_spinner(titel):
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
                    line[left] = Fore.LIGHTYELLOW_EX + pacman_frames[i % len(pacman_frames)] + Fore.RESET

                if left > 0:
                    line[left - 1] = " "

                if right < start or right >= start + len(title):
                    line[right] = Fore.LIGHTYELLOW_EX + rotated_pacman[i % len(rotated_pacman)] + Fore.RESET

                if right < width - 1:
                    line[right + 1] = " "

                frames.append(Style.BRIGHT + "  " + "".join(line) + Style.RESET_ALL)

            SPINNERS[titel] = {
                "interval": 50,
                "frames": frames,
            }

        return Spinner(titel, speed=0.5)

    def stope(self):
        self._stop_event.set()
        if self._worker.is_alive():
            self._worker.join(timeout=1.0)
        try:
            if not self._logs_file.closed:
                self._logs_file.close()
        except Exception:
            pass

    def _warn(self):
        with Live(self._get_spinners(), refresh_per_second=15, vertical_overflow="visible", transient=True) as animation:
            while not self._stop_event.is_set():
                animation.update(self._get_spinners())
                self._stop_event.wait(0.05)

    @classmethod
    def _create_spinner(cls, frames):
        spinner_name = f"spinner_{cls._spinners}"

        SPINNERS[spinner_name] = {
            "interval": 50,
            "frames": frames
        }

        cls._spinners += 1

        return spinner_name

    @staticmethod
    def _gen_line_spinner(msg, log_type):
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

        color = Fore.LIGHTGREEN_EX if log_type is LogType.INFO else Fore.LIGHTRED_EX

        for i in range(len(msg)):

            log = f"    {log_type.ansi()}{spaces}{Fore.LIGHTCYAN_EX}{arrows_frames[i % len(arrows_frames)]}{Fore.RESET}    "

            char = msg[i].upper() if msg[i].isalpha() else msg[i]

            animated_msg = (
                Fore.YELLOW + msg[:i] + Fore.RESET + color + char + Style.RESET_ALL + msg[i+1:]
            )

            frames.append(log + animated_msg)

        spinner_name = WarningManager._create_spinner(frames)

        return Spinner(
            spinner_name,
            speed=0.5
        )

    def _save_log(self, msg, title, log_type):
        arrows = "▸▸▸▸▸"
        log = f"[{title}]{log_type.text()}   {arrows}   {msg}"
        print(log, file=self._logs_file)
        self._logs_file.flush()

    def log(self, msg, titel="Warning", log_type=LogType.WARNING):
        self._save_log(msg, titel, log_type)
        with self._lock:
            poped_box = None
            if titel in self._tables:
                poped_box = self._tables[titel].pop()
            else:
                self._tables[titel] = [Spinner("b_top"), self._gen_titel_spinner(titel), ""]

            spinners_counter = len(self._tables[titel]) - 1

            if spinners_counter // 2 >= 10:
                self._tables[titel] = [Spinner("b_top"), self._gen_titel_spinner(titel), ""]

            self._tables[titel].extend([self._gen_line_spinner(msg, log_type), "", poped_box if poped_box else Spinner("b_bottom")])

    def stop(self):
        self.stope()

    def _get_spinners(self):
        with self._lock:
            all_spinners = []
            for spinners in self._tables.values():
                all_spinners.extend(spinners)

            return Group(*all_spinners)

    def start(self):
        if not self._worker.is_alive():
            self._worker.start()

    def join(self):
        self._worker.join()


warning_manager = WarningManager()
log = warning_manager.log
