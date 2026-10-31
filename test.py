from src.config import Config
from src.engine import GameEngine, EngineState, Cheat
from src.entities import Direction, GhostState
from src.consumables import Consumable, SuperPacGum, PacGum
from src.highscore import HighscoreManager
from src.errors import setup_warnings
from pathlib import Path

setup_warnings()

engine = GameEngine(Config.from_file(Path("config.json")))
# engine._save_states()
engine._load_states()
print(engine._state)