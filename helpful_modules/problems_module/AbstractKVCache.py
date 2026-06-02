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
from abc import ABC, abstractmethod
import typing
from typing import List
import warnings
import orjson

from . import OwnershipNotDeterminableException
from ..FileDictionaryReader import AsyncFileDict
from .appeal import Appeal, AppealViewInfo
from .base_problem import BaseProblem
from .dict_convertible import DictConvertible, IdentifiableDictConvertible
from .errors import (
    FormatException,
    SQLNotSupportedInRedisException, ThingNotFound,
    CorruptedDataException
)
from .GuildData import GuildData
from .quizzes import Quiz
from .user_data import UserData
from .verification_code_info import VerificationCodeInfo
from .cache_ABC import AbstractCache, TYPE_ERROR_NOT_FOUND
from .parse_problem import convert_dict_to_problem
MUST_IMPLEMENT_ERROR = NotImplementedError("Subclasses must implement this")
GuildID = typing.Optional[int]
T = typing.TypeVar('T', bound=IdentifiableDictConvertible)

PREFIX_REGISTRY = {
    "Quiz": Quiz,
    "UserData": UserData,
    "GuildData": GuildData,
    "VerificationCodeInfo": VerificationCodeInfo,
    "Appeal": Appeal,
    "AppealViewInfo": AppealViewInfo,
    "BaseProblem": convert_dict_to_problem, # this is because there are different types of problems that have to be parsed appropriately
}

class AbstractKVBasedCache(AbstractCache, ABC):
    def __init__(self, *args, **kwargs) -> None:
        self._async_file_dict = AsyncFileDict("config.json")



    @abstractmethod
    async def get_all_things(self) -> list[IdentifiableDictConvertible]:
        """Return a list of EVERYTHING in the database"""
        pass
    @abstractmethod
    async def items(self) -> list[tuple[str, IdentifiableDictConvertible]]:
        """Return a list of EVERYTHING in the database (and their keys)"""
        pass
    @abstractmethod
    async def add_thing(self, thing: IdentifiableDictConvertible) -> None:
        """
        Adds a dictionary convertible object to the cache. If it is already in the cache, it will replace whatever is in there.

        :param thing: The object to add to the cache.
        :type thing: DictConvertible
        :return: Nothing.
        """
        pass

    @abstractmethod
    async def remove_thing(self, thing_id: str) -> None:
        """
        Removes a dictionary convertible object from the cache.

        :param thing_id: The object to remove from the cache.
        :type thing_id: str
        :return: Nothing.
        """
        pass

    @abstractmethod
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
        pass

    @property
    @abstractmethod
    def is_locked(self) -> bool:
        """Return whether the cache is locked"""
        pass
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
    async def get_all_items_starting_with(self, thing_start: str) -> list[tuple[str, IdentifiableDictConvertible]]:
        return list(filter(lambda tu: tu[0].startswith(thing_start), await self.items()))
    async def get_appeal_view_infos(self) -> list[AppealViewInfo]:
        """
        Retrieve all appeal view information stored in Redis.

        Yields:
        - AppealViewInfo: Each retrieved AppealViewInfo object.

        Raises:
        - AppealViewInfoNotFound: If no appeal view information is found in Redis.
        - BaseExceptionGroup: If there are formatting exceptions during result processing.
        """
        warnings.warn("This is a slow method. Please consider overriding it.", category=FutureWarning)
        return [obj[1] for obj in await self.get_all_items_starting_with("AppealViewInfo") if isinstance(obj[1], AppealViewInfo)] # type: ignore
    async def get_all_appeals(self) -> list[Appeal]:
        """Fetch all appeals from the database."""
        warnings.warn("This is a slow method. Please consider overriding it.", category=FutureWarning)
        return [obj[1] for obj in await self.get_all_items_starting_with("Appeal") if isinstance(obj[1], Appeal)] # type: ignore
    async def get_all_things_for_func(self, func: typing.Callable[[IdentifiableDictConvertible], bool]) -> List[IdentifiableDictConvertible]:
        return list(filter(func, await self.get_all_things()))
    async def get_all_problems(self) -> List[BaseProblem]:
        """Return a list of all problems!
        Time complexity: O(N)"""
        warnings.warn(
            "There is a faster method to doing this, without a FULL scan of the database. Please override this method.",
            category=RuntimeWarning)
        return [convert_dict_to_problem(obj) for obj in await self.get_all_items_starting_with("BaseProblem")] # type: ignore



    async def get_problem(self, guild_id: GuildID, problem_id: int) -> BaseProblem:
        """Attempt to return the problem with guild_id and problem_id =problem_id
        Time complexity: O(1)"""
        prob = await self.get_thing(BaseProblem.key_of(guild_id=guild_id, id=problem_id), cls=BaseProblem)
        return prob



    async def get_all_problems_by_guild(self, guild_id: GuildID) -> List[BaseProblem]:
        """return a list of all problems with the guild id = id
                Time complexity: O(N)"""
        warnings.warn("This method is slow. Consider overriding it to do a more efficient DB scan", category=RuntimeWarning)
        return await self.get_all_problems_by_func(lambda p: p.guild_id == guild_id)

    async def get_global_problems(self) -> List[BaseProblem]:
        """
        Return a list of all global problems.

        :return: A list of global problems.
        """
        return await self.get_all_problems_by_guild(None)
    async def get_all_problems_by_func(self, func: typing.Callable[[BaseProblem], bool]) -> List[BaseProblem]:
        return list(filter(func, await self.get_all_problems()))
    async def add_problem(self, problem_id, problem: BaseProblem):
        """
        Add a problem to the cache.

        :param problem_id: The ID of the problem.
        :param problem: The BaseProblem instance.
        :raises TypeError: If 'problem_id' is not an int or 'problem' is not a BaseProblem.
        :raises ValueError: If IDs do not match.
        """
        if not problem_id == problem.id:
            raise TypeError("IDs do not match")
        await self.add_thing(problem)
    async def remove_problem(self, problem_id: int, guild_id: GuildID):
        """
        Remove a problem from the cache.

        :param problem_id: The ID of the problem.
        :param guild_id: The ID of the guild.
        :raises TypeError: If 'problem_id' is not an int or 'guild_id' is not an int.
        """
        await self.remove_thing(BaseProblem.key_of(guild_id=guild_id, id=problem_id))


    async def add_quiz(self, quiz_id: int, quiz: Quiz):
        """Add a quiz to the cache"""
        assert quiz_id == quiz.id
        await self.add_thing(quiz)
    async def get_quiz(self, quiz_id: int) -> Quiz:
        """
        Get quiz data by quiz ID.

        :param quiz_id: The ID of the quiz.
        :return: The data associated with the quiz.
        :raises ProblemNotFoundException: If the quiz is not found.
        """
        return await self.get_thing(Quiz.key_of(id=quiz_id), cls=Quiz)
    async def remove_quiz(self, quiz_id: int) -> None:
        """
        Remove a quiz from the cache.

        :param quiz_id: The ID of the quiz.
        """
        return await self.remove_thing(Quiz.key_of(id=quiz_id))
    async def get_user_data(self, user_id: int, default: UserData | None = None) -> UserData | None:
        return await self.get_thing(UserData.key_of(user_id=user_id), cls=UserData, default=default)
    async def add_user_data(self, user_data: UserData) -> None:
        """Add the data of a user to the cache"""
        return await self.add_thing(user_data)
    async def get_permissions_required_for_command(self, command_name: str | None) -> dict[str, bool]:
        """
        Get the permissions required for a command.

        :param command_name: The name of the command.
        :return: A dictionary of permissions required for the command.
        """
        if not hasattr(self, "_async_file_dict"):
            raise NotImplementedError("Subclasses must implement this method.")
        await self._async_file_dict.read_from_file()
        return self._async_file_dict.dict["permissions_required"][command_name]


    async def get_appeal(self, special_id: int, default: Appeal | None = None) -> Appeal:
        """Fetch an appeal from the database, with special id specified. If not found, return default (if not None)
        If no appeal is found, and default is None, raise ThingNotFound."""
        return await self.get_thing(Appeal.key_of(special_id=special_id), cls=Appeal, default=default)

    async def add_appeal(self, appeal: Appeal) -> None:
        """Add an appeal to the database."""
        await self.add_thing(appeal)
    async def set_appeal(self, appeal: Appeal) -> None:
        """Change an appeal in the database."""
        return await self.add_appeal(appeal)
    async def remove_appeal(self, appeal: Appeal) -> None:
        """Remove an appeal from the database."""
        return await self.remove_thing(Appeal.key_of(special_id=appeal.special_id))
    async def update_cache(self):
        raise NotImplementedError("This method is being removed due to its expensiveness!!!")
    async def add_guild_data(self, guild_data: GuildData) -> None:
        """Add the data of a guild to the cache."""
        return await self.add_thing(guild_data)
    async def remove_guild_data(self, guild_id: GuildID) -> None:
        """Remove the data of a guild from the cache."""
        return await self.remove_thing(GuildData.key_of(guild_id=guild_id))
    async def del_guild_data(self, guild_id: GuildID) -> None:
        return await self.remove_guild_data(guild_id)
    async def get_guild_data(self, guild_id: GuildID) -> GuildData:
        """Get the data of a guild from the cache."""
        return await self.get_thing(GuildData.key_of(guild_id=guild_id), cls=GuildData)
    async def get_all_by_user_id(self, user_id: int) -> list[dict]:
        things = await self.get_all_things()
        things_authored = []
        for thing in things:
            try:
                if thing.belongs_to_user(user_id):
                    things_authored.append(thing)
            except OwnershipNotDeterminableException:
                pass
        return things_authored

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
        raise MUST_IMPLEMENT_ERROR
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
        raise MUST_IMPLEMENT_ERROR
    async def set_appeal_view_info(self, view_info: AppealViewInfo):
        """
        Store appeal view information in Redis.

        Parameters:
        - view_info (AppealViewInfo): The AppealViewInfo object to store.
        """
        await self.add_thing(view_info)
    async def get_appeal_view_info(self, view_info: AppealViewInfo):
        """
        Retrieve appeal view information from Redis.

        Parameters:
        - message_id (int): The message ID associated with the appeal view information to retrieve.

        Returns:
        - AppealViewInfo: The retrieved AppealViewInfo object.

        Raises:
        - AppealViewInfoNotFound: If no appeal view information is found for the given message_id.
        - FormatException: If the stored data cannot be decoded into an AppealViewInfo object.
        """
        return await self.get_thing(AppealViewInfo.key_of(message_id=view_info.message_id), cls=AppealViewInfo)
    async def del_appeal_view_info(self, message_id: int):
        """Delete an appeal view information from the DB."""
        return await self.del_thing(AppealViewInfo.key_of(message_id=message_id))

    async def get_verification_code_info(self, user_id: int) -> VerificationCodeInfo:
        return await self.get_thing(VerificationCodeInfo.key_of(user_id=user_id), cls=VerificationCodeInfo)
    async def del_verification_code_info(self, user_id: int):
        await self.del_thing(VerificationCodeInfo.key_of(user_id=user_id))
    async def delete_verification_code_info(self, user_id: int):
        return await self.del_verification_code_info(user_id)
    async def set_verification_code_info(self, code_info: VerificationCodeInfo):
        return await self.add_thing(code_info)
    async def initialize_sql_table(self):
        raise SQLNotSupportedInRedisException(
            "SQL is not supported in Redis, and creating sql tables is not supported in Redis either"
        )

