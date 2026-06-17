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
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Type, TypeVar

from .cache_ABC import AbstractCache, GuildID
from .fixed_answer_problem import FixedAnswerProblem
from .GuildData import GuildData
from .quizzes import Quiz
from .user_data import UserData
from .appeal import Appeal, AppealViewInfo
from .verification_code_info import VerificationCodeInfo
from .dict_convertible import IdentifiableDictConvertible
from .errors import (
    ThingNotFound,
    ProblemNotFound,
    QuizNotFound,
    AppealViewInfoNotFound,
    ClearProhibitedError
)

T = TypeVar("T", bound=IdentifiableDictConvertible)


class MongoCache(AbstractCache):
    def __init__(self, mongo_uri: str, db_name: str = "bot"):
        super().__init__()
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[db_name]

        # collections
        self.problems = self.db["problems"]
        self.quizzes = self.db["quizzes"]
        self.users = self.db["users"]
        self.guilds = self.db["guilds"]
        self.appeals = self.db["appeals"]
        self.verification = self.db["verification"]
        self.appeal_views = self.db["appeal_views"]
        self.things = self.db["things"]

    # -------------------------
    # INDEX SETUP (IMPORTANT)
    # -------------------------
    async def init_indexes(self):
        await self.problems.create_index(
            [("guild_id", 1), ("problem_id", 1)],
            unique=True
        )
        await self.problems.create_index("guild_id")

        await self.quizzes.create_index("quiz_id", unique=True)
        await self.users.create_index("user_id", unique=True)
        await self.guilds.create_index("_id", unique=True)

    # -------------------------
    # CORE THING STORAGE
    # -------------------------
    async def add_thing(self, thing: IdentifiableDictConvertible) -> None:
        data = thing.to_dict()
        await self.things.update_one(
            {"_id": thing.id},
            {"$set": data},
            upsert=True
        )

    async def remove_thing(self, thing_id: str) -> None:
        await self.things.delete_one({"_id": thing_id})

    async def get_thing(
        self,
        thing_id: str,
        cls: Type[T],
        default: T | None = None,
    ) -> T | None:
        doc = await self.things.find_one({"_id": thing_id})
        if not doc:
            if default is not None:
                return default
            raise ThingNotFound()
        return cls.from_dict(doc)

    async def get_all_things(self) -> list[object]:
        return await self.things.find().to_list(None)

    # -------------------------
    # PROBLEMS (FAST PATH)
    # -------------------------
    async def add_problem(self, problem_id: int, problem: FixedAnswerProblem):
        doc = problem.to_dict()
        doc["problem_id"] = problem_id
        doc["guild_id"] = problem.guild_id

        await self.problems.update_one(
            {"guild_id": problem.guild_id, "problem_id": problem_id},
            {"$set": doc},
            upsert=True
        )

    async def remove_problem(self, problem_id: int, guild_id: GuildID):
        await self.problems.delete_one(
            {"guild_id": guild_id, "problem_id": problem_id}
        )

    async def get_problem(self, guild_id: GuildID, problem_id: int) -> FixedAnswerProblem:
        doc = await self.problems.find_one(
            {"guild_id": guild_id, "problem_id": problem_id}
        )
        if not doc:
            raise ProblemNotFound()
        return FixedAnswerProblem.from_dict(doc)

    async def get_all_problems(self) -> List[FixedAnswerProblem]:
        docs = await self.problems.find().to_list(None)
        return [FixedAnswerProblem.from_dict(d) for d in docs]

    # -------------------------
    # ⭐ KEY METHOD YOU ASKED FOR
    # -------------------------
    async def num_guild_problems(self, guild_id: GuildID) -> int:
        return await self.problems.count_documents(
            {"guild_id": guild_id}
        )

    # -------------------------
    # QUIZZES
    # -------------------------
    async def add_quiz(self, quiz_id: int, quiz: Quiz) -> Quiz:
        await self.quizzes.update_one(
            {"quiz_id": quiz_id},
            {"$set": quiz.to_dict()},
            upsert=True
        )
        return quiz

    async def get_quiz(self, quiz_id: int) -> Quiz:
        doc = await self.quizzes.find_one({"quiz_id": quiz_id})
        if not doc:
            raise QuizNotFound()
        return Quiz.from_dict(doc)

    async def remove_quiz(self, quiz_id: int) -> None:
        await self.quizzes.delete_one({"quiz_id": quiz_id})

    # -------------------------
    # USERS
    # -------------------------
    async def get_user_data(self, user_id: int, default: UserData | None = None):
        doc = await self.users.find_one({"user_id": user_id})
        if not doc:
            return default
        return UserData.from_dict(doc)

    async def add_user_data(self, user_data: UserData) -> None:
        await self.users.update_one(
            {"user_id": user_data.user_id},
            {"$set": user_data.to_dict()},
            upsert=True
        )

    # -------------------------
    # GUILD DATA
    # -------------------------
    async def add_guild_data(self, guild_data: GuildData) -> None:
        await self.guilds.update_one(
            {"_id": guild_data.guild_id},
            {"$set": guild_data.to_dict()},
            upsert=True
        )

    async def remove_guild_data(self, guild_id: GuildID) -> None:
        await self.guilds.delete_one({"_id": guild_id})

    async def get_guild_data(self, guild_id: GuildID) -> GuildData:
        doc = await self.guilds.find_one({"_id": guild_id})
        if not doc:
            raise ThingNotFound()
        return GuildData.from_dict(doc)

    # -------------------------
    # APPEALS
    # -------------------------
    async def add_appeal(self, appeal: Appeal) -> None:
        await self.appeals.update_one(
            {"_id": appeal.special_id},
            {"$set": appeal.to_dict()},
            upsert=True
        )

    async def get_appeal(self, special_id: int, default: Appeal | None = None):
        doc = await self.appeals.find_one({"_id": special_id})
        if not doc:
            if default is not None:
                return default
            raise ThingNotFound()
        return Appeal.from_dict(doc)

    async def get_all_appeals(self) -> list[Appeal]:
        docs = await self.appeals.find().to_list(None)
        return [Appeal.from_dict(d) for d in docs]

    async def remove_appeal(self, appeal: Appeal) -> None:
        await self.appeals.delete_one({"_id": appeal.special_id})

    # -------------------------
    # APPEAL VIEW INFO
    # -------------------------
    async def set_appeal_view_info(self, view_info: AppealViewInfo):
        await self.appeal_views.update_one(
            {"message_id": view_info.message_id},
            {"$set": view_info.to_dict()},
            upsert=True
        )

    async def get_appeal_view_info(self, view_info: AppealViewInfo):
        doc = await self.appeal_views.find_one(
            {"message_id": view_info.message_id}
        )
        if not doc:
            raise AppealViewInfoNotFound()
        return AppealViewInfo.from_dict(doc)

    async def del_appeal_view_info(self, message_id: int):
        await self.appeal_views.delete_one({"message_id": message_id})

    async def get_appeal_view_infos(self):
        docs = await self.appeal_views.find().to_list(None)
        return [AppealViewInfo.from_dict(d) for d in docs]

    # -------------------------
    # VERIFICATION
    # -------------------------
    async def get_verification_code_info(self, user_id: int):
        doc = await self.verification.find_one({"user_id": user_id})
        if not doc:
            raise ThingNotFound()
        return VerificationCodeInfo.from_dict(doc)

    async def set_verification_code_info(self, code_info: VerificationCodeInfo):
        await self.verification.update_one(
            {"user_id": code_info.user_id},
            {"$set": code_info.to_dict()},
            upsert=True
        )

    async def del_verification_code_info(self, user_id: int):
        await self.verification.delete_one({"user_id": user_id})

    # -------------------------
    # USER-GLOBAL SCAN
    # -------------------------
    async def get_all_by_user_id(self, user_id: int) -> list[dict]:
        cursor = self.things.find({
            "$or": [
                {"author": user_id},
                {"authors": user_id},
                {"user_id": user_id},
            ]
        })
        return await cursor.to_list(None)

    async def del_all_by_user_id(self, user_id: int) -> None:
        await self.things.delete_many({
            "$or": [
                {"author": user_id},
                {"authors": user_id},
                {"user_id": user_id},
            ]
        })

    async def delete_all_by_guild_id(self, guild_id: int) -> None:
        await self.problems.delete_many({"guild_id": guild_id})

    # -------------------------
    # LOCK STATE (simple stub)
    # -------------------------
    @property
    def is_locked(self) -> bool:
        return False

    async def clear(self, force: bool = False) -> None:
        """
        Safely wipes all data out of the cache collections. Preserves index layouts.

        :param force: Explicit confirmation flag required to clear.
        :raises ClearProhibitedError: If executed inside a production environment.
        :raises ValueError: If force=True is omitted.
        """
        if self.is_production:
            raise ClearProhibitedError(
                f"Aborting destructive action! Clear operation is strictly prohibited "
                f"while your system environment is flagged as '{self.environment}'."
            )

        if not force:
            raise ValueError("You must pass 'force=True' to clear this database instance.")

        # Gather your active internal collection bindings
        collections_to_wipe = [
            self.problems, self.quizzes, self.users, self.guilds,
            self.appeals, self.verification, self.appeal_views, self.things
        ]

        # Wipe contents using delete_many without losing index blueprints
        for collection in collections_to_wipe:
            await collection.delete_many({})