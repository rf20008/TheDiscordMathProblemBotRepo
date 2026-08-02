import typing
from typing import List, Tuple
import warnings
import orjson
from abc import ABC
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

# Assuming these are imported relative to your project structure
from .appeal import Appeal, AppealViewInfo
from .fixed_answer_problem import FixedAnswerProblem
from .dict_convertible import DictConvertible, IdentifiableDictConvertible
from .errors import (
    ThingNotFound,
    CorruptedDataException,
)
from .AbstractKVCache import AbstractKVBasedCache
from .register_dicts import PREFIX_REGISTRY
GuildID = typing.Optional[int]
T = typing.TypeVar("T", bound=IdentifiableDictConvertible)


class MongoCache(AbstractKVBasedCache):
    def __init__(
        self,
        db_client: AsyncIOMotorClient,
        db_name: str,
        collection_name: str,
        *args,
        **kwargs,
    ) -> None:
        """
        Initialize the MongoDB Cache implementation.

        Documents are stored with an '_id' field mapping to the unique key string,
        a 'type' field representing the class type (e.g., 'Quiz', 'FixedAnswerProblem'),
        and a 'data' field containing the raw serialized object or dictionary.
        """
        super().__init__(*args, **kwargs)
        self.client: AsyncIOMotorClient = db_client
        self.db = self.client[db_name]
        self.collection: AsyncIOMotorCollection = self.db[collection_name]
        self._locked = False

    async def create_indexes(self) -> None:
        """Helper method to set up performance indexes for optimized scans."""
        # Index on type to quickly find subsets (e.g., all problems, all appeals)
        await self.collection.create_index("type")
        # Compound index for fast guild-specific lookups within problems
        await self.collection.create_index([("type", 1), ("data.guild_id", 1)])

    # ==========================================
    # CORE ABSTRACT METHOD IMPLEMENTATIONS
    # ==========================================

    async def clear(self, force=False):
        """Clear the database collection entirely."""
        await self.collection.delete_many({})

    async def get_all_things(self) -> list[IdentifiableDictConvertible]:
        """Return a list of EVERYTHING in the database."""
        things = []
        async for doc in self.collection.find({}):
            cls_type = PREFIX_REGISTRY.get(doc["type"])
            if cls_type:
                things.append(self._deserialize(doc, cls_type))
        return things

    async def items(self) -> list[tuple[str, IdentifiableDictConvertible]]:
        """Return a list of EVERYTHING in the database along with their unique string keys."""
        items_list = []
        async for doc in self.collection.find({}):
            cls_type = PREFIX_REGISTRY.get(doc["type"])
            if cls_type:
                items_list.append((doc["_id"], self._deserialize(doc, cls_type)))
        return items_list

    async def add_thing(self, thing: IdentifiableDictConvertible) -> None:
        """Upsert a dictionary convertible object into MongoDB using its strict protocol contract."""
        thing_type = type(thing).__name__

        # Enforce the strict protocol contract: use the .key property on the instance
        thing_id = thing.key

        await self.collection.replace_one(
            {"_id": thing_id},
            {
                "_id": thing_id,
                "type": thing_type,
                "data": thing.to_dict(),  # Guaranteed by DictConvertible
            },
            upsert=True,
        )

    def _deserialize(self, doc: dict, cls: typing.Type[T]) -> T:
        """Helper to convert MongoDB document back into its structured class object via from_dict."""
        try:
            data = doc["data"]
            # Strictly use from_dict as guaranteed by the DictConvertible protocol
            return cls.from_dict(data)
        except Exception as e:
            raise CorruptedDataException(
                f"Failed to parse data into {cls.__name__} using from_dict: {e}"
            )

    async def remove_thing(self, thing_id: str) -> None:
        """Removes an object from MongoDB by its structural key."""
        await self.collection.delete_one({"_id": thing_id})

    async def del_thing(self, thing_id: str) -> None:
        """Alias handling for internal deletion mechanisms."""
        await self.remove_thing(thing_id)

    async def get_thing(
        self,
        thing_id: str,
        cls: typing.Type[T],
        default: T | None = None,
    ) -> T:
        """Retrieve an object by its structural ID string."""
        doc = await self.collection.find_one({"_id": thing_id})
        if not doc:
            if default is not None:
                return default
            raise ThingNotFound(f"Object with ID {thing_id} not found in database.")
        return self._deserialize(doc, cls)

    @property
    def is_locked(self) -> bool:
        return self._locked

    async def get_next_appeal_num(self, user_id: int) -> int:
        """Gets the next unique appeal incrementing token for a user."""
        # Counts current appeals under that specific user to issue the next sequence number
        count = await self.collection.count_documents(
            {"type": "Appeal", "data.user_id": user_id}
        )
        return count + 1

    # ==========================================
    # OVERRIDING SLOW BASE-CLASS IMPLEMENTATIONS
    # ==========================================

    async def get_appeal_view_infos(self) -> list[AppealViewInfo]:
        """Optimized: Uses a direct indexed lookup on 'type' rather than a string start filter."""
        appeals_view = []
        async for doc in self.collection.find({"type": "AppealViewInfo"}):
            appeals_view.append(self._deserialize(doc, AppealViewInfo))
        return appeals_view

    async def get_all_appeals(self) -> list[Appeal]:
        """Optimized: Native database selection filter."""
        appeals = []
        async for doc in self.collection.find({"type": "Appeal"}):
            appeals.append(self._deserialize(doc, Appeal))
        return appeals

    async def get_all_problems(self) -> List[FixedAnswerProblem]:
        """Optimized: Native targeted filter instead of scanning the full workspace."""
        problems = []
        async for doc in self.collection.find({"type": "FixedAnswerProblem"}):
            problems.append(self._deserialize(doc, FixedAnswerProblem))
        return problems

    async def get_all_problems_by_guild(
        self, guild_id: GuildID
    ) -> List[FixedAnswerProblem]:
        """Optimized: Sub-document structural filtering execution using indexing."""
        problems = []
        async for doc in self.collection.find(
            {"type": "FixedAnswerProblem", "data.guild_id": guild_id}
        ):
            problems.append(self._deserialize(doc, FixedAnswerProblem))
        return problems
