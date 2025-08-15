import sys
from pathlib import Path

# Ensure the src package is on the Python path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

from orchestra.execution.menu import load_menu


def test_load_menu_contains_appetizers():
    menu = load_menu()
    assert 'Appetizers' in menu
