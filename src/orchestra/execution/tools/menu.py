from langchain_core.tools import tool
from typing import List, Dict, Any


@tool
def get_menu() -> Dict[str, Any]:
    """Return the current menu"""
    # TODO: Load menu from data store
    return {"menu": "TODO: Implement menu retrieval"}


@tool
def search_menu_item(item: str) -> Dict[str, Any]:
    """Search for a menu item"""
    # TODO: Implement search logic
    return {"item": item, "found": False}


@tool
def get_business_hours() -> Dict[str, str]:
    """Return business hours"""
    # TODO: Implement business hours retrieval
    return {"hours": "TODO: Implement business hours"}
