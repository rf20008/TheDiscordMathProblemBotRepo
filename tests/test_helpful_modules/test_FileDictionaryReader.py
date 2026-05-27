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
import asyncio
import json
import unittest
import unittest.mock

import func_timeout
from pyfakefs import fake_filesystem_unittest

from helpful_modules.FileDictionaryReader import AsyncFileDict
from tests.mockable_aiofiles import MockableAioFiles


class TestAsyncFileDict(fake_filesystem_unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()

    def setUp(self) -> None:
        self.setUpPyfakefs()

    def test_init(self):
        with unittest.mock.patch("asyncio.run") as mock_run:
            afd = AsyncFileDict(filename="test.json")
            mock_run.assert_not_called()
            self.assertEqual(afd.filename, "test.json")
            self.assertEqual(afd.dict, {})
            afd = AsyncFileDict(filename="test2.json", overwrite=True)
            mock_run.assert_called()
            self.assertEqual(afd.filename, "test2.json")
            self.assertEqual(afd.dict, {})

    def test_update_file(self):
        func_timeout.func_timeout(
            timeout=0.75,
            func=self.loop.run_until_complete,
            args=(self.update_file_test(),),
        )

    @unittest.mock.patch("aiofiles.open", wraps=MockableAioFiles)
    async def update_file_test(self, mock_aiofiles_open):
        afd = AsyncFileDict(filename="haha.json")
        await afd.update_my_file()
        with open("haha.json", "rb") as file:
            stuff = file.read()
            self.assertEqual(stuff, bytes(json.dumps({}), "utf-8"))
        afd.dict = {"hehe boi": 123456789}
        await afd.update_my_file()
        with open("haha.json", "rb") as file:
            stuff = file.read()
            self.assertEqual(stuff, bytes(json.dumps({"hehe boi": 123456789}), "utf-8"))
        self.setUpPyfakefs()

    def test_read_file(self):
        func_timeout.func_timeout(
            timeout=0.75,
            func=self.loop.run_until_complete,
            args=(self.read_file_test(),),
        )

    @unittest.mock.patch("aiofiles.open", wraps=MockableAioFiles)
    async def read_file_test(self, mock_aiofiles_open):
        afd = AsyncFileDict(filename="haha.json")

        with open("haha.json", "w") as file:
            file.write('{"123456789": "hehe boi"}')
        await afd.read_from_file()
        self.assertEqual(afd.dict, {"123456789": "hehe boi"})
        afd.dict["OH NO"] = 314159
        await afd.update_my_file()
        with open("haha.json", "r") as file:
            stuff = file.read()
            self.assertIn(
                stuff,
                (
                    '{"123456789": "hehe boi", "OH NO": 314159}',
                    '{"OH NO": 314159,"123456789": "hehe boi"}',
                ),
            )
        bef = afd.dict
        await afd.read_from_file()
        self.assertEqual(bef, afd.dict)
        self.assertEqual(afd.dict, {"123456789": "hehe boi", "OH NO": 314159})

    def test_get_and_set_key(self):
        func_timeout.func_timeout(
            timeout=0.75,
            func=self.loop.run_until_complete,
            args=(self.get_and_set_test(),),
        )

    @unittest.mock.patch("aiofiles.open", wraps=MockableAioFiles)
    async def get_and_set_test(self, mock_open):
        afd = AsyncFileDict(filename="haha.json")
        await afd.set_key(key="13", val="1000")
        self.assertEqual(afd.dict, {"13": "1000"})
        with open("haha.json", "r") as file:
            self.assertEqual(file.read(-1).replace("'", '"'), '{"13": "1000"}')
        self.assertEqual(await afd.get_key(key="13"), "1000")

    def test_del_key(self):
        func_timeout.func_timeout(
            timeout=0.75, func=self.loop.run_until_complete, args=(self.del_key_test(),)
        )

    @unittest.mock.patch("aiofiles.open", wraps=MockableAioFiles)
    async def del_key_test(self, mock_update):
        afd = AsyncFileDict(filename="haha.json", overwrite=False)
        afd.dict = {"key1": "value1", "key2": "value2"}
        await afd.del_key("key1")
        self.assertNotIn("key1", afd.dict)
        self.assertIn("key2", afd.dict)
        mock_update.assert_called()

    def test_iter(self):
        afd = AsyncFileDict(filename="haha.json", overwrite=False)
        afd.dict = {"key1": "value1", "key2": "value2"}
        keys = list(afd)
        self.assertListEqual(keys, ["key1", "key2"])

    def test_keys(self):
        afd = AsyncFileDict(filename="haha.json", overwrite=False)
        afd.dict = {"key1": "value1", "key2": "value2"}
        keys = afd.keys()
        self.assertSetEqual(set(keys), {"key1", "key2"})

    def test_values(self):
        afd = AsyncFileDict(filename="haha.json", overwrite=False)
        afd.dict = {"key1": "value1", "key2": "value2"}
        values = afd.values()
        self.assertSetEqual(set(values), {("key1", "value1"), ("key2", "value2")})

    def test_items(self):
        afd = AsyncFileDict(filename="haha.json", overwrite=False)
        afd.dict = {"key1": "value1", "key2": "value2"}
        items = afd.items()
        self.assertSetEqual(set(items), {("key1", "value1"), ("key2", "value2")})


if __name__ == "__main__":
    unittest.main()
