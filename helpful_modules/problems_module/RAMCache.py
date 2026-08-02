"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - RedisCache

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

from . import ClearProhibitedError
from .AbstractKVCache import AbstractKVBasedCache
from .cache_ABC import AbstractCache
import typing
from typing import List
import warnings
import orjson

from ..FileDictionaryReader import AsyncFileDict
from .appeal import Appeal, AppealViewInfo
from .fixed_answer_problem import FixedAnswerProblem
from .dict_convertible import DictConvertible, IdentifiableDictConvertible
from .errors import CorruptedDataException, ThingNotFound, ClearProhibitedError
from .cache_ABC import TYPE_ERROR_NOT_FOUND


MUST_IMPLEMENT_ERROR = NotImplementedError("Subclasses must implement this")
GuildID = typing.Optional[int]
T = typing.TypeVar("T", bound=IdentifiableDictConvertible)


class RAMCache(AbstractKVBasedCache):
    def __init__(self, *args, **kwargs) -> None:
        self._async_file_dict = AsyncFileDict("config.json")
        self.things: dict[str, IdentifiableDictConvertible] = {}

    async def get_all_things(self) -> list[IdentifiableDictConvertible]:
        """Return a list of EVERYTHING in the database"""
        return self.things.values()

    async def add_thing(self, thing: IdentifiableDictConvertible) -> None:
        """
        Adds a dictionary convertible object to the cache. If it is already in the cache, it will replace whatever is in there.

        :param thing: The object to add to the cache.
        :type thing: DictConvertible
        :return: Nothing.
        """
        self.things[thing.key] = thing

    async def remove_thing(self, thing_id: str) -> None:
        """
        Removes a dictionary convertible object from the cache.

        :param thing_id: The object to remove from the cache.
        :type thing_id: str
        :return: Nothing.
        """
        if thing_id in self.things:
            del self.things[thing_id]

    async def get_thing(
        self,
        thing_id: str,
        cls: typing.Type[T],
        default: T | None = None,
    ) -> T:
        """:param thing_id: The ID of the object.
        :type thing_id: int
        :param cls: The type of the dictionary convertible object.
        :type cls: typing.Type[DictConvertible]
        :param default: The default value to return if the object is not found.
        :type default: DictConvertible or None
        :return: The retrieved object.
        :rtype: the same class
        :raises ThingNotFound: If the object is not found (and default is None).
        :raises CorruptedDataException: If the object is found in the database, but is of the wrong type
        """
        if thing_id not in self.things:
            if default is not None:
                return default
            # raise correct error
            raise TYPE_ERROR_NOT_FOUND.get(cls, ThingNotFound)(
                f"No object with {thing_id} was found in the database (expected class type: {cls.__name__})"
            )
        T = self.things[thing_id]
        if not isinstance(T, cls):
            raise CorruptedDataException(
                f"Corrupted data found in database. Expected an object of type {cls.__name__} but found an object of class {T.__class__.__name__}"
            )
        return T

    def is_locked(self) -> bool:
        """Return whether the cache is locked"""
        return False

    async def items(self) -> list[tuple[str, IdentifiableDictConvertible]]:
        """Return a list of EVERYTHING in the database (and their keys)"""
        return self.things.items()

    async def clear(self, force=False):
        """Clear the database."""
        if not force:
            raise ClearProhibitedError("You did not force clearing of this database")
        if self.is_production():
            raise ClearProhibitedError("Cannot clear database during production")
        self.things.clear()
