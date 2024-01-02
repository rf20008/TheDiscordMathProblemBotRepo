import unittest
from disnake import Intents
from helpful_modules.return_intents import return_intents  # Make sure to replace 'your_module' with the actual module name

class TestReturnIntents(unittest.TestCase):
    def test_return_intents(self):
        result = return_intents()

        # Ensure the returned object is an instance of Intents
        self.assertIsInstance(result, Intents)

        # Check specific attributes of the Intents object
        self.assertFalse(result.typing)
        self.assertFalse(result.presences)
        self.assertFalse(result.members)
        self.assertFalse(result.reactions)
        self.assertFalse(result.bans)

if __name__ == '__main__':
    unittest.main()