from pathlib import Path
import unittest

def load_tests(loader, tests, pattern):
    # Discover from the project root (the folder containing manage.py)
    project_root = Path(__file__).resolve().parent.parent
    return loader.discover(str(project_root), pattern="test*.py")