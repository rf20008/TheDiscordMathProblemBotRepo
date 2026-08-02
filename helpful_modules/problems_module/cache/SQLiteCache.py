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

import asyncio
import logging
import pickle
import sqlite3
import typing
import warnings
from copy import copy, deepcopy
from types import FunctionType
from typing import *

import aiosqlite
import disnake

from helpful_modules.dict_factory import dict_factory

from ..fixed_answer_problem import FixedAnswerProblem
from ..cache_ABC import AbstractCache
from ..errors import *
from ..mysql_connector_with_stmt import mysql_connection
from ..parse_problem import convert_dict_to_problem, convert_row_to_problem
from ..quizzes import QuizProblem
log = logging.getLogger(__name__)

class SQLiteCache(AbstractCache):
    def __init__(
        self,
        *,
        max_answer_length: int = 100,
        max_question_limit: int = 250,
        max_guild_problems: int = 125,
        max_answers_per_problem: int = 25,
        max_problems_per_quiz: int = 50,
        max_quizzes_per_guild: int = 50,
        warnings_or_errors: Union[Literal["warnings"], Literal["errors"]] = "warnings",
        db_name: str = "problems_module.db",
        update_cache_by_default_when_requesting: bool = True,
        use_cached_problems: bool = False,
    ):
        """Create a new MathProblemCache. The arguments should be self-explanatory.
        Many methods are async!"""
        self.cached_submissions_organized_by_dict = None
        log.info("Initializing the MathProblemCache object.")
        # make_sql_table([], db_name = sql_dict_db_name)
        # make_sql_table([], db_name = "MathProblemCache1.db", table_name="kv_store")
        if use_sqlite:
            warnings.warn(
                "Sqlite has been deprecated. Use MySQL instead.", stacklevel=2
            )
        self.db_name = db_name
        self.db = db_name
        if warnings_or_errors not in ["warnings", "errors"]:
            log.critical("Uh oh; warnings_or_errors is bad")
            raise ValueError(
                f"warnings_or_errors is {warnings_or_errors}, not 'warnings' or 'errors'"
            )
        self.warnings = (
            warnings_or_errors == "warnings"
        )  # Whether to raise TypeErrors or warn
        if max_answers_per_problem < 1:
            raise ValueError("max_answers_per_problem must be at least 1!")
        self._max_answers_per_problem = max_answers_per_problem
        self.use_sqlite = use_sqlite
        self.use_cached_problems = use_cached_problems
        self._max_answer_length = max_answer_length
        self._max_question_length = max_question_limit
        self._max_guild_limit = max_guild_problems
        self.mysql_username = mysql_username
        self.max_quizzes_per_guild = max_quizzes_per_guild
        self.max_problems_per_quiz = max_problems_per_quiz
        self.mysql_password = mysql_password
        self.mysql_db_ip = mysql_db_ip
        self.mysql_db_name = mysql_db_name
        asyncio.run(
            self.initialize_sql_table()
        )  # Initialize the SQL tables (but asyncio.run() has to be used because __init__ cannot be async)
        self.update_cache_by_default_when_requesting = (
            update_cache_by_default_when_requesting
        )
        self.guild_ids = set()
        self.cached_submissions = []
        self.cached_quizzes = []
        self.guild_problems = dict()
        self._guilds: typing.List[disnake.Guild] = []
        # asyncio.run(self.update_cache())
        self.cached_sessions = {}
    async def bgsave(
        self,
        schedule: bool = True,
        path: str = None,
        wait: bool = False,
        raise_on_error: bool = False,
        replace: bool = False,
    ):
        """
        Perform a background save operation.

        This method is specific to Redis caches and is not supported for SQL caches.
        Attempting to call this method on a SQL cache will raise a BGSaveNotSupportedOnSQLException.

        Parameters:
        - schedule: An argument representing the schedule for the background save operation.
        - path (str): The path to save the data to.
        - wait (bool): Whether to wait for the operation to complete.
        - raise_on_error (bool): Whether to raise an error if the operation encounters an error.
        - replace (bool): Whether to replace existing data at the specified path.

        Raises:
        - BGSaveNotSupportedOnSQLException: If the cache is a SQL cache and does not support background save operations.
        """
        raise BGSaveNotSupportedOnSQLException("Only Redis caches can do bgsave")


    async def get_problem(
            self, guild_id: typing.Optional[int], problem_id: int
    ) -> FixedAnswerProblem:
        """Gets the problem with this guild id and problem id. If the problem is not found, a ProblemNotFound exception will be raised."""
        # This isn't working
        # Possible causes:
        # The item is of the wrong type
        # Wrong database/table / a SQL feature that I didn't know about
        # Searching by NULL
        log.debug(
            f"Type of guild_id & problem_id: guild_id: {type(guild_id)} {guild_id}, problem_id: {type(problem_id)} {problem_id}"
        )
        assert isinstance(guild_id, int) or guild_id is None
        # The problem: where doesn't work with an 'and' clause
        if not isinstance(problem_id, int):
            if self.warnings:
                warnings.warn("problem_id is not a integer", category=RuntimeWarning)
            else:
                raise TypeError("problem_id is not a integer")

            # Otherwise, use SQL to get the problem!
        async with aiosqlite.connect(self.db_name) as conn:
            cursor = await conn.cursor()
            log.debug(
                f"Getting the problem with guild id {guild_id} and problem_id {problem_id} (types: {type(guild_id)}, {type(problem_id)})"
            )
            r = await cursor.execute(
                """SELECT * FROM problems WHERE problem_id = ?""",
                # Not sure if making "from" uppercase will change anything (but it selects the problem from the database)
                (problem_id,),
            )
            rows = list(await cursor.fetchall())
            log.debug(f"{str(r)} {len(rows)} problems found")
            if len(rows) == 0:
                raise ProblemNotFound("Problem not found!")
            elif len(rows) > 1:
                log.critical("Uh oh; too many problems!")
                raise TooManyProblems(
                    f"{len(rows)} problems exist with the same guild_id and problem_id, not 1"
                )
            await conn.commit()
            if isinstance(rows[0], sqlite3.Row):
                row = dict_factory(cursor, rows[0])  #
            else:
                row = rows[0]
            return convert_dict_to_problem(row, cache=copy(self))
