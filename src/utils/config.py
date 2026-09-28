from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "zones.json"


def load_zones():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)
