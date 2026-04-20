import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Any

try: 
    SUDOKU_DIR = Path(__file__).parents[2]
except:
    SUDOKU_DIR = Path.cwd()

CONFIG_FILE = SUDOKU_DIR / "src" / "settings.json"
SAVE_FILE_PATH = (SUDOKU_DIR / "gallery")
if not SAVE_FILE_PATH.exists():
    SAVE_FILE_PATH.mkdir(parents=True, exist_ok=True)

IMAGE_EXTS = (".bmp", ".dib", ".jpeg", ".jpg", ".jpe", ".jp2",
              ".png", ".webp", ".pbm", ".pgm", ".ppm", ".pxm", ".pnm",
              ".tiff", ".tif", ".exr", ".hdr", ".pic")

DEFAULTS = {
    "display_solved_image": True,
    "unique_solution": True,
    "save_solved_image": False,
    "save_file_path": str(SAVE_FILE_PATH),
    "verbose": False,
    "debug": False,
}

def load_settings() -> dict:
    if not CONFIG_FILE.exists():
        save_settings(DEFAULTS)
        return DEFAULTS
    try:
        with open(CONFIG_FILE, "r") as f:
            saved = json.load(f)
    except json.JSONDecodeError:
        os.remove(CONFIG_FILE.__str__())
        save_settings(DEFAULTS)
        return DEFAULTS

    return {**DEFAULTS, **saved}
    
def save_settings(settings: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(settings, f, indent=2)

@dataclass
class Settings():
    def __init__(self, *args, **kwargs) -> None:
        self.load_settings()
        if kwargs:
            for key, value in kwargs.items():
                self.__setattr__(key, value)

    def load_settings(self):
        values = load_settings()
        for key, value in values.items():
            self.__setattr__(key, value)

    def save_settings(self):
        save_settings(self.__dict__)

    def __getitem__(self, key) -> Any:
        return self.__getattribute__(key)
    
    def __setitem__(self, key, value):
        self.__setattr__(key, value)
        self.save_settings()
        return None
        
    def __repr__(self) -> str:
        return f"Settings({", ".join([f'\"{key}\": {value}' for key, value in self.__dict__.items()])})"

settings = Settings()