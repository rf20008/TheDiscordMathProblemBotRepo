"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - SQLiteCache

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
Developed with the assistance of Google Gemini.
"""

import typing
from typing import List, Tuple
import warnings
import orjson
import aiosqlite


from .fixed_answer_problem import FixedAnswerProblem
from .dict_convertible import DictConvertible, IdentifiableDictConvertible
from .errors import ThingNotFound, CorruptedDataException

from .parse_problem import convert_dict_to_problem
from .AbstractKVCache import AbstractKVBasedCache, PREFIX_REGISTRY

GuildID = typing.Optional[int]
T = typing.TypeVar("T", bound=IdentifiableDictConvertible)


class SQLiteCache(AbstractKVBasedCache):
    def __init__(
        self,
        db_path: str = "bot_cache.db",
        table_name: str = "cache_table",
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.db_path = db_path
        self.table_name = table_name
        self._db: typing.Optional[aiosqlite.Connection] = None
        self._locked = False

    async def initialize(self) -> None:
        """Establishes connection to the file and sets up structural schemas."""
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row

        # Enable Write-Ahead Logging for high concurrency environments
        await self._db.execute("PRAGMA journal_mode=WAL;")

        await self._db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                key TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                data TEXT NOT NULL
            );
        """
        )
        # Indexes provide faster lookup vectors for type segregation and JSON fields
        await self._db.execute(
            f"CREATE INDEX IF NOT EXISTS idx_type ON {self.table_name}(type);"
        )
        await self._db.execute(
            f"CREATE INDEX IF NOT EXISTS idx_guild_id ON {self.table_name}(json_extract(data, '$.guild_id'));"
        )
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    def _deserialize(self, row: aiosqlite.Row, cls: typing.Type[T]) -> T:
        try:
            raw_data = row["data"]
            data_dict = orjson.loads(raw_data)

            # Map problems using specialized domain transformation function matching prefix mapping patterns
            if cls == FixedAnswerProblem:
                return convert_dict_to_problem(data_dict)  # type: ignore

            return cls.from_dict(data_dict)
        except Exception as e:
            raise CorruptedDataException(
                f"Failed to cleanly rebuild {cls.__name__} metadata schema parameters: {e}"
            )

    # ==========================================
    # ABS CONTRACT ROUTINES
    # ==========================================

    async def clear(self, force=False):
        await self._db.execute(f"DELETE FROM {self.table_name};")
        await self._db.commit()

    async def get_all_things(self) -> list[IdentifiableDictConvertible]:
        async with self._db.execute(f"SELECT * FROM {self.table_name};") as cursor:
            rows = await cursor.fetchall()
            results = []
            for r in rows:
                cls = PREFIX_REGISTRY.get(r["type"])
                if cls:
                    target_cls = (
                        FixedAnswerProblem if r["type"] == "FixedAnswerProblem" else cls
                    )
                    results.append(self._deserialize(r, target_cls))  # type: ignore
            return results

    async def items(self) -> list[tuple[str, IdentifiableDictConvertible]]:
        async with self._db.execute(f"SELECT * FROM {self.table_name};") as cursor:
            rows = await cursor.fetchall()
            results = []
            for r in rows:
                cls = PREFIX_REGISTRY.get(r["type"])
                if cls:
                    target_cls = (
                        FixedAnswerProblem if r["type"] == "FixedAnswerProblem" else cls
                    )
                    results.append((r["key"], self._deserialize(r, target_cls)))  # type: ignore
            return results

    async def add_thing(self, thing: IdentifiableDictConvertible) -> None:
        thing_id = thing.key
        thing_type = type(thing).__name__
        serialized_payload = orjson.dumps(thing.to_dict()).decode("utf-8")

        await self._db.execute(
            f"""
            INSERT INTO {self.table_name} (key, type, data)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET type=excluded.type, data=excluded.data;
        """,
            (thing_id, thing_type, serialized_payload),
        )
        await self._db.commit()

    async def remove_thing(self, thing_id: str) -> None:
        await self._db.execute(
            f"DELETE FROM {self.table_name} WHERE key = ?;", (thing_id,)
        )
        await self._db.commit()

    async def del_thing(self, thing_id: str) -> None:
        await self.remove_thing(thing_id)

    async def get_thing(
        self, thing_id: str, cls: typing.Type[T], default: T | None = None
    ) -> T:
        async with self._db.execute(
            f"SELECT * FROM {self.table_name} WHERE key = ?;", (thing_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                if default is not None:
                    return default
                raise ThingNotFound(
                    f"Element referenced by key token {thing_id} was missing from storage frames."
                )
            return self._deserialize(row, cls)

    @property
    def is_locked(self) -> bool:
        return self._locked

    # ==========================================
    # INDEXED METHOD PERFORMANCE OVERRIDES
    # ==========================================

    async def get_all_problems(self) -> List[FixedAnswerProblem]:
        async with self._db.execute(
            f"SELECT * FROM {self.table_name} WHERE type = 'FixedAnswerProblem';"
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._deserialize(r, FixedAnswerProblem) for r in rows]

    async def get_all_problems_by_guild(
        self, guild_id: GuildID
    ) -> List[FixedAnswerProblem]:
        # Optimization over structural full scan: leverages fast indexed json extraction queries
        async with self._db.execute(
            f"""
            SELECT * FROM {self.table_name} 
            WHERE type = 'FixedAnswerProblem' AND json_extract(data, '$.guild_id') IS ?;
        """,
            (guild_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._deserialize(r, FixedAnswerProblem) for r in rows]

    async def del_all_by_user_id(self, user_id: int) -> None:
        # Atomic sub-document deletions bypasses pulling everything into memory
        await self._db.execute(
            f"""
            DELETE FROM {self.table_name} 
            WHERE json_extract(data, '$.user_id') = ? 
               OR json_extract(data, '$.author') = ?;
        """,
            (user_id, user_id),
        )
        await self._db.commit()

    async def delete_all_by_guild_id(self, guild_id: int) -> None:
        await self._db.execute(
            f"""
            DELETE FROM {self.table_name} 
            WHERE json_extract(data, '$.guild_id') = ?;
        """,
            (guild_id,),
        )
        await self._db.commit()

    async def get_next_appeal_num(self, user_id: int) -> int:
        async with self._db.execute(
            f"""
            SELECT COUNT(*) FROM {self.table_name} 
            WHERE type = 'Appeal' AND json_extract(data, '$.user_id') = ?;
        """,
            (user_id,),
        ) as cursor:
            count = await cursor.fetchone()
            return (count[0] + 1) if count else 1

    # ==========================================
    # CORE INTERFACE SPECIFIC REQUIREMENTS
    # ==========================================

    async def initialize_sql_table(self):
        """Pre-initializes layout properties during explicit dependency workflow injections."""
        await self.initialize()

    async def run_sql(
        self, sql: str, placeholders: typing.Optional[typing.List[typing.Any]] = None
    ) -> dict:
        placeholders = placeholders or []
        async with self._db.execute(sql, placeholders) as cursor:
            if sql.strip().upper().startswith("SELECT"):
                rows = await cursor.fetchall()
                return {"results": [dict(r) for r in rows]}
            else:
                await self._db.commit()
                return {
                    "status": "Execution completed successfully.",
                    "changes": self._db.total_changes,
                }

    async def bgsave(
        self,
        schedule: typing.Any,
        path: str = None,
        wait: bool = False,
        raise_on_error: bool = False,
        replace: bool = False,
        **kwargs,
    ):
        """Bypassed safely. SQLite WAL logs automatically handle live persistent transactions directly."""
        pass
