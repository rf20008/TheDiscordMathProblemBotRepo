"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - ChangeLog

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""

import datetime
import io
import asyncio
import json
import typing as t
import os

def create_log_entry_from_file(file):
    entries = json.load(file)
    changelogs = []
    for entry in entries.values():
        changelogs.append(ChangeLogEntry.from_dict(entry))
    return changelogs

class ChangeLogEntry:
    def __init__(
        self, *, patchNotes: t.List[str], old: str, new: str, date_released: str
    ):
        self.patchNotes = "\n".join(patchNotes)
        self.patch_notes = patchNotes
        self.old_version = old
        self.new_version = new
        try:
            self.date_released = datetime.datetime.fromtimestamp( ## ensure that you can convert to a date time
                date_released, tz=datetime.timezone.utc
            )
        except TypeError:
            raise TypeError("Could not convert date_released to a datetime object")

    def to_dict(self) -> dict:
        return {
            "patch_notes": self.patchNotes.split("\n"),
            "old": self.old_version,
            "new": self.new_version,
            "date_released": self.date_released.timestamp(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChangeLogEntry":
        return cls(
            patchNotes=data["patch_notes"],
            old=data["old"],
            new=data["new"],
            date_released=data["date_released"],
        )


class ChangeLogManager:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self._lock = asyncio.Lock()
        if not os.path.exists(file_name): # ensure filepath exists
            raise FileNotFoundError(f"{file_name} does not exist")
        self._changelogs: t.List[ChangeLogEntry] = []

    async def _open_file(
        self,
        func: t.Callable[[io.TextIOWrapper, t.Any], t.Any] = lambda f: None,
        mode="r",
        args: list = None,
        kwargs: dict = None,
    ) -> t.Any:
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        async with self._lock:
            with open(self.file_name, mode) as file:
                return func(file, *args, *kwargs)  # type: ignore

    async def load_files(self):


        self._changelogs = await self._open_file(func=create_log_entry_from_file, mode="r") #type: ignore
        return self._changelogs

    async def save_files(self, new: dict):
        def func(file: io.TextIOWrapper, data: dict):
            json.dump(data, file)

        return await self._open_file(func=func, mode="w", args=[new])

    async def add_changelog(self, item: ChangeLogEntry):
        data = await self.load_files()
        data.append(item.to_dict())

        def func(file, _data):
            json.dump(_data, file)

        await self._open_file(func=func, mode="w", args=[data])

    @staticmethod
    async def create_changelog(data: dict):
        # TODO: finish
        try:
            return ChangeLogEntry(**data)
        except BaseException as exc:
            raise RuntimeError("Could not convert it to a dictionary") from exc
