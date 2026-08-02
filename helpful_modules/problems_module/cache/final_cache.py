"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - MathProblemCache

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
"""

import asyncio
import contextlib
import logging
import sqlite3
import typing
from typing import Literal

import aiosqlite
import aiomysql
import disnake

from helpful_modules.dict_factory import dict_factory

from ..appeal import Appeal, AppealViewInfo
from ..cache_ABC import AbstractCache, T
from ..dict_convertible import IdentifiableDictConvertible
from ..errors import BGSaveNotSupportedOnSQLException, ThingNotFound
from ..fixed_answer_problem import FixedAnswerProblem
from ..GuildData import GuildData
from ..quizzes import Quiz
from ..user_data import UserData
from ..verification_code_info import VerificationCodeInfo
from .misc_related_cache import MiscRelatedCache

log = logging.getLogger(__name__)


class SQLCache(MiscRelatedCache):
    """Shared SQL cache behavior that is not tied to one SQL driver."""

    placeholder = "?"

    def __init__(
        self,
        *,
        use_sqlite: bool = True,
        max_answer_length: int = 100,
        max_question_limit: int = 250,
        max_guild_problems: int = 125,
        max_answers_per_problem: int = 25,
        max_problems_per_quiz: int = 50,
        max_quizzes_per_guild: int = 50,
        warnings_or_errors: Literal["warnings", "errors"] = "warnings",
        db_name: str = "problems_module.db",
        update_cache_by_default_when_requesting: bool = True,
        use_cached_problems: bool = False,
        initialize_tables: bool = True,
        **_: typing.Any,
    ):
        AbstractCache.__init__(self)
        log.info("Initializing SQLCache")
        if warnings_or_errors not in ("warnings", "errors"):
            raise ValueError(
                f"warnings_or_errors is {warnings_or_errors}, not 'warnings' or 'errors'"
            )
        if max_answers_per_problem < 1:
            raise ValueError("max_answers_per_problem must be at least 1!")

        self.cached_submissions_organized_by_dict = None
        self.db_name = db_name
        self.db = db_name
        self.warnings = warnings_or_errors == "warnings"
        self._max_answers_per_problem = max_answers_per_problem
        self.use_sqlite = use_sqlite
        self.use_cached_problems = use_cached_problems
        self._max_answer_length = max_answer_length
        self._max_question_length = max_question_limit
        self._max_guild_limit = max_guild_problems
        self.max_quizzes_per_guild = max_quizzes_per_guild
        self.max_problems_per_quiz = max_problems_per_quiz
        self.update_cache_by_default_when_requesting = (
            update_cache_by_default_when_requesting
        )
        self.guild_ids = set()
        self.cached_submissions = []
        self.cached_quizzes = []
        self.guild_problems = {}
        self.global_problems = {}
        self._guilds: list[disnake.Guild] = []
        self.cached_sessions = {}
        self._locked = False

        if initialize_tables:
            asyncio.run(self.initialize_sql_table())

    @contextlib.contextmanager
    def get_connection(self):
        connection = sqlite3.connect(self.db_name)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    get_a_connection = get_connection

    @property
    def is_locked(self) -> bool:
        return self._locked

    async def bgsave(
        self,
        schedule: typing.Any = True,
        path: str = None,
        wait: bool = False,
        raise_on_error: bool = False,
        replace: bool = False,
        **kwargs,
    ):
        raise BGSaveNotSupportedOnSQLException("Only Redis caches can do bgsave")

    async def run_sql(
        self, sql: str, placeholders: typing.Optional[list[typing.Any]] = None
    ) -> list[dict]:
        assert isinstance(sql, str)
        if placeholders is None:
            placeholders = []
        async with aiosqlite.connect(self.db_name) as conn:
            conn.row_factory = dict_factory
            cursor = await conn.cursor()
            await cursor.execute(sql, placeholders)
            rows = await cursor.fetchall()
            await conn.commit()
            return rows

    async def add_thing(self, thing: IdentifiableDictConvertible) -> None:
        if isinstance(thing, FixedAnswerProblem):
            await self.add_problem(thing.id, thing)
        elif isinstance(thing, Quiz):
            await self.add_quiz(thing.id, thing)
        elif isinstance(thing, UserData):
            await self.add_user_data(thing)
        elif isinstance(thing, GuildData):
            await self.add_guild_data(thing)
        elif isinstance(thing, Appeal):
            await self.add_appeal(thing)
        elif isinstance(thing, AppealViewInfo):
            await self.set_appeal_view_info(thing)
        elif isinstance(thing, VerificationCodeInfo):
            await self.set_verification_code_info(thing)
        else:
            raise TypeError(f"Unsupported SQL cache object: {thing.__class__.__name__}")

    async def remove_thing(self, thing_id: str) -> None:
        prefix, _, raw_id = thing_id.partition(":")
        if prefix == "UserData":
            await self.del_user_data(int(raw_id))
        elif prefix == "GuildData":
            await self.remove_guild_data(int(raw_id))
        elif prefix == "AppealViewInfo":
            await self.del_appeal_view_info(int(raw_id))
        elif prefix == "VerificationCodeInfo":
            await self.del_verification_code_info(int(raw_id))
        else:
            raise ThingNotFound(f"Cannot remove unsupported SQL cache key {thing_id}")

    async def clear(self, force=False):
        tables = (
            "problems",
            "quizzes",
            "quiz_submissions",
            "quiz_submission_sessions",
            "quiz_description",
            "user_data",
            "guild_data",
            "appeals",
            "appeal_view_info",
            "verification_code_infos",
        )
        for table in tables:
            await self.run_sql(f"DELETE FROM {table}")

    def get_thing(
        self,
        thing_id: str,
        cls: typing.Type[T],
        default: T | None = None,
    ) -> IdentifiableDictConvertible | None:
        raise NotImplementedError("SQLCache lookups are async; use typed async methods.")

    async def get_all_things(self) -> list[object]:
        things: list[object] = []
        things.extend(await self.get_all_problems())
        try:
            things.extend(await self.get_all_appeals())
        except ThingNotFound:
            pass
        return things

    async def remove_user_data(self, user_data: UserData) -> None:
        await self.del_user_data(user_data.user_id)

    async def remove_guild_data(self, guild_id: int | None) -> None:
        await self.run_sql("DELETE FROM guild_data WHERE guild_id IS ?", [guild_id])

    async def del_all_by_user_id(self, user_id: int) -> None:
        await self.delete_all_by_user_id(user_id)

    async def remove_quiz(self, quiz_id: int) -> None:
        await self.run_sql("DELETE FROM quizzes WHERE quiz_id = ?", [quiz_id])
        await self.run_sql("DELETE FROM quiz_submissions WHERE quiz_id = ?", [quiz_id])
        await self.run_sql(
            "DELETE FROM quiz_submission_sessions WHERE quiz_id = ?", [quiz_id]
        )
        await self.run_sql("DELETE FROM quiz_description WHERE quiz_id = ?", [quiz_id])

    async def del_verification_code_info(self, user_id: int):
        await self.delete_verification_code_info(user_id)

    async def get_appeal_view_infos(self):
        return self.get_all_appeal_view_infos()

    async def num_guild_problems(self, guild_id: int | None) -> int:
        rows = await self.run_sql(
            "SELECT COUNT(*) AS count FROM problems WHERE guild_id IS ?",
            [guild_id],
        )
        return int(rows[0]["count"])


class MySQLCache(SQLCache):
    """MySQL-specific connection details for the SQL-backed math problem cache."""

    placeholder = "%s"

    def __init__(
        self,
        *,
        mysql_username: str,
        mysql_password: str,
        mysql_db_ip: str,
        mysql_db_name: str,
        use_sqlite: bool = False,
        **kwargs: typing.Any,
    ):
        self.mysql_username = mysql_username
        self.mysql_password = mysql_password
        self.mysql_db_ip = mysql_db_ip
        self.mysql_db_name = mysql_db_name
        super().__init__(use_sqlite=use_sqlite, **kwargs)

    @contextlib.asynccontextmanager
    async def get_a_connection(self):
        connection = await aiomysql.connect(
            host=self.mysql_db_ip,
            password=self.mysql_password,
            user=self.mysql_username,
            db=self.mysql_db_name,
        )
        try:
            yield connection
            await connection.commit()
        finally:
            connection.close()

    async def run_sql(
        self, sql: str, placeholders: typing.Optional[list[typing.Any]] = None
    ) -> list[dict]:
        assert isinstance(sql, str)
        if placeholders is None:
            placeholders = []
        async with self.get_a_connection() as connection:
            cursor = await connection.cursor(aiomysql.DictCursor)
            await cursor.execute(sql, placeholders)
            if cursor.description is None:
                return []
            return list(await cursor.fetchall())

    async def remove_guild_data(self, guild_id: int | None) -> None:
        await self.run_sql("DELETE FROM guild_data WHERE guild_id = %s", [guild_id])

    async def remove_quiz(self, quiz_id: int) -> None:
        await self.run_sql("DELETE FROM quizzes WHERE quiz_id = %s", [quiz_id])
        await self.run_sql(
            "DELETE FROM quiz_submissions WHERE quiz_id = %s", [quiz_id]
        )
        await self.run_sql(
            "DELETE FROM quiz_submission_sessions WHERE quiz_id = %s", [quiz_id]
        )
        await self.run_sql(
            "DELETE FROM quiz_description WHERE quiz_id = %s", [quiz_id]
        )

    async def num_guild_problems(self, guild_id: int | None) -> int:
        if guild_id is None:
            rows = await self.run_sql(
                "SELECT COUNT(*) AS count FROM problems WHERE guild_id IS NULL"
            )
        else:
            rows = await self.run_sql(
                "SELECT COUNT(*) AS count FROM problems WHERE guild_id = %s",
                [guild_id],
            )
        return int(rows[0]["count"])


class MathProblemCache(SQLCache):
    """Backwards-compatible public cache name."""

    pass
