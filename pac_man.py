from src.errors import setup_warnings
from pathlib import Path
from src.config import Config
from src.highscore import HighscoreManager

setup_warnings()

def main() -> None:
    path = Path("config.json")
    config = Config.from_file(path)
    highscoremanager = HighscoreManager(config.highscore_filename)
    highscoremanager.save("yssuiui", 909090)
    print(highscoremanager.get_top_scores())
    

if __name__ == "__main__":
    main()
