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
With the assistance of Google Gemini
"""
import typing
from typing import List, Tuple
import os
import warnings
import orjson
import asyncpg

# Assuming structural imports relative to your environment
from . import user_data, UnknownPrivilegeError
from .appeal import Appeal, AppealViewInfo
from .fixed_answer_problem import FixedAnswerProblem
from .dict_convertible import DictConvertible, IdentifiableDictConvertible
from .errors import (
    FormatException,
    SQLNotSupportedInRedisException,
    ThingNotFound,
    ProblemNotFound,
    QuizNotFound,
    AppealViewInfoNotFound,
    CorruptedDataException
)
from .GuildData import GuildData
from .quizzes import Quiz
from .user_data import UserData
from .verification_code_info import VerificationCodeInfo
from .cache_ABC import AbstractCache, PREFIX_REGISTRY

GuildID = typing.Optional[int]
T = typing.TypeVar('T', bound=IdentifiableDictConvertible)


class PostgresCache(AbstractCache):
    def __init__(self, dsn: str, table_name: str = "cache_table", *args, **kwargs) -> None:
        """
        :param dsn: PostgreSQL connection string (e.g., 'postgresql://user:password@localhost:5432/dbname')
        """
        super().__init__(*args, **kwargs)
        self.dsn = dsn
        self.table_name = table_name
        self._pool: typing.Optional[asyncpg.Pool] = None
        self._locked = False

    async def initialize(self) -> None:
        """Establishes the connection pool, creates the table, and optimizes with a GIN index."""
        self._pool = await asyncpg.create_pool(self.dsn)

        async with self._pool.acquire() as conn:
            # Create the master key-value document table
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    key TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    data JSONB NOT NULL
                );
            """)
            # GIN (Generalized Inverted Index) allows lightning-fast sub-document matching inside JSONB
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_data_gin 
                ON {self.table_name} USING gin (data);
            """)
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_type 
                ON {self.table_name} (type);
            """)

    async def close(self) -> None:
        """Safely close the connection pool."""
        if self._pool:
            await self._pool.close()

    def _deserialize(self, record: asyncpg.Record, cls: typing.Type[T]) -> T:
        """Enforces protocol invariants to safely decode native JSONB fields."""
        try:
            # asyncpg automatically parses JSONB columns into Python dicts/lists out of the box!
            data_dict = record["data"]
            if isinstance(data_dict, str):
                data_dict = orjson.loads(data_dict)
            return cls.from_dict(data_dict)
        except Exception as e:
            raise CorruptedDataException(f"Failed to parse database record into {cls.__name__}: {e}")

    # ==========================================
    # CORE ROUTINES
    # ==========================================

    async def clear(self, force=False):
        async with self._pool.acquire() as conn:
            await conn.execute(f"TRUNCATE TABLE {self.table_name};")

    async def add_thing(self, thing: IdentifiableDictConvertible) -> None:
        thing_id = thing.key
        thing_type = type(thing).__name__
        # Encode dict into a raw JSON string for the entry parameter mapping
        json_data = orjson.dumps(thing.to_dict()).decode('utf-8')

        async with self._pool.acquire() as conn:
            await conn.execute(f"""
                INSERT INTO {self.table_name} (key, type, data)
                VALUES ($1, $2, $3::jsonb)
                ON CONFLICT (key) DO UPDATE 
                SET type = EXCLUDED.type, data = EXCLUDED.data;
            """, thing_id, thing_type, json_data)

    async def add_things(self, things: list[IdentifiableDictConvertible]) -> None:
        """Optimized high-speed bulk upsert using executemany."""
        if not things:
            return

        payload = [
            (t.key, type(t).__name__, orjson.dumps(t.to_dict()).decode('utf-8'))
            for t in things
        ]
        async with self._pool.acquire() as conn:
            await conn.executemany(f"""
                INSERT INTO {self.table_name} (key, type, data)
                VALUES ($1, $2, $3::jsonb)
                ON CONFLICT (key) DO UPDATE 
                SET type = EXCLUDED.type, data = EXCLUDED.data;
            """, payload)

    async def remove_thing(self, thing_id: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(f"DELETE FROM {self.table_name} WHERE key = $1;", thing_id)

    def get_thing(
            self,
            thing_id: str,
            cls: typing.Type[T],
            default: T | None = None,
    ) -> T:
        raise NotImplementedError("Use async variants or fetch data using driver task integrations.")

    async def get_thing_async(self, thing_id: str, cls: typing.Type[T], default: T | None = None) -> T:
        async with self._pool.acquire() as conn:
            record = await conn.fetchrow(f"SELECT * FROM {self.table_name} WHERE key = $1;", thing_id)
            if not record:
                if default is not None:
                    return default
                raise ThingNotFound(f"Key {thing_id} not discovered.")
            return self._deserialize(record, cls)

    @property
    def is_locked(self) -> bool:
        return self._locked

    # ==========================================
    # CORE ABSTRACT CONCRETE ENTITY RESOLUTIONS
    # ==========================================

    async def get_problem(self, guild_id: GuildID, problem_id: int) -> FixedAnswerProblem:
        key = FixedAnswerProblem.key_of(guild_id=guild_id, id=problem_id)
        return await self.get_thing_async(key, FixedAnswerProblem)

    async def get_all_problems(self) -> List[FixedAnswerProblem]:
        async with self._pool.acquire() as conn:
            records = await conn.fetch(f"SELECT * FROM {self.table_name} WHERE type = 'FixedAnswerProblem';")
            return [self._deserialize(r, FixedAnswerProblem) for r in records]

    async def get_all_things(self) -> list[object]:
        all_elements = []
        async with self._pool.acquire() as conn:
            records = await conn.fetch(f"SELECT * FROM {self.table_name};")
            for r in records:
                cls = PREFIX_REGISTRY.get(r["type"])
                if cls:
                    all_elements.append(self._deserialize(r, cls))
        return all_elements

    async def get_all_problems_by_guild(self, guild_id: GuildID) -> List[FixedAnswerProblem]:
        # Using PostgreSQL native JSONB containment operator (@>) to query values instantly via the GIN index
        guild_filter = orjson.dumps({"guild_id": guild_id}).decode('utf-8')
        async with self._pool.acquire() as conn:
            records = await conn.fetch(f"""
                SELECT * FROM {self.table_name} 
                WHERE type = 'FixedAnswerProblem' AND data @> $1::jsonb;
            """, guild_filter)
            return [self._deserialize(r, FixedAnswerProblem) for r in records]

    async def add_problem(self, problem_id, problem: FixedAnswerProblem):
        if problem_id != problem.id:
            raise TypeError("IDs do not match")
        await self.add_thing(problem)

    async def remove_problem(self, problem_id: int, guild_id: GuildID):
        key = FixedAnswerProblem.key_of(guild_id=guild_id, id=problem_id)
        await self.remove_thing(key)

    async def num_guild_problems(self, guild_id: GuildID) -> int:
        guild_filter = orjson.dumps({"guild_id": guild_id}).decode('utf-8')
        async with self._pool.acquire() as conn:
            count = await conn.fetchval(f"""
                SELECT COUNT(*) FROM {self.table_name} 
                WHERE type = 'FixedAnswerProblem' AND data @> $1::jsonb;
            """, guild_filter)
            return count

    # ==========================================
    # QUIZZES, USER RECORDS, AND SYSTEM DATA
    # ==========================================

    async def add_quiz(self, quiz_id: int, quiz: Quiz) -> Quiz:
        assert quiz_id == quiz.id
        await self.add_thing(quiz)
        return quiz

    async def get_quiz(self, quiz_id: int) -> Quiz:
        key = Quiz.key_of(id=quiz_id)
        return await self.get_thing_async(key, Quiz)

    async def remove_quiz(self, quiz_id: int) -> None:
        await self.remove_thing(Quiz.key_of(id=quiz_id))

    async def get_user_data(self, user_id: int, default: UserData | None = None) -> UserData | None:
        return await self.get_thing_async(UserData.key_of(user_id=user_id), UserData, default=default)

    async def add_user_data(self, user_data: UserData) -> None:
        await self.add_thing(user_data)

    async def remove_user_data(self, user_data: UserData) -> None:
        await self.remove_thing(UserData.key_of(user_id=user_data.id))

    # ==========================================
    # APPEALS & SECURITY MANAGEMENT
    # ==========================================

    async def get_appeal(self, special_id: int, default: Appeal | None = None) -> Appeal:
        return await self.get_thing_async(Appeal.key_of(special_id=special_id), Appeal, default=default)

    async def get_all_appeals(self) -> list[Appeal]:
        async with self._pool.acquire() as conn:
            records = await conn.fetch(f"SELECT * FROM {self.table_name} WHERE type = 'Appeal';")
            return [self._deserialize(r, Appeal) for r in records]

    async def has_appeal(self, user_id: int, appeal_num: int) -> bool:
        appeal_filter = orjson.dumps({"user_id": user_id, "appeal_num": appeal_num}).decode('utf-8')
        async with self._pool.acquire() as conn:
            exists = await conn.fetchval(f"""
                SELECT EXISTS(
                    SELECT 1 FROM {self.table_name} 
                    WHERE type = 'Appeal' AND data @> $1::jsonb
                );
            """, appeal_filter)
            return exists

    async def set_appeal(self, appeal: Appeal) -> None:
        await self.add_thing(appeal)

    async def remove_appeal(self, appeal: Appeal) -> None:
        await self.remove_thing(Appeal.key_of(special_id=appeal.special_id))

    async def add_guild_data(self, guild_data: GuildData) -> None:
        await self.add_thing(guild_data)

    async def remove_guild_data(self, guild_id: GuildID) -> None:
        await self.remove_thing(GuildData.key_of(guild_id=guild_id))

    async def get_guild_data(self, guild_id: GuildID, default: GuildData | None = None) -> GuildData:
        return await self.get_thing_async(GuildData.key_of(guild_id=guild_id), GuildData, default=default)

    # ==========================================
    # CLEANUP BY USER / GUILD ID
    # ==========================================

    async def get_all_by_user_id(self, user_id: int) -> list[dict]:
        # Evaluates containment vectors cleanly across discrete nested sub-properties
        u_filter = orjson.dumps({"user_id": user_id}).decode('utf-8')
        a_filter = orjson.dumps({"author": user_id}).decode('utf-8')

        async with self._pool.acquire() as conn:
            records = await conn.fetch(f"""
                SELECT data FROM {self.table_name} 
                WHERE data @> $1::jsonb 
                   OR data @> $2::jsonb 
                   OR (data->>'authors')::jsonb @> $3::jsonb;
            """, u_filter, a_filter, str(user_id))
            return [r["data"] for r in records]

    async def del_all_by_user_id(self, user_id: int) -> None:
        u_filter = orjson.dumps({"user_id": user_id}).decode('utf-8')
        a_filter = orjson.dumps({"author": user_id}).decode('utf-8')

        async with self._pool.acquire() as conn:
            await conn.execute(f"""
                DELETE FROM {self.table_name} 
                WHERE data @> $1::jsonb 
                   OR data @> $2::jsonb 
                   OR (data->>'authors')::jsonb @> $3::jsonb;
            """, u_filter, a_filter, str(user_id))

    async def delete_all_by_guild_id(self, guild_id: int) -> None:
        guild_filter = orjson.dumps({"guild_id": guild_id}).decode('utf-8')
        async with self._pool.acquire() as conn:
            await conn.execute(f"DELETE FROM {self.table_name} WHERE data @> $1::jsonb;", guild_filter)

    # ==========================================
    # APPEAL VIEWS & CODES
    # ==========================================

    async def set_appeal_view_info(self, view_info: AppealViewInfo):
        await self.add_thing(view_info)

    async def get_appeal_view_info(self, view_info: AppealViewInfo):
        return await self.get_thing_async(AppealViewInfo.key_of(message_id=view_info.message_id), AppealViewInfo)

    async def del_appeal_view_info(self, message_id: int):
        await self.remove_thing(AppealViewInfo.key_of(message_id=message_id))

    async def get_appeal_view_infos(self) -> list[AppealViewInfo]:
        async with self._pool.acquire() as conn:
            records = await conn.fetch(f"SELECT * FROM {self.table_name} WHERE type = 'AppealViewInfo';")
            return [self._deserialize(r, AppealViewInfo) for r in records]

    async def get_verification_code_info(self, user_id: int) -> VerificationCodeInfo:
        return await self.get_thing_async(VerificationCodeInfo.key_of(user_id=user_id), VerificationCodeInfo)

    async def del_verification_code_info(self, user_id: int):
        await self.remove_thing(VerificationCodeInfo.key_of(user_id=user_id))

    async def set_verification_code_info(self, code_info: VerificationCodeInfo):
        await self.add_thing(code_info)

    # ==========================================
    # ARBITRARY SQL CAPABILITY GATEWAY
    # ==========================================

    async def run_sql(self, sql: str, placeholders: typing.Optional[typing.List[typing.Any]] = None) -> dict:
        """
        Runs true native relational SQL queries against the active PostgreSQL deployment.
        """
        placeholders = placeholders or []
        async with self._pool.acquire() as conn:
            # Check if the instruction intends to retrieve relational rows or execute a side-effect command
            if sql.strip().upper().startswith("SELECT"):
                records = await conn.fetch(sql, *placeholders)
                # Convert the internal list of Records into standard dict mappings
                return {"results": [dict(r) for r in records]}
            else:
                status_message = await conn.execute(sql, *placeholders)
                return {"status": status_message}

    async def initialize_sql_table(self):
        """Fulfills abstract protocol sequence cleanly without double overhead execution."""
        pass

    async def bgsave(self, schedule: typing.Any, path: str = None, wait: bool = False, raise_on_error: bool = False,
                     replace: bool = False, **kwargs):
        if raise_on_error:
            raise NotImplementedError("bgsave context frames are structural to memory-mapped Redis backends.")
        warnings.warn("bgsave safely bypassed: PostgreSQL manages background write logs continuously.", RuntimeWarning)