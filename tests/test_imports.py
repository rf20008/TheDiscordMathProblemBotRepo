import unittest
import sys
import importlib

class TestBotStartup(unittest.TestCase):
    def test_main_imports(self):
        sys.modules.pop("main", None)
        importlib.import_module("main")