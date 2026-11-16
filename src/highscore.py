"""Leaderboard and highscore manager for persisting player scores."""

import json
import re
from .logger import log, LogType
from .data_dir import DATA_DIR


class HighscoreManager:
    """Manages loading, validating, and persisting highscores to disk."""

    def __init__(self) -> None:
        """Initialize the highscore manager and load highscores from disk."""
        self._file_path = DATA_DIR / "highscores.json"
        self._scores: dict[str, int] = {}

        if (
            not self._file_path.exists()
            or not self._file_path.is_file()
            or self._file_path.suffix != ".json"
        ):
            log(
                f"Missing '{self._file_path.name}', using empty board",
                "Highscore",
                LogType.WARNING,
            )
            return

        try:
            data = json.loads(self._file_path.read_text(encoding="utf-8"))

            if not isinstance(data, dict) or not data:
                log(
                    f"Invalid '{self._file_path.name}', using empty board",
                    "Highscore",
                    LogType.WARNING,
                )
                return

            cleaned_data = {}
            for name, score in data.items():
                if (
                    isinstance(name, str)
                    and isinstance(score, int)
                    and not isinstance(score, bool)
                ):
                    cleaned_data[name] = score
                else:
                    log(
                        f"Skipped invalid entry ({name!r}: {score!r})",
                        "Highscore",
                        LogType.WARNING,
                    )

            self._scores = cleaned_data
            log(
                f"Loaded {len(self._scores)} highscores",
                "Highscore",
                LogType.INFO,
            )

        except (json.JSONDecodeError, OSError, AttributeError) as err:
            log(
                f"Parse error ({err.__class__.__name__}), resetting",
                "Highscore",
                LogType.WARNING,
            )

    @property
    def has_scores(self) -> bool:
        """Check whether any highscore entries exist.

        Returns:
            bool: True if at least one score exists, False otherwise.
        """
        return bool(self._scores)

    def get_top_scores(self, limit: int = 10) -> list[tuple[str, int]]:
        """Return top scores sorted in descending order.

        Args:
            limit: Maximum number of leaderboard entries to return.

        Returns:
            list[tuple[str, int]]: List of (name, score) tuples.
        """
        return sorted(
            self._scores.items(), key=lambda item: item[1], reverse=True
        )[:limit]

    @staticmethod
    def _is_valid(name: str, score: int) -> tuple[bool, str]:
        """Validate candidate player name and score.

        Args:
            name: Candidate player name.
            score: Candidate numeric score.

        Returns:
            tuple[bool, str]: (is_valid, error_message).
        """
        cleaned_name = name.strip()

        if len(cleaned_name) > 10:
            warn_msg = f"Name '{cleaned_name}' too long (max 10)"
            log(warn_msg, "Highscore", LogType.WARNING)
            return False, warn_msg

        if type(score) is not int or score < 0:
            warn_msg = f"Invalid score {score!r}, must be >= 0"
            log(warn_msg, "Highscore", LogType.WARNING)
            return False, warn_msg

        invalid_pattern = r"[^a-zA-Z0-9 ]+"
        if not cleaned_name or re.search(invalid_pattern, cleaned_name):
            warn_msg = f"Name '{cleaned_name}' invalid (letters/digits)"
            log(warn_msg, "Highscore", LogType.WARNING)
            return False, warn_msg

        return True, ""

    def save(self, name: str, score: int) -> tuple[bool, str]:
        """Validate, update, and persist a player's score to disk.

        Args:
            name: Player name.
            score: Numeric score achieved.

        Returns:
            tuple[bool, str]: (success, status_or_error_message).
        """
        name = name.strip()

        is_valid, warn_msg = HighscoreManager._is_valid(name, score)
        if not is_valid:
            return False, warn_msg

        if name in self._scores:
            old_score = self._scores[name]
            if score > old_score:
                warn_msg = (
                    f"New record for '{name}': {score} (was {old_score})"
                )
                log(warn_msg, "Highscore", LogType.INFO)
                self._scores[name] = score
            else:
                warn_msg = (
                    f"Score {score} not higher than best ({old_score})"
                )
                log(warn_msg, "Highscore", LogType.WARNING)
                return False, warn_msg
        else:
            self._scores[name] = score

        top10_highscores = dict(self.get_top_scores(10))

        try:
            self._file_path.write_text(
                json.dumps(top10_highscores, indent=2),
                encoding="utf-8",
            )
            log(
                f"Saved '{name}': {score} pts",
                "Highscore",
                LogType.INFO,
            )
        except OSError as err:
            warn_msg = f"Save failed ({err.__class__.__name__})"
            log(warn_msg, "Highscore", LogType.WARNING)
            return False, warn_msg

        return True, ""
