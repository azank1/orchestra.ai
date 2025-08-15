from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_menu() -> Dict[str, Any]:
    """Load the restaurant menu from the packaged JSON file."""
    menu_file = Path(__file__).resolve().parent / "menu" / "restaurant_menu.json"
    with menu_file.open("r", encoding="utf-8") as f:
        return json.load(f)
