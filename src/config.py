from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from errors import PacmanConfigWarning
from lark import Lark
from warnings import warn
import random


@dataclass(frozen=True)
class LevelConfig:
    level: int
    width: int
    height: int
    pacgum: int
    level_max_time: int
    frightened_duration: float
    ghost_speed: float
    seed: int


@dataclass(frozen=True)
class Config:
    width: int = 15
    height: int = 15
    lives: int = 3
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    frightened_duration: float = 8.0
    ghost_speed: float = 3.0
    pacman_speed: float = 3.0
    seed: int = 42
    level_max_time: int = 90
    highscore_filename: str = Path("highscores.json")

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        # --- File System Checks ---
        if not path.exists():
            warn(
                f"Config file not found at '{path}'. Fallback to default configuration.",
                category=PacmanConfigWarning,
                stacklevel=2,
            )
            return cls()

        if not path.is_file():
            warn(
                f"Path '{path}' is not a regular file (directory or link). Fallback to default configuration.",
                category=PacmanConfigWarning,
                stacklevel=2,
            )
            return cls()

        if path.suffix != ".json":
            warn(
                f"Config file '{path.name}' must have a '.json' extension (got '{path.suffix}'). Fallback to default configuration.",
                category=PacmanConfigWarning,
                stacklevel=2,
            )
            return cls()

        # --- Reading & Parsing ---
        try:
            raw_text = path.read_text()
            clean_text = cls._strip_comments(raw_text)

            raw_dict = json.loads(clean_text)
            if not isinstance(raw_dict, dict):
                warn(
                    f"Root JSON element in '{path.name}' must be an object/dict (got {type(raw_dict).__name__}). Fallback to default configuration.",
                    category=PacmanConfigWarning,
                    stacklevel=2,
                )
                return cls()

            clamped_data = cls._clamp_defaults(raw_dict)
            return cls(**clamped_data)

        except json.JSONDecodeError as err:
            warn(
                f"Invalid JSON syntax in '{path.name}' at line {err.lineno}, col {err.colno}: {err.msg}. Fallback to default configuration.",
                category=PacmanConfigWarning,
                stacklevel=2,
            )
            return cls()

        except Exception as err:
            warn(
                f"Unexpected error while loading '{path.name}' ({err.__class__.__name__}: {err}). Fallback to default configuration.",
                category=PacmanConfigWarning,
                stacklevel=2,
            )
            return cls()

    @staticmethod
    def _strip_comments(raw: str) -> str:
        grammar = r"""
            start: (STRING | OTHER)+

            STRING: ESCAPED_STRING

            COMMENT: /#[^\n]*/
            CPP_COMMENT: /\/\/[^\n]*/
            C_COMMENT: /\/\*[\s\S]*?\*\//

            OTHER: /[^"#\/]+/ | /\/(?![*\/])/

            %ignore COMMENT
            %ignore CPP_COMMENT
            %ignore C_COMMENT

            %import common.ESCAPED_STRING
        """

        tree = Lark(grammar, parser="earley").parse(raw)

        return "".join(child.value for child in tree.children)

    @staticmethod
    def _clamp_defaults(data: dict) -> dict:
        clamped: dict[str, Any] = {
            "width": 15,
            "height": 15,
            "lives": 3,
            "points_per_pacgum": 10,
            "points_per_super_pacgum": 50,
            "points_per_ghost": 200,
            "frightened_duration": 8.0,
            "ghost_speed": 3.0,
            "pacman_speed": 3.0,
            "seed": 42,
            "level_max_time": 90,
            "highscore_filename": Path("highscores.json")
        }

        def validate_int_field(key: str, min_val: int | None = None, strictly_positive: bool = False):
            if key not in data:
                warn(
                    f"Missing '{key}' in config. Using default: {clamped[key]}.",
                    category=PacmanConfigWarning,
                    stacklevel=3,
                )
                return

            val = data[key]
            is_valid = isinstance(val, int) and not isinstance(val, bool)

            if is_valid and min_val is not None:
                is_valid = val >= min_val
            elif is_valid and strictly_positive:
                is_valid = val > 0

            if is_valid:
                clamped[key] = val
            else:
                condition_msg = f">= {min_val}" if min_val is not None else ("> 0" if strictly_positive else "an integer")
                warn(
                    f"Invalid value for '{key}': got {val!r}, expected {condition_msg}. Using default: {clamped[key]}.",
                    category=PacmanConfigWarning,
                    stacklevel=3,
                )

        validate_int_field("width", min_val=7)
        validate_int_field("height", min_val=7)
        validate_int_field("lives", min_val=1)
        validate_int_field("points_per_pacgum", min_val=0)
        validate_int_field("points_per_super_pacgum", min_val=0)
        validate_int_field("points_per_ghost", min_val=0)
        validate_int_field("seed")
        validate_int_field("level_max_time", strictly_positive=True)

        if "frightened_duration" in data:
            match data["frightened_duration"]:
                case (float() | int()) as value if value >= 0:
                    clamped["frightened_duration"] = value
                case _:
                    warn()
        else:
            warn()
        
        if "ghost_speed" in data:
            match data["ghost_speed"]:
                case (float() | int()) as value if value >= 0:
                    clamped["ghost_speed"] = data["ghost_speed"]
                case _:
                    warn()
        else:
            warn()

        if "pacman_speed" in data:
            match data["pacman_speed"]:
                case (float() | int()) as value if value >= 0:
                    clamped["pacman_speed"] = data["pacman_speed"]
                case _:
                    warn()
        else:
            warn()


        if "highscore_filename" not in data:
            warn(
                f"Missing 'highscore_filename' in config. Using default: '{clamped['highscore_filename']}'.",
                category=PacmanConfigWarning,
                stacklevel=2,
            )
        else:
            raw_path = data["highscore_filename"]
            if not isinstance(raw_path, str):
                warn(
                    f"Invalid 'highscore_filename': got {raw_path!r}, expected a string path. Using default: '{clamped['highscore_filename']}'.",
                    category=PacmanConfigWarning,
                    stacklevel=2,
                )
            else:
                clamped["highscore_filename"] = Path(raw_path)

        return clamped

    def generate_level(self, level: int) -> LevelConfig:
        return LevelConfig(
            level=level,
            level_max_time=max(45, self.level_max_time - (level - 1) * 3),
            frightened_duration=max(2.0, self.frightened_duration - (level - 1) * 0.5),
            ghost_speed=min(4.8, self.ghost_speed + (level - 1) * 0.1),
            seed=self.seed if level == 1 else random.randint(1, 1_000_000)
        )
