import aioredis
from ..errors import LockedCacheException, ProblemNotFoundException
from ..base_problem import BaseProblem
import asyncio
import orjson
class ProblemsRelatedRedisCache:
    """A class that is supposed to handle the problems, and have the same API as problems_related_cache"""
    def __init__(self, redis_url: str, password: str):
        self.redis_url = redis_url
        self.password = password
        self.redis = aioredis.from_url(redis_url, encoding = "utf-8", decode_responses=True, password=password)
        self.lock = asyncio.Lock()
    @property
    def is_locked(self):
        """Return whether the cache is locked"""
        return self.lock.locked()

    async def get_key(self, thing: str):
        """Return the value with key thing
        Time complexity: O(1)"""
        return await self.redis.hget(thing)
    async def set_key(self, key: str, value: str):
        """Set the thing at key to value.
        Time complexity: O(1)
        :param key: the key
        :param value: the value
        :return: Nothing
        :raises LockedCacheException: If the cache is locked"""
        if self.is_locked:
            raise LockedCacheException("The cache is currently locked!")
        await self.redis.hset(key, value)
    async def del_key(self, key: str):
        """Delete the key associated with key:
        Time complexity: O(1)"""
        if self.is_locked:
            raise LockedCacheException("The cache is currently locked")
        await self.redis.hdel(key)
    async def get_problem(self, guild_id: int, problem_id: int) -> BaseProblem:
        """Attempt to return the problem with guild_id and problem_id =problem_id
        Time complexity: O(1)"""
        if guild_id is not None and not isinstance(guild_id, int):
            raise TypeError("guild_id is not an int")
        result = await self.get_key(f"problem:{guild_id}:{problem_id}")
        if result is not None:
            return BaseProblem.from_dict(orjson.loads(result))
        result = await self.get_key(f"quiz_problems:{guild_id}:{problem_i}")
        if result is not None:
            return BaseProblem.from_dict(orjson.loads(result))
        raise ProblemNotFoundException("That problem is not found")
    async def get_all_problems(self):
        """Return a list of all problems!
        Time complexity: O(N)"""
        return list(map(BaseProblem.from_dict, await self.redis.hgetall("problem").values()))
    async def get_all_problems_by_guild(self, guild_id: int | None):
        """return a list of all problems with the guild id = id
        Time complexity: O(N)"""
        return list(map(BaseProblem.from_dict, await self.redis.hgetall(f"problem:{guild_id}").values()))
    async def get_all_problems_by_func(self, func):
        """Return a list of all problems that satisfy the function.
        It is actually implemented as filter(func, await self.get_all_problems())
        Time complexity: O(N + sumF(P) over all problems) where F(P) is the big O runtime
        of calling func on a problem P"""
        return filter(func, await self.get_all_problems())
    async def get_global_problems(self):
        return await self.get_all_problems_by_guild(None)
    async def add_empty_guild(self):
        raise NotImplementedError("This method is deprecated")

    async def add_problem(self, problem_id: int, problem: BaseProblem):
        if not isinstance(problem_id, int) or not isinstance(problem, BaseProblem):
            raise TypeError("Problem_id is not an int or problem is not a base problem")
        if problem.id != problem_id:
            raise ValueError("Ids do not match")

        await self.set_key(f"problem:{problem.guild_id}:{problem_id}", problem.to_dict(show_answer=True))

