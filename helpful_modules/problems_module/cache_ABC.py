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
import os

from .errors import UnknownPrivilegeError
from .user_data import UserData
from ..FileDictionaryReader import AsyncFileDict
from .appeal import Appeal, AppealViewInfo
from .fixed_answer_problem import FixedAnswerProblem
from .dict_convertible import DictConvertible, IdentifiableDictConvertible
from .errors import (
    SQLNotSupportedInRedisException,
    ThingNotFound,
    ProblemNotFound,
    QuizNotFound,
    AppealViewInfoNotFound,
)
from .GuildData import GuildData
from .quizzes import Quiz
from .user_data import UserData
from .verification_code_info import VerificationCodeInfo

MUST_IMPLEMENT_ERROR = NotImplementedError("Subclasses must implement this")
GuildID = typing.Optional[int]
T = typing.TypeVar("T", bound=IdentifiableDictConvertible)
TYPE_ERROR_NOT_FOUND = {
    FixedAnswerProblem: ProblemNotFound,
    GuildData: ThingNotFound,
    Quiz: QuizNotFound,
    VerificationCodeInfo: ThingNotFound,
    UserData: ThingNotFound,
    Appeal: ThingNotFound,
    AppealViewInfo: AppealViewInfoNotFound,
}


class AbstractCache(ABC):
    def __init__(self, *args, **kwargs) -> None:
        self._async_file_dict = AsyncFileDict("config.json")

    async def has_thing(self, thing_key: str) -> bool:
        warnings.warn("This is a slow method. Please override it to be faster")
        try:
            await self.get_thing(thing_key, default=None)
            return True
        except ThingNotFound:
            return False

    @abstractmethod
    async def add_thing(self, thing: IdentifiableDictConvertible) -> None:
        """
        Adds a dictionary convertible object to the cache.

        :param thing: The object to add to the cache.
        :type thing: DictConvertible
        :param thing_id: The ID of the object. (If none, will attempt to guess it from thing.id)
        :type thing: str | None
        :return: Nothing.
        """
        pass

    async def add_things(self, things: list[IdentifiableDictConvertible]) -> object:
        """
        Adds a list of dictionary convertible objects to the cache using a batch set operation.

        :param things: The list of objects to add to the cache.
        :type things: List[DictConvertible]
        :return: Nothing.
        """
        warnings.warn(
            "This method is slow. Please override it to use a batch query to make it faster",
            category=RuntimeWarning,
        )
        for thing in things:
            await self.add_thing(thing)

    @abstractmethod
    async def remove_thing(self, thing_id: str) -> None:
        """
        Removes a dictionary convertible object from the cache.

        :param thing: The object to remove from the cache.
        :type thing: DictConvertible
        :return: Nothing.
        """
        pass

    @abstractmethod
    def get_thing(
        self,
        thing_id: str,
        cls: typing.Type[T],
        default: T | None = None,
    ) -> IdentifiableDictConvertible | None:
        """:param thing_guild_id: The guild ID associated with the object.
        :type thing_guild_id: int
        :param thing_id: The ID of the object.
        :type thing_id: int
        :param cls: The type of the dictionary convertible object.
        :type cls: typing.Type[DictConvertible]
        :param default: The default value to return if the object is not found.
        :type default: DictConvertible or None
        :return: The retrieved object.
        :rtype: DictConvertible
        :raises ThingNotFound: If the object is not found.
        """
        pass

    @property
    @abstractmethod
    def is_locked(self) -> bool:
        """Return whether the cache is locked"""
        pass

    @abstractmethod
    async def get_problem(
        self, guild_id: GuildID, problem_id: int
    ) -> FixedAnswerProblem:
        """Attempt to return the problem with guild_id and problem_id =problem_id
        Time complexity: O(1)"""
        pass

    @abstractmethod
    async def get_all_problems(self) -> List[FixedAnswerProblem]:
        """Return a list of all problems!
        Time complexity: O(N)"""
        pass

    @abstractmethod
    async def get_all_things(self) -> list[object]:
        """Return a list of EVERYTHING in the database"""
        pass

    async def get_all_problems_by_guild(
        self, guild_id: GuildID
    ) -> List[FixedAnswerProblem]:
        """return a list of all problems with the guild id = id
        Time complexity: O(N)"""
        warnings.warn(
            "This method is slow. Consider overriding it to do a more efficient DB scan",
            category=RuntimeWarning,
        )
        return await self.get_all_problems_by_func(lambda p: p.guild_id == guild_id)

    async def get_global_problems(self) -> List[FixedAnswerProblem]:
        """
        Return a list of all global problems.

        :return: A list of global problems.
        """
        return await self.get_all_problems_by_guild(None)

    async def get_all_problems_by_func(
        self, func: typing.Callable[[FixedAnswerProblem], bool]
    ) -> List[FixedAnswerProblem]:
        return list(filter(func, await self.get_all_problems()))

    @abstractmethod
    async def add_problem(self, problem_id, problem: FixedAnswerProblem):
        """
        Add a problem to the cache.

        :param problem_id: The ID of the problem.
        :param problem: The FixedAnswerProblem instance.
        :raises TypeError: If 'problem_id' is not an int or 'problem' is not a FixedAnswerProblem.
        :raises ValueError: If IDs do not match.
        """
        pass

    async def update_problem(self, problem_id: int, problem: FixedAnswerProblem):
        """
        Update a problem in the cache.

        :param problem_id: The ID of the problem.
        :param problem: The FixedAnswerProblem instance.
        """
        return await self.add_problem(problem_id, problem)

    @abstractmethod
    async def remove_problem(self, problem_id: int, guild_id: GuildID):
        """
        Remove a problem from the cache.

        :param problem_id: The ID of the problem.
        :param guild_id: The ID of the guild.
        :raises TypeError: If 'problem_id' is not an int or 'guild_id' is not an int.
        """
        pass

    @abstractmethod
    async def add_quiz(self, quiz_id: int, quiz: Quiz) -> Quiz:
        """Add a quiz to the cache"""
        pass

    @abstractmethod
    async def get_quiz(self, quiz_id: int) -> Quiz:
        """
        Get quiz data by quiz ID.

        :param quiz_id: The ID of the quiz.
        :return: The data associated with the quiz.
        :raises ProblemNotFoundException: If the quiz is not found.
        """
        pass

    @abstractmethod
    async def remove_quiz(self, quiz_id: int) -> None:
        """
        Remove a quiz from the cache.

        :param quiz_id: The ID of the quiz.
        """
        pass

    @abstractmethod
    async def get_user_data(
        self, user_id: int, default: UserData | None = None
    ) -> UserData | None:
        """Add the data of a user to the cache"""
        pass

    @abstractmethod
    async def add_user_data(self, user_data: UserData) -> None:
        pass

    @abstractmethod
    async def remove_user_data(self, user_data: UserData) -> None:
        pass

    async def get_permissions_required_for_command(
        self, command_name: str | None
    ) -> dict[str, bool]:
        """
        Get the permissions required for a command.

        :param command_name: The name of the command.
        :return: A dictionary of permissions required for the command.
        """
        if not hasattr(self, "_async_file_dict"):
            raise NotImplementedError("Subclasses must implement this method.")
        await self._async_file_dict.read_from_file()
        return self._async_file_dict.dict["permissions_required"][command_name]

    async def user_meets_permissions_required_to_use_command(
        self,
        user_id: int,
        permissions_required: typing.Optional[typing.Dict[str, bool]] = None,
        command_name: str | None = None,
    ) -> bool:
        """
        Return whether the user meets permissions required to use the command.

        :param user_id: The ID of the user.
        :param permissions_required: Optional permissions required for the command.
        :param command_name: Optional name of the command.
        :return: True if the user meets permissions, False otherwise.
        """
        if permissions_required is None:
            permissions_required = await self.get_permissions_required_for_command(
                command_name
            )
        user_data: UserData = await self.get_user_data(
            user_id, default=UserData.default(user_id=user_id)
        )
        for perm_flag, required_state in permissions_required.items():
            # Convert the lowercase dict key (e.g., 'trusted') to uppercase ('TRUSTED')
            # to perfectly match your BotPermissionLevel attributes.
            user_has_flag = getattr(user_data.permissions, perm_flag.upper(), None)

            if user_has_flag is None:
                # Fallback check directly on the UserData instance attributes if not an Enum flag
                user_has_flag = getattr(user_data.permissions, perm_flag.lower(), None)
            if user_has_flag is None:
                user_has_flag = getattr(
                    user_data.permissions, perm_flag, None
                )  # final check: use the other one
            if isinstance(user_has_flag, bool):
                if user_has_flag != required_state:
                    return False
            else:
                raise UnknownPrivilegeError(f"Unknown privilege {perm_flag}")
        return True

    @abstractmethod
    async def get_appeal(
        self, special_id: int, default: Appeal | None = None
    ) -> Appeal:
        """Fetch an appeal from the database, with special id specified. If not found, return default (if not None)
        If no appeal is found, and default is None, raise ThingNotFound."""
        pass

    @abstractmethod
    async def get_all_appeals(self) -> list[Appeal]:
        """Fetch all appeals from the database."""
        pass

    async def add_appeal(self, appeal: Appeal) -> None:
        """Add an appeal to the database."""
        # step 1: does it exist? if not, we need to insert it, and reserve a new code
        if appeal.appeal_num >= 0 and await self.has_appeal(
            user_id=appeal.user_id, appeal_num=appeal.appeal_num
        ):
            # set it
            await self.set_appeal(appeal)  # it's already created
        else:
            # must create the appeal
            appeal.appeal_num = await self.reserve_next_appeal_num(appeal.user_id)
            await self.set_appeal(appeal)

    @abstractmethod
    async def has_appeal(self, user_id: int, appeal_num: int) -> bool:
        """Check if an appeal exists in the database."""
        pass

    @abstractmethod
    async def set_appeal(self, appeal: Appeal) -> None:
        """Change an appeal in the database. Please call add_appeal if you are creating a new appeal, because it will handle the appeal number"""
        pass

    @abstractmethod
    async def remove_appeal(self, appeal: Appeal) -> None:
        """Remove an appeal from the database."""
        pass

    async def get_next_appeal_num(self, user_id: int) -> int:
        """Get the next appeal number for a user."""
        data = await self.get_user_data(user_id)
        return data.appeal_num + 1

    async def reserve_next_appeal_num(self, user_id: int) -> int:
        """Reserve and return the next appeal number for a user."""
        data = await self.get_user_data(user_id)
        data.appeal_num += 1
        await self.add_user_data(data)
        return data.appeal_num

    async def update_cache(self):
        raise NotImplementedError(
            "This method is being removed due to its expensiveness!!!"
        )

    @abstractmethod
    async def add_guild_data(self, guild_data: GuildData) -> None:
        """Add the data of a guild to the cache."""
        pass

    @abstractmethod
    async def remove_guild_data(self, guild_id: GuildID) -> None:
        """Remove the data of a guild from the cache."""
        pass

    async def del_guild_data(self, guild_id: GuildID) -> None:
        return await self.remove_guild_data(guild_id)

    @abstractmethod
    async def get_guild_data(
        self, guild_id: GuildID, default: GuildData | None = None
    ) -> GuildData:
        """Get the data of a guild from the cache."""
        pass

    @abstractmethod
    async def get_all_by_user_id(self, user_id: int) -> list[dict]:
        """Get all data from a specific user in the cache.
        :param user_id: The ID of the user.
        :return: A list of dictionaries."""
        pass

    @abstractmethod
    async def del_all_by_user_id(self, user_id: int) -> None:
        pass

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

    @abstractmethod
    async def set_appeal_view_info(self, view_info: AppealViewInfo):
        """
        Store appeal view information in Redis.

        Parameters:
        - view_info (AppealViewInfo): The AppealViewInfo object to store.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def del_appeal_view_info(self, message_id: int):
        """Delete an appeal view information from the DB."""
        pass

    @abstractmethod
    async def get_appeal_view_infos(self):
        """
        Retrieve all appeal view information stored in Redis.

        Yields:
        - AppealViewInfo: Each retrieved AppealViewInfo object.

        Raises:
        - AppealViewInfoNotFound: If no appeal view information is found in Redis.
        - BaseExceptionGroup: If there are formatting exceptions during result processing.
        """
        pass

    @abstractmethod
    async def get_verification_code_info(self, user_id: int) -> VerificationCodeInfo:
        pass

    @abstractmethod
    async def del_verification_code_info(self, user_id: int):
        pass

    async def delete_verification_code_info(self, user_id: int):
        return await self.del_verification_code_info(user_id)

    @abstractmethod
    async def set_verification_code_info(self, code_info: VerificationCodeInfo):
        pass

    async def initialize_sql_table(self):
        raise SQLNotSupportedInRedisException(
            "SQL is not supported in Redis, and creating sql tables is not supported in Redis either"
        )

    @abstractmethod
    async def delete_all_by_guild_id(self, guild_id: int) -> None:
        pass

    @abstractmethod
    async def num_guild_problems(self, guild_id: GuildID) -> int:
        """
        Return number of problems in a guild.
        Must be O(log N) or better in backend implementation.
        """
        pass

    @staticmethod
    def is_production() -> bool:
        return "prod" in os.getenv("APP_ENV", "prod")

    @abstractmethod
    async def clear(self, force=False):
        """Clear the database."""
        pass
