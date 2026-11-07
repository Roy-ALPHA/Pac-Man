"""Configuration loader and level generator for the Pac-Man game."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random
from typing import Any
from lark import Lark, Token
from .logs import log, LogType
from .maze_adapter import MazeAdapter


@dataclass(frozen=True)
class LevelConfig:
    """Configuration settings for a specific gameplay level.

    Attributes:
        level: Level number (1-based index).
        frightened_duration: Duration in seconds for ghost frightened mode.
        ghost_speed: Movement speed of ghosts in tiles per second.
        seed: Random seed used to generate the level maze.
    """

    level: int
    frightened_duration: float
    ghost_speed: float
    seed: int


@dataclass(frozen=True)
class Config:
    """Global configuration settings for the Pac-Man game."""

    width: int = 15
    height: int = 15
    lives: int = 3
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    frightened_duration: float = 8.0
    ghost_speed: float = 3.0
    pacman_speed: float = 5.0
    seed: int = 42

    @classmethod
    def set_maze_size(cls, width: int, height: int) -> None:
        """Set the maze dimensions in the maze adapter.

        Args:
            width: Maze width in cells.
            height: Maze height in cells.
        """
        MazeAdapter.set_maze_size((width, height))

    @classmethod
    def from_file(cls, path: Path) -> Config:
        """Load and validate configuration from a JSON file.

        Args:
            path: Path to the JSON configuration file.

        Returns:
            Config: Loaded configuration or default fallback on error.
        """
        # --- File System Checks ---
        if not path.exists():
            log(
                f"Config file not found at '{path}'. "
                "Fallback to default configuration.",
                "Config",
                LogType.WARNING,
            )
            return cls()

        if not path.is_file():
            log(
                f"Path '{path}' is not a regular file (directory or link). "
                "Fallback to default configuration.",
                "Config",
                LogType.WARNING,
            )
            return cls()

        if path.suffix != ".json":
            log(
                f"Config file '{path.name}' must have a '.json' extension "
                f"(got '{path.suffix}'). Fallback to default configuration.",
                "Config",
                LogType.WARNING,
            )
            return cls()

        # --- Reading & Parsing ---
        try:
            raw_text = path.read_text(encoding="utf-8")
            clean_text = cls._strip_comments(raw_text)

            raw_dict = json.loads(clean_text)
            if not isinstance(raw_dict, dict):
                log(
                    f"Root JSON element in '{path.name}' must be an "
                    f"object/dict (got {type(raw_dict).__name__}). "
                    "Fallback to default configuration.",
                    "Config",
                    LogType.WARNING,
                )
                return cls()

            clamped_data = cls._clamp_defaults(raw_dict)
            cls.set_maze_size(clamped_data["width"], clamped_data["height"])
            log(
                f"Successfully loaded configuration from '{path.name}'",
                "Config",
                LogType.INFO,
            )
            return cls(**clamped_data)

        except json.JSONDecodeError as err:
            log(
                f"Invalid JSON syntax in '{path.name}' at line {err.lineno}, "
                f"col {err.colno}: {err.msg}. "
                "Fallback to default configuration.",
                "Config",
                LogType.WARNING,
            )
            return cls()

        except Exception as err:
            log(
                f"Unexpected error while loading '{path.name}' "
                f"({err.__class__.__name__}: {err}). "
                "Fallback to default configuration.",
                "Config",
                LogType.WARNING,
            )
            return cls()

    @staticmethod
    def _strip_comments(raw: str) -> str:
        """Strip C, C++, and Python comments from a JSON string.

        Args:
            raw: Raw JSON text containing comments.

        Returns:
            str: Clean JSON text without comments.
        """
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

        return "".join(
            child.value if isinstance(child, Token) else str(child)
            for child in tree.children
        )

    @staticmethod
    def _clamp_defaults(data: dict[str, Any]) -> dict[str, Any]:
        """Validate and clamp configuration values against default bounds.

        Args:
            data: Raw dictionary loaded from configuration JSON.

        Returns:
            dict[str, Any]: Dictionary with clamped and validated values.
        """
        clamped: dict[str, Any] = {
            "width": 15,
            "height": 15,
            "lives": 3,
            "points_per_pacgum": 10,
            "points_per_super_pacgum": 50,
            "points_per_ghost": 200,
            "frightened_duration": 8.0,
            "ghost_speed": 3.0,
            "pacman_speed": 5.0,
            "seed": 42,
        }

        def validate_int_field(
            key: str, min_val: int | None = None, max_val: int | None = None
        ) -> None:
            if key not in data:
                log(
                    f"Missing '{key}' in config. "
                    f"Using default: {clamped[key]}.",
                    "Config",
                    LogType.WARNING,
                )
                return

            val = data[key]
            is_valid = isinstance(val, int) and not isinstance(val, bool)

            if is_valid and min_val is not None:
                is_valid = val >= min_val
            if is_valid and max_val is not None:
                is_valid = val <= max_val

            if is_valid:
                clamped[key] = val
            else:
                if min_val is not None and max_val is not None:
                    condition_msg = f"between {min_val} and {max_val}"
                elif min_val is not None:
                    condition_msg = f">= {min_val}"
                elif max_val is not None:
                    condition_msg = f"<= {max_val}"
                else:
                    condition_msg = "an integer"
                log(
                    f"Invalid value for '{key}': got {val!r}, "
                    f"expected {condition_msg}. "
                    f"Using default: {clamped[key]}.",
                    "Config",
                    LogType.WARNING,
                )

        validate_int_field("width", min_val=7, max_val=40)
        validate_int_field("height", min_val=7, max_val=40)
        validate_int_field("lives", min_val=1)
        validate_int_field("points_per_pacgum", min_val=0)
        validate_int_field("points_per_super_pacgum", min_val=0)
        validate_int_field("points_per_ghost", min_val=0)
        validate_int_field("seed", min_val=1)

        if "frightened_duration" in data:
            match data["frightened_duration"]:
                case (float() | int()) as value if value >= 0:
                    clamped["frightened_duration"] = value
                case _:
                    log(
                        f"Invalid frightened_duration: "
                        f"{data['frightened_duration']!r}. "
                        f"Using default: {clamped['frightened_duration']}.",
                        "Config",
                        LogType.WARNING,
                    )
        else:
            log(
                "Missing frightened_duration in config. "
                f"Using default: {clamped['frightened_duration']}.",
                "Config",
                LogType.WARNING,
            )

        if "ghost_speed" in data:
            match data["ghost_speed"]:
                case (float() | int()) as value if value > 0:
                    clamped["ghost_speed"] = data["ghost_speed"]
                case _:
                    log(
                        f"Invalid ghost_speed: {data['ghost_speed']!r}. "
                        f"Using default: {clamped['ghost_speed']}.",
                        "Config",
                        LogType.WARNING,
                    )
        else:
            log(
                "Missing ghost_speed in config. "
                f"Using default: {clamped['ghost_speed']}.",
                "Config",
                LogType.WARNING,
            )

        if "pacman_speed" in data:
            match data["pacman_speed"]:
                case (float() | int()) as value if value > 0:
                    clamped["pacman_speed"] = data["pacman_speed"]
                case _:
                    log(
                        f"Invalid pacman_speed: {data['pacman_speed']!r}. "
                        f"Using default: {clamped['pacman_speed']}.",
                        "Config",
                        LogType.WARNING,
                    )
        else:
            log(
                "Missing pacman_speed in config. "
                f"Using default: {clamped['pacman_speed']}.",
                "Config",
                LogType.WARNING,
            )

        return clamped

    def generate_level(self, level: int) -> LevelConfig:
        """Generate level parameters with progressive difficulty.

        Args:
            level: The 1-based level index.

        Returns:
            LevelConfig: Configuration for the generated level.
        """
        fright_dur = max(
            2.0, self.frightened_duration - (level - 1) * 0.5
        )
        g_speed = min(4.8, self.ghost_speed + (level - 1) * 0.1)
        seed_val = self.seed if level == 1 else random.randint(1, 1_000_000)
        return LevelConfig(
            level=level,
            frightened_duration=fright_dur,
            ghost_speed=g_speed,
            seed=seed_val,
        )
