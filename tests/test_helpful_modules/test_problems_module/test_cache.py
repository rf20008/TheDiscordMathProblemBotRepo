import pytest
from unittest.mock import AsyncMock

# import your interface + models
from helpful_modules.problems_module import AbstractCache
from helpful_modules.problems_module import (
    BaseProblem,
    Quiz,
    Appeal,
    UserData,
    GuildData,
)


# -----------------------------
# 1. Fixture: provide ANY cache
# -----------------------------
@pytest.fixture
def cache():
    """
    Replace this with:
    - RedisCache
    - SQLCache
    - FakeCache
    """
    raise NotImplementedError("Provide a concrete cache implementation")


# -----------------------------
# 2. add_thing / get_thing
# -----------------------------
@pytest.mark.asyncio
async def test_add_and_get_thing(cache):
    thing = GuildData(guild_id=123)

    await cache.add_thing(thing)

    result = await cache.get_thing(
        thing_id=thing.key,
        cls=GuildData,
        default=None
    )

    assert result is not None
    assert result.guild_id == 123


# -----------------------------
# 3. remove_thing
# -----------------------------
@pytest.mark.asyncio
async def test_remove_thing(cache):
    thing = UserData(user_id=42)

    await cache.add_thing(thing)
    await cache.remove_thing(thing.key)

    with pytest.raises(Exception):
        await cache.get_thing(thing.key, UserData)


# -----------------------------
# 4. has_thing
# -----------------------------
@pytest.mark.asyncio
async def test_has_thing(cache):
    thing = GuildData(guild_id=999)

    await cache.add_thing(thing)

    assert await cache.has_thing(thing.key) is True

    await cache.remove_thing(thing.key)

    assert await cache.has_thing(thing.key) is False


# -----------------------------
# 5. add_things batch default behavior
# -----------------------------
@pytest.mark.asyncio
async def test_add_things(cache):
    things = [GuildData(guild_id=i) for i in range(5)]

    await cache.add_things(things)

    all_things = await cache.get_all_things()

    assert len(all_things) >= 5


# -----------------------------
# 6. clear() behavior (CRITICAL TEST)
# -----------------------------
@pytest.mark.asyncio
async def test_clear_resets_state(cache):
    things = [GuildData(guild_id=i) for i in range(10)]

    for t in things:
        await cache.add_thing(t)

    await cache.clear(force=True)

    all_things = await cache.get_all_things()

    assert all_things == []


# -----------------------------
# 7. clear() must require force (if implemented that way)
# -----------------------------
@pytest.mark.asyncio
async def test_clear_requires_force(cache):
    with pytest.raises(Exception):
        await cache.clear(force=False)


# -----------------------------
# 8. update_problem delegates to add_problem
# -----------------------------
@pytest.mark.asyncio
async def test_update_problem(cache):
    problem = BaseProblem(problem_id=1, guild_id=None)

    await cache.add_problem(1, problem)

    updated = BaseProblem(problem_id=1, guild_id=None, text="updated")

    await cache.update_problem(1, updated)

    result = await cache.get_problem(None, 1)

    assert result.text == "updated"


# -----------------------------
# 9. user permissions logic
# -----------------------------
@pytest.mark.asyncio
async def test_permissions(cache):
    user_id = 123

    user = UserData(user_id=user_id, trusted=True, denylisted=False)
    await cache.add_user_data(user)

    perms = {"trusted": True}

    assert await cache.user_meets_permissions_required_to_use_command(
        user_id=user_id,
        permissions_required=perms
    ) is True


# -----------------------------
# 10. global problems fallback
# -----------------------------
@pytest.mark.asyncio
async def test_global_problems(cache):
    problems = await cache.get_global_problems()
    assert isinstance(problems, list)

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "factory, add_fn, get_fn, remove_fn",
    [
        ( # Base Problems
            lambda: BaseProblem(problem_id=1, guild_id=None),
            lambda c, o: c.add_problem(1, o),
            lambda c, o: c.get_problem(None, 1),
            lambda c, o: c.remove_problem(1, None),
        ),
        (
            lambda: Quiz(quiz_id=10),
            lambda c, o: c.add_quiz(10, o),
            lambda c, o: c.get_quiz(10),
            lambda c, o: c.remove_quiz(10),
        ),
        (
            lambda: UserData(user_id=42),
            lambda c, o: c.add_user_data(o),
            lambda c, o: c.get_user_data(42),
            lambda c, o: c.del_verification_code_info(42),
        ),
        (
            lambda: GuildData(guild_id=7),
            lambda c, o: c.add_guild_data(o),
            lambda c, o: c.get_guild_data(7),
            lambda c, o: c.remove_guild_data(7),
        ),
        (
            lambda: Appeal(special_id=99),
            lambda c, o: c.add_appeal(o),
            lambda c, o: c.get_appeal(99),
            lambda c, o: c.remove_appeal(o),
        ),
        ( # AppealViewInfos

        )
        ( # Things
            lambda: GuildData(guild_id=123),  # any IdentifiableDictConvertible
            lambda c, o: c.add_thing(o),
            lambda c, o: c.get_thing(o.key, type(o)),
            lambda c, o: c.remove_thing(o.key),
        ),
    ],
)
async def test_cache_crud(cache, factory, add_fn, get_fn, remove_fn):
    obj = factory()

    await add_fn(cache, obj)

    result = await get_fn(cache, obj)

    assert result == obj   # <- your requested change

    await remove_fn(cache, obj)

    with pytest.raises(Exception):
        await get_fn(cache, obj)