from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from orchestra.interfaces import KnowledgeInterface


class MenuService(KnowledgeInterface):
    """Service for accessing restaurant menu data."""

    def __init__(self) -> None:
        self._menu_file = Path(__file__).resolve().parent / "menu" / "restaurant_menu.json"

    def load_menu(self) -> Dict[str, Any]:
        """Load the restaurant menu from the packaged JSON file."""
        with self._menu_file.open("r", encoding="utf-8") as f:
            return json.load(f)


def load_menu() -> Dict[str, Any]:
    """Convenience wrapper to load the menu using the default service."""
    return MenuService().load_menu()
