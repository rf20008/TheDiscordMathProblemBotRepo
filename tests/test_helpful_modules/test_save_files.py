#  The Discord Math Problem Bot
#  A discord bot made mostly for ay136416's fun, but also to show math problems
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# TODO: there will be issues with files
import unittest
from unittest.mock import mock_open, MagicMock, patch, AsyncMock
from helpful_modules.save_files import FileSaver
from helpful_modules.problems_module import RedisCache
import pyfakefs
from pyfakefs import fake_filesystem_unittest

class TestSaveFiles(fake_filesystem_unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        self.saver = FileSaver(name="TestSaver")
        self.mock_cache = AsyncMock(spec=RedisCache)
        self.setUpPyfakefs()

    def test_enable_and_disable(self):
        """Test enabling and disabling the FileSaver."""
        self.saver.disable()
        self.assertFalse(self.saver.enabled)
        self.saver.enable()
        self.assertTrue(self.saver.enabled)

    def test_disable_prevents_load(self):
        """Test that disabling the FileSaver prevents loading files."""
        self.saver.disable()
        self.assertFalse(self.saver.enabled, "expected saver to be disabled")
        self.assertRaises(
            RuntimeError,
            self.saver.load_files,
            AsyncMock(spec=RedisCache)
        )
        self.assertRaises(TypeError, self.saver.load_files, "hehe boi")

    def test_disable_prevents_save(self):
        """Test that disabling the FileSaver prevents saving files."""
        self.saver.disable()
        self.assertFalse(self.saver.enabled, "expected saver to be disabled")
        self.assertRaises(RuntimeError, self.saver.save_files, self.mock_cache)
        self.assertRaises(TypeError, self.saver.save_files, "hehe boi")


    @patch('builtins.print')  # Mock the print function
    def test_load_files(self, mock_print):
        """Test loading files with mock data."""
        # create the saver
        file_saver = FileSaver(enabled=True, printSuccessMessagesByDefault=True)
        # make sure it's enabled
        self.assertTrue(file_saver.enabled)
        # we need a cache
        main_cache = self.mock_cache  # Assuming you have a MockMathProblemCache class for testing

        # Prepare files
        with open("math_problems.json", "w") as f:
            f.write("{\"example_key\": \"example_value\"}")
        with open("vote_threshold.txt", "w") as f:
            f.write("3")
        with open("trusted_users.txt", "w") as f:
            f.write("0")
        with open("guild_math_problems.json", "w") as f:
            f.write("{}")
        # Now we can test!
        result = file_saver.load_files(main_cache, printSuccessMessages=True)

        expected_result = {
            "guildMathProblems": {},
            "trusted_users": [0],
            "mathProblems": {"example_key": "example_value"},
            "vote_threshold": 3,
        }
        # now we need to delete the files
        self.fs.root.remove_entry("guild_math_problems.json")
        self.fs.root.remove_entry("vote_threshold.txt")
        self.fs.root.remove_entry("math_problems.json")
        self.fs.root.remove_entry("trusted_users.txt")
        self.assertRaises(Exception, open, "guild_math_problems.json")
        self.assertRaises(Exception, open, "vote_threshold.txt")
        self.assertRaises(Exception, open, "math_problems.json")
        self.assertRaises(Exception, open, "trusted_users.txt")
        # now we can actually test
        self.assertEqual(result, expected_result)
        mock_print.assert_called_with(f"{file_saver.name}: Successfully loaded files.")


    @patch("builtins.print")
    def test_save_files(self, mock_print):
        self.saver.enable()
        self.assertTrue(self.saver.enabled)
        result = self.saver.save_files(
            main_cache=self.mock_cache,
            trusted_users_list=[-1],
            vote_threshold = 13,
            math_problems_dict = {"1": "3"},
            guild_math_problems_dict = {"1": "3"},
            printSuccessMessages=True
        )

        self.assertIs(result, None)
        with open("trusted_users.txt", "r") as f: # type: ignore
            self.assertEqual(f.readline(), "-1\n")
        self.fs.root.remove_entry("trusted_users.txt")
        with open("vote_threshold.txt", "r") as f:
            self.assertEqual(f.readline(), "13")
        self.fs.root.remove_entry("vote_threshold.txt")
        with open("math_problems.json", "r") as f:
            self.assertEqual(f.readline().replace("'", '"'), """{"1": "3"}""")
        self.fs.root.remove_entry("math_problems.json")
        with open("guild_math_problems.json", "r") as f:
            self.assertEqual(f.readline().replace("'", '"'), """{"1": "3"}""")
        self.fs.root.remove_entry("guild_math_problems.json")
        mock_print.assert_called_with(f"{self.saver.name}: Successfully saved files.")
        # TODO: add another test to make sure mock_print isn't printed when printSuccessMessages=False

    def test_my_id(self):
        """Test the my_id method of FileSaver."""
        self.saver.enable()
        self.assertEqual(self.saver.my_id(), self.saver.id)
    def test_my_name(self):
        """Test changing and retrieving the name of FileSaver."""
        self.assertEqual(self.saver.name, "TestSaver")
        self.saver.change_name("TestSaver3")
        self.assertEqual(self.saver.name, "TestSaver3")
        self.saver.change_name("1")
        self.assertEqual(self.saver.name, '1')
        self.saver.change_name("TestSaver")
        self.assertEqual(self.saver.name, "TestSaver")

    def test_goodbye(self):
        """Test the goodbye method of FileSaver."""
        with patch('builtins.print') as mock_print:
            self.saver.goodbye()

        mock_print.assert_called_with(f"{str(self.saver)}: Goodbye.... :(")

if __name__=="__main__":
    unittest.main()