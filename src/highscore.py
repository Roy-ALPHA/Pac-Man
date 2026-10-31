import json
from pathlib import Path
import re
from .logs import log, LogType


class HighscoreManager:

	def __init__(self, highscore_file: Path):
		self._file_path = highscore_file
		self._scores: dict = {}

		if (
			not self._file_path.exists()
			or not self._file_path.is_file()
			or self._file_path.suffix != ".json"
		):
			log(
				f"Invalid or missing file: '{self._file_path}'. Fallback: starting with an empty leaderboard.",
				"Highscore",
				LogType.WARNING,
			)
			return

		try:
			data = json.loads(self._file_path.read_text())

			if not isinstance(data, dict) or not data:
				log(
					f"File '{self._file_path.name}' is empty or not a valid JSON dict. Fallback: starting with an empty leaderboard.",
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
						f"Skipped invalid entry ({name!r}: {score!r}). Fallback: entry omitted from leaderboard.",
						"Highscore",
						LogType.WARNING,
					)

			self._scores = cleaned_data
			log(f"Loaded {len(self._scores)} highscore entries from '{self._file_path.name}'", "Highscore", LogType.INFO)

		except (json.JSONDecodeError, OSError, AttributeError) as err:
			log(
					f"Failed to read/parse highscore file: {err}. Fallback: starting with an empty leaderboard.",
					"Highscore",
					LogType.WARNING,
			)

	@property
	def has_scores(self) -> bool:
		return bool(self._scores)

	def get_top_scores(self, limit: int = 10):
		return sorted(self._scores.items(), key=lambda item: item[1], reverse=True)[
				:limit
		]

	@staticmethod
	def _is_valid(name: str, score: int):
		cleaned_name = name.strip()

		if len(cleaned_name) > 10:
			warn_msg = f"Name '{cleaned_name}' is too long (max 10 characters). Score rejected: not saved."
			log(warn_msg, "Highscore", LogType.WARNING)
			return False, warn_msg

		if type(score) is not int or score < 0:
			warn_msg = f"Score must be a positive integer, got {score!r}. Score rejected: not saved."
			log(warn_msg, "Highscore", LogType.WARNING)
			return False, warn_msg

		invalid_pattern = r"[^a-zA-Z0-9 ]+"
		if not cleaned_name or re.search(invalid_pattern, cleaned_name):
			warn_msg = (
				f"Name '{cleaned_name}' is empty or contains forbidden characters"
				" (alphanumeric and spaces only). Score rejected: not saved."
			)
			log(warn_msg, "Highscore", LogType.WARNING)
			return False, warn_msg

		return True, ""

	def save(self, name: str, score: int):
		name = name.strip()

		is_valid, warn_msg = HighscoreManager._is_valid(name, score)
		if not is_valid:
			return False, warn_msg

		if name in self._scores:
			old_score = self._scores[name]
			if score > old_score:
				warn_msg = (
					f"Player '{name}' already exists with score {old_score}. "
					f"Replacement: updated to new personal best {score}."
				)
				log(warn_msg, "Highscore", LogType.INFO)
				self._scores[name] = score
			else:
				warn_msg = (
					f"Player '{name}' already exists with higher score ({old_score} >= {score}). "
					f"Replacement: kept existing score {old_score}."
				)
				log(warn_msg, "Highscore", LogType.WARNING)
				return False, warn_msg
		else:
			self._scores[name] = score

		top10_highscores = dict(self.get_top_scores(10))

		try:
			self._file_path.write_text(
					json.dumps(top10_highscores, indent=2)
			)
			log(f"Successfully saved highscore for '{name}': {score} pts", "Highscore", LogType.INFO)
		except OSError as err:
			warn_msg = f"Failed to write scores to disk: {err}. Score changes retained in memory only."
			log(warn_msg, "Highscore", LogType.WARNING)
			return False, warn_msg

		return True, ""
