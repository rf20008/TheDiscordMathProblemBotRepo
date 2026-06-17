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
from abc import ABC
import typing
import orjson
import asyncio
from helpful_modules.FileDictionaryReader import AsyncFileDict
from helpful_modules.problems_module.dict_convertible import DictConvertible, IdentifiableDictConvertible
from redis import asyncio as aioredis  # type: ignore
from helpful_modules.problems_module.errors import (
    SQLNotSupportedInRedisException,
    ThingNotFound,
    CorruptedDataException,
    OwnershipNotDeterminableException, ClearProhibitedError
)
from ..AbstractKVCache import AbstractKVBasedCache, PREFIX_REGISTRY
from ..cache_ABC import TYPE_ERROR_NOT_FOUND
MUST_IMPLEMENT_ERROR = NotImplementedError("Subclasses must implement this")
GuildID = typing.Optional[int]
T = typing.TypeVar('T', bound=IdentifiableDictConvertible)


def _parse_key(self, key: str) -> str:
    """
    Extracts and returns the namespace prefix string from a Redis key.

    Raises:
        ValueError: If the key is malformed.
    """
    if ":" not in key:
        raise ValueError(f"Malformed key missing namespace delimiter: '{key}'")

    return key.split(":", 1)[0]


def _parse_value(self, prefix: str, raw_val: str | bytes) -> IdentifiableDictConvertible:
    """
    Looks up the prefix in the registry, decodes the JSON, and returns
    the proper instantiated object instance.

    Raises:
        ValueError: If the prefix is unregistered.
        Exception: Any parsing or constructor validation error.
    """
    target_class = PREFIX_REGISTRY.get(prefix)
    if target_class is None:
        raise ValueError(f"Unregistered namespace prefix '{prefix}' encountered.")

    parsed_dict = orjson.loads(raw_val)
    return target_class.from_dict(parsed_dict)
class RedisCache2(AbstractKVBasedCache, ABC):
    def __init__(self, redis_url: str, password: str) -> None:
        self._async_file_dict = AsyncFileDict("config.json")
        self.redis_url = redis_url
        self.password = password
        self.redis = aioredis.from_url(
            redis_url, encoding="utf-8", decode_responses=True, password=password
        )
        self.lock = asyncio.Lock()


    async def get_all_things(self) -> list[IdentifiableDictConvertible]:
        """Return a list of EVERYTHING in the database"""
        return [value for key, value in await self.items()]

    async def items(self) -> list[tuple[str, IdentifiableDictConvertible]]:
        """
        Return a list of EVERYTHING in the database.

        Raises:
            ExceptionGroup: A combined group containing all ThingNotFound and
                            CorruptedDataException errors encountered during processing.
        """
        string_keys = []

        # 1. Scan for string keys safely to avoid freezing the event loop
        async for key in self.redis.scan_iter(match="*"):
            key_type = await self.redis.type(key)
            if key_type == "string":
                string_keys.append(key)

        if not string_keys:
            return []

        # 2. Bulk fetch all values at once
        raw_values = await self.redis.mget(string_keys)

        results = []
        errors: list[Exception] = []

        # 3. Process records leveraging the single-responsibility helpers
        for key, raw_val in zip(string_keys, raw_values):

            # Track keys that disappeared mid-process
            if raw_val is None:
                errors.append(
                    ThingNotFound(
                        f"Key '{key}' was detected during scan_iter() but vanished "
                        f"before it could be retrieved via mget()."
                    )
                )
                continue

            try:
                # Step A: Extract prefix string (e.g., "FixedAnswerProblem")
                prefix = self._parse_key(key)

                # Step B: Match class registry, unpack json, and build object factory style
                obj = self._parse_value(prefix, raw_val)

                results.append((key, obj))

            except Exception as e:
                # Any failure across string splitting, missing prefixes, malformed json,
                # or missing model dataclass arguments is safely trapped here.
                corrupted_error = CorruptedDataException(
                    f"Key '{key}' failed strict namespace parsing or structural verification."
                )
                corrupted_error.__cause__ = e
                errors.append(corrupted_error)

        # 4. Fail loudly if any issues were collected across the database loop
        if errors:
            raise ExceptionGroup(
                "Data integrity errors encountered during cache processing inside items().",
                errors
            )

        return results
    async def add_thing(self, thing: IdentifiableDictConvertible) -> None:
        """
        Adds a dictionary convertible object to the cache. If it is already in the cache, it will replace whatever is in there.

        :param thing: The object to add to the cache.
        :type thing: DictConvertible
        :return: Nothing.
        """
        await self.redis.set(thing.key, orjson.dumps(thing).decode('utf-8'))
    async def remove_thing(self, thing_id: str) -> None:
        """
        Removes a dictionary convertible object from the cache.

        :param thing_id: The object to remove from the cache.
        :type thing_id: str
        :return: Nothing.
        """
        await self.redis.delete(thing_id)

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
        thing_unparsed = await self.redis.get(thing_id)
        prefix = self._parse_key(thing_id)
        if thing_unparsed is None:
            if default is not None:
                return default
            # raise correct error
            raise TYPE_ERROR_NOT_FOUND.get(cls, ThingNotFound)(
                f"No object with {thing_id} was found in the database "
                f"(expected class type: {cls.__name__})"
            )
        try:
            to_ret = _parse_value(prefix, thing_unparsed)
            if not isinstance(to_ret, cls):
                raise CorruptedDataException(
                    f"Corrupted data found in database. "
                    f"Expected an object of type {cls.__name__} "
                    f"but found an object of class {to_ret.__class__.__name__}"
                )
            return to_ret
        except Exception as e:
            raise CorruptedDataException(
                f"Corrupted data found in database. "
                f"Could not parse {thing_unparsed} found at key {thing_id} "
                f"into an object of type {cls.__name__}"
            ) from e

    @property
    def is_locked(self) -> bool:
        """Return whether the cache is locked"""
        return self.lock.locked()
    async def del_all_by_user_id(self, user_id: int) -> None:
        all_items = await self.items()
        for key, value in all_items:
            try:
                belongs = value.belongs_to_user(user_id)
            except OwnershipNotDeterminableException:
                continue
            if belongs:
                await self.remove_thing(key)
    async def delete_all_by_guild_id(self, guild_id: int) -> None:
        all_items = await self.items()
        for key, value in all_items:
            try:
                belongs = value.belongs_to_guild(guild_id)
            except OwnershipNotDeterminableException:
                continue
            if belongs:
                await self.remove_thing(key)

    async def get_all_items_starting_with(
            self,
            thing_start: str
    ) -> list[tuple[str, IdentifiableDictConvertible]]:
        """
        Returns a list of keys and objects matching a specific namespace prefix pattern.

        Leverages Redis's scanning features natively rather than filtering
        the entire database in Python memory.

        Raises:
            ExceptionGroup: Combined group of target specific errors.
        """
        string_keys = []

        # 1. Use Redis's power to match only the target keys
        # e.g., if thing_start is "FixedAnswerProblem", match pattern becomes "FixedAnswerProblem*"
        async for key in self.redis.scan_iter(match=f"{thing_start}*"):
            key_type = await self.redis.type(key)
            if key_type == "string":
                string_keys.append(key)

        if not string_keys:
            return []

        # 2. Bulk fetch only the matched subset of values
        raw_values = await self.redis.mget(string_keys)

        results = []
        errors: list[Exception] = []

        # 3. Process the records safely using your helper pipeline
        for key, raw_val in zip(string_keys, raw_values):
            if raw_val is None:
                errors.append(
                    ThingNotFound(
                        f"Key '{key}' matched targeted scan pattern but vanished "
                        f"before it could be retrieved via mget()."
                    )
                )
                continue

            try:
                # Step A: Extract prefix string
                prefix = self._parse_key(key)

                # Step B: Parse JSON and evaluate strict type verification
                obj = self._parse_value(prefix, raw_val)

                results.append((key, obj))

            except CorruptedDataException as cde:
                # Trap the type-mismatch exception explicitly so its custom message remains intact
                errors.append(cde)

            except Exception as e:
                # Handle delimiter syntax issues or raw orjson decoding errors
                corrupted_error = CorruptedDataException(
                    f"Key '{key}' failed strict structural verification during prefix scan."
                )
                corrupted_error.__cause__ = e
                errors.append(corrupted_error)

        # 4. If any errors were hit inside this specific namespace batch, throw them together
        if errors:
            raise ExceptionGroup(
                f"Data integrity errors encountered while scanning for prefix '{thing_start}'.",
                errors
            )

        return results





    async def bgsave(
        self,
        schedule: typing.Any,
        path: str = None,
        wait: bool = False,
        raise_on_error: bool = False,
        replace: bool = False,
        **kwargs,
    ):
        """
        Perform a background save operation.

        This method is specific to Redis caches and is not supported for SQL caches.
        Attempting to call this method on a SQL cache will raise a BGSaveNotSupportedOnSQLException.

        Time complexity: O(1)

        Parameters:
        - schedule: An argument representing the schedule for the background save operation.
        - path (str): The path to save the data to.
        - wait (bool): Whether to wait for the operation to complete.
        - raise_on_error (bool): Whether to raise an error if the operation encounters an error.
        - replace (bool): Whether to replace existing data at the specified path.

        Raises:
        - BGSaveNotSupportedOnSQLException: If the cache is a SQL cache and does not support background save operations.
        """
        await self.redis.bgsave(
            schedule=schedule,
            path=path,
            wait=wait,
            raise_on_error=raise_on_error,
            replace=replace,
            **kwargs,
        )
    async def run_sql(
        self, sql: str, placeholders: typing.Optional[typing.List[typing.Any]] = None
    ) -> dict:
        """
        Run arbitrary SQL.

        Parameters:
        - sql (str): The SQL query to execute.
        - placeholders (Optional[List[Any]]): List of placeholders for SQL query parameters.

        Raises:
        - SQLNotSupportedInRedisException: Always raised since SQL operations are not supported in a Redis cache.
        """
        raise SQLNotSupportedInRedisException("SQL operations are not supported in redis")

    async def initialize_sql_table(self):
        raise SQLNotSupportedInRedisException(
            "SQL is not supported in Redis, and creating sql tables is not supported in Redis either"
        )
    async def clear(self, force=False):
        if self.is_production():
            raise ClearProhibitedError("Aborting! Cannot flush Redis in a production environment.")

        if not force:
            raise ValueError("You must pass force=True to confirm clearing the Redis database.")

            # flushdb() takes an asynchronous keyword argument in redis-py / aioredis
        await self._redis.flushdb(asynchronous=True)
if __name__ == "__main__":
    r = RedisCache2(redis_url="redis://localhost", password="<PASSWORD>")