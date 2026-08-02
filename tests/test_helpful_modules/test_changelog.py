"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

This file is part of TheDiscordMathProblemBotRepo

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

import unittest
import tempfile
import os
import json
import asyncio
import datetime

from helpful_modules.changelog import (
    ChangeLogEntry,
    ChangeLogManager,
    create_log_entry_from_file,
)


class TestChangeLogEntry(unittest.TestCase):
    def test_valid_creation(self):
        entry = ChangeLogEntry(
            patchNotes=["Fixed bug", "Added feature"],
            old="1.0",
            new="1.1",
            date_released=1710000000,
        )

        self.assertEqual(entry.old_version, "1.0")
        self.assertEqual(entry.new_version, "1.1")
        self.assertEqual(entry.patch_notes, ["Fixed bug", "Added feature"])

    def test_invalid_timestamp(self):
        with self.assertRaises(TypeError):
            ChangeLogEntry(
                patchNotes=["x"],
                old="1",
                new="2",
                date_released="not a timestamp",
            )

    def test_to_dict(self):
        entry = ChangeLogEntry(
            patchNotes=["A", "B"],
            old="1.0",
            new="2.0",
            date_released=1710000000,
        )

        data = entry.to_dict()

        self.assertEqual(data["patch_notes"], ["A", "B"])
        self.assertEqual(data["old"], "1.0")
        self.assertEqual(data["new"], "2.0")

    def test_from_dict(self):
        data = {
            "patch_notes": ["Test note"],
            "old": "1.0",
            "new": "1.1",
            "date_released": 1710000000,
        }

        entry = ChangeLogEntry.from_dict(data)

        self.assertEqual(entry.patch_notes, ["Test note"])
        self.assertEqual(entry.old_version, "1.0")
        self.assertEqual(entry.new_version, "1.1")
        self.assertEqual(entry.date_released, 1710000000)


class TestCreateLogEntryFromFile(unittest.TestCase):
    def test_create_entries(self):
        data = {
            "0": {
                "patch_notes": ["A"],
                "old": "1.0",
                "new": "1.1",
                "date_released": 1710000000,
            },
            "1": {
                "patch_notes": ["B"],
                "old": "1.1",
                "new": "1.2",
                "date_released": 1710000100,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            json.dump(data, tmp)
            tmp.seek(0)

            entries = create_log_entry_from_file(tmp)

        os.unlink(tmp.name)

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].old_version, "1.0")
        self.assertEqual(entries[1].new_version, "1.2")


class TestChangeLogManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.NamedTemporaryFile(mode="w+", delete=False)

        json.dump({}, self.temp)
        self.temp.close()

        self.manager = ChangeLogManager(self.temp.name)

    async def asyncTearDown(self):
        os.unlink(self.temp.name)

    async def test_load_files(self):
        data = {
            "0": {
                "patch_notes": ["Hello"],
                "old": "1.0",
                "new": "1.1",
                "date_released": 1710000000,
            }
        }

        with open(self.temp.name, "w") as f:
            json.dump(data, f)

        logs = await self.manager.load_files()

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].new_version, "1.1")

    async def test_add_changelog(self):
        entry = ChangeLogEntry(
            patchNotes=["New feature"],
            old="1.0",
            new="1.1",
            date_released=1710000000,
        )

        await self.manager.add_changelog(entry)

        with open(self.temp.name, "r") as f:
            content = json.load(f)

        self.assertTrue(len(content) > 0)

    async def test_create_changelog(self):
        data = {
            "patchNotes": ["A"],
            "old": "1.0",
            "new": "1.1",
            "date_released": 1710000000,
        }

        entry = await self.manager.create_changelog(data)

        self.assertEqual(entry.old_version, "1.0")


if __name__ == "__main__":
    unittest.main()
