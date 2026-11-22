"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

This file is part of The Discord Math Problem Bot Repo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
"""
import os
import tempfile
import unittest
from helpful_modules.constants_loader import BotConstants  # Replace with your actual module name


def test_load_from_env_file(tmp_path):
    # Create a temporary .env file using pytest's tmp_path fixture
    env_content = """
mysql_username=test_user
mysql_password=test_password
mysql_db_ip=127.0.0.1
mysql_db_name=test_db
DISCORD_TOKEN=test_token_123
use_sqlite=True
sqlite_database_path=test.db
source_code_link=https://github.com/example/repo
"""
    env_file = tmp_path / ".env"
    env_file.write_text(env_content.strip())

    # Initialize BotConstants with the temp file path
    constants = BotConstants(env_path=str(env_file))

    # Assert that all attributes are loaded correctly using plain assert statements
    assert constants.MYSQL_USERNAME == "test_user"
    assert constants.MYSQL_PASSWORD == "test_password"
    assert constants.MYSQL_DB_IP == "127.0.0.1"
    assert constants.MYSQL_DB_NAME == "test_db"
    assert constants.DISCORD_TOKEN == "test_token_123"
    assert constants.USE_SQLITE is True
    assert constants.SQLITE_DB_PATH == "test.db"
    assert constants.SOURCE_CODE_LINK == "https://github.com/example/repo"


def test_use_sqlite_false_parsing(tmp_path):
    # Test that 'use_sqlite' handles non-True values correctly (e.g., "False")
    env_file = tmp_path / ".env"
    env_file.write_text("use_sqlite=False\n")

    constants = BotConstants(env_path=str(env_file))
    assert constants.USE_SQLITE is False