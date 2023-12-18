import unittest
from helpful_modules import StatsTrack


class TestCommandUsage(unittest.TestCase):
    def test_to_dict(self):
        test_class = StatsTrack.CommandUsage(user_id=3, command_name="haha", time=-1.0)

        self.assertEqual(test_class.to_dict(), {"user_id": 3, "command_name": "haha", "time": -1.0})
    def test_from_dict(self):
        test_class = StatsTrack.CommandUsage(user_id=3, command_name="haha", time=-1.0)
        self.assertEqual(StatsTrack.CommandUsage.from_dict({"user_id": 3, "command_name": "haha", "time": -1.0}),test_class)

if __name__=="__main__":
    unittest.main()