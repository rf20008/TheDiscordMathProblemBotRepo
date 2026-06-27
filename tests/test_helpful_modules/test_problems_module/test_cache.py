import pytest
from unittest.mock import AsyncMock

# import your interface + models
from helpful_modules.problems_module import AbstractCache, ThingNotFound
from helpful_modules.problems_module import (
    FixedAnswerProblem,
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
    problem = FixedAnswerProblem(problem_id=1, guild_id=None)

    await cache.add_problem(1, problem)

    updated = FixedAnswerProblem(problem_id=1, guild_id=None, text="updated")

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
    "factory, add_fn, get_fn, remove_fn, modify_fn",
    [
        (  # Base Problems
                lambda: FixedAnswerProblem(problem_id=1, guild_id=None, answer="initial"),
                lambda c, o: c.add_problem(1, o),
                lambda c, o: c.get_problem(None, 1),
                lambda c, o: c.remove_problem(1, None),
                lambda o: setattr(o, "answer", "updated") or o,
        ),
        (  # Quizzes
                lambda: Quiz(quiz_id=10, name="Math Quiz"),
                lambda c, o: c.add_quiz(10, o),
                lambda c, o: c.get_quiz(10),
                lambda c, o: c.remove_quiz(10),
                lambda o: setattr(o, "name", "Updated Quiz") or o,
        ),
        (  # UserData
                lambda: UserData(user_id=42, xp=100),
                lambda c, o: c.add_user_data(o),
                lambda c, o: c.get_user_data(42),
                lambda c, o: c.remove_user_data(o),  # Fixed from verification code info
                lambda o: setattr(o, "xp", 250) or o,
        ),
        (  # GuildData
                lambda: GuildData(guild_id=7, prefix="!"),
                lambda c, o: c.add_guild_data(o),
                lambda c, o: c.get_guild_data(7),
                lambda c, o: c.remove_guild_data(7),
                lambda o: setattr(o, "prefix", "?") or o,
        ),
        (  # Appeal
                lambda: Appeal(special_id=99, status="pending"),
                lambda c, o: c.add_appeal(o),
                lambda c, o: c.get_appeal(99),
                lambda c, o: c.remove_appeal(o),
                lambda o: setattr(o, "status", "approved") or o,
        ),
        (  # AppealViewInfo
                lambda: AppealViewInfo(message_id=555, channel_id=111),
                lambda c, o: c.set_appeal_view_info(o),
                lambda c, o: c.get_appeal_view_info(o),
                lambda c, o: c.del_appeal_view_info(555),
                lambda o: setattr(o, "channel_id", 222) or o,
        ),
        (  # Generic Things
                lambda: GuildData(guild_id=123, prefix="old"),
                lambda c, o: c.add_thing(o),
                lambda c, o: c.get_thing(o.key, type(o)),
                lambda c, o: c.remove_thing(o.key),
                lambda o: setattr(o, "prefix", "new") or o,
        ),
    ],
)
async def test_cache_upsert_and_crud(cache, factory, add_fn, get_fn, remove_fn, modify_fn):
    # 1. Create and Insert Initial Object
    obj = factory()
    await add_fn(cache, obj)

    # Verify initial insert worked
    first_result = await get_fn(cache, obj)
    assert first_result == obj

    # 2. Modify Object and Trigger Upsert (The Update Part)
    modified_obj = modify_fn(obj)
    await add_fn(cache, modified_obj)  # Calls add_thing / add_problem again on same key

    # 3. Assert Changes Persisted Successfully
    updated_result = await get_fn(cache, modified_obj)
    assert updated_result == modified_obj
    assert updated_result != factory()  # Ensure it matches the modified values, not original ones

    # 4. Cleanup and Removal
    await remove_fn(cache, modified_obj)

    with pytest.raises(Exception):
        await get_fn(cache, modified_obj)


# ==========================================
# 1. THE MISSING DATA & DEFAULT FALLBACK TEST
# ==========================================
@pytest.mark.asyncio
async def test_cache_missing_data_behavior(cache):
    fake_key = "UserData:999999999"

    # Assert strict failure when no default is given
    with pytest.raises(ThingNotFound):
        await cache.get_thing(fake_key, cls=UserData, default=None)

    # Assert clean fallback when a default is provided
    default_user = UserData.default(user_id=999999999)
    result = await cache.get_thing(fake_key, cls=UserData, default=default_user)
    assert result == default_user

    # Assert it raises if None is explicitly passed as a default
    with pytest.raises(ThingNotFound):
        await cache.get_thing(fake_key, cls=UserData, default=None)



# ==========================================
# 2. BULK EXTRACTION & FILTERING TEST
# ==========================================
@pytest.mark.asyncio
async def test_bulk_extraction_and_filtering(cache):
    # Setup problems across multiple guilds
    guild_a = 1111
    guild_b = 2222

    prob1 = FixedAnswerProblem(problem_id=1, guild_id=guild_a, answer="A1")
    prob2 = FixedAnswerProblem(problem_id=2, guild_id=guild_a, answer="A2")
    prob3 = FixedAnswerProblem(problem_id=3, guild_id=guild_b, answer="B1")

    await cache.add_problem(1, prob1)
    await cache.add_problem(2, prob2)
    await cache.add_problem(3, prob3)

    # Test filtering by specific guild
    guild_a_probs = await cache.get_all_problems_by_guild(guild_a)
    assert len(guild_a_probs) == 2
    assert prob1 in guild_a_probs
    assert prob2 in guild_a_probs
    assert prob3 not in guild_a_probs

    # Test pulling absolutely everything
    all_probs = await cache.get_all_problems()
    assert len(all_probs) == 3

    # Cleanup
    await cache.clear(force=True)

# ==========================================
# 3. CASCADE DELETION TEST (MASS EVICTION)
# ==========================================
@pytest.mark.asyncio
async def test_cascade_deletion_by_guild(cache):
    target_guild = 7777
    other_guild = 8888

    # Populate target guild data mix
    guild_config = GuildData(guild_id=target_guild, prefix="!")
    prob_target = FixedAnswerProblem(problem_id=100, guild_id=target_guild, answer="Yes")

    # Populate separate safe guild data
    prob_safe = FixedAnswerProblem(problem_id=200, guild_id=other_guild, answer="No")

    await cache.add_guild_data(guild_config)
    await cache.add_problem(100, prob_target)
    await cache.add_problem(200, prob_safe)

    # Execute mass cascade wipeout
    await cache.delete_all_by_guild_id(target_guild)

    # Verify target items are cleanly dropped
    with pytest.raises(ThingNotFound):
        await cache.get_guild_data(target_guild)
    with pytest.raises(ThingNotFound):
        await cache.get_problem(target_guild, 100)

    # Verify the unrelated guild data was left completely untouched
    safe_check = await cache.get_problem(other_guild, 200)
    assert safe_check == prob_safe

    # Cleanup remaining item
    await cache.remove_problem(200, other_guild)


# ==========================================
# 4. DATA CORRUPTION PROTECTION TEST
# ==========================================
@pytest.mark.asyncio
async def test_data_corruption_handling(cache):
    corrupt_key = "UserData:5555"

    # Dynamically handle insertion based on adapter architecture
    if hasattr(cache, "run_sql"):
        # For SQLiteCache / PostgresCache: Write invalid unparseable raw fragments
        await cache.initialize_sql_table()
        await cache.run_sql(
            f"INSERT INTO {cache.table_name} (key, type, data) VALUES (?, ?, ?);",
            [corrupt_key, "UserData", "{broken-json-payload,,}"]
        )
    elif hasattr(cache, "_collection"):
        # For MongoCache: Insert broken data shapes manually bypassing serializers
        await cache._collection.insert_one({"_id": corrupt_key, "type": "UserData", "data": "not-a-dict"})
    else:
        # For RAMCache / RedisCache raw string sets
        raw_driver = getattr(cache, "_db", cache)
        if hasattr(raw_driver, "set"):  # Redis native client
            await raw_driver.set(corrupt_key, b"!!corrupt raw string value!!")
        else:  # Dictionary storage mapping fallback
            cache._storage[corrupt_key] = ("UserData", b"!!corrupt!!")

    # Accessing this entity must trigger CorruptedDataException safely instead of internal driver crashes
    with pytest.raises(CorruptedDataException):
        await cache.get_thing(corrupt_key, cls=UserData)

    # Cleanup manually from underlying driver storage frameworks
    if hasattr(cache, "run_sql"):
        await cache.run_sql(f"DELETE FROM {cache.table_name} WHERE key = ?;", [corrupt_key])
    elif hasattr(cache, "_collection"):
        await cache._collection.delete_one({"_id": corrupt_key})
    else:
        try:
            await cache.remove_thing(corrupt_key)
        except Exception:
            pass


@pytest.mark.asyncio
async def test_cache_clear_force(cache):
    # 1. Populate the cache with diverse data types
    user = UserData(user_id=12345, xp=500)
    guild = GuildData(guild_id=999, prefix="!")
    prob = FixedAnswerProblem(problem_id=55, guild_id=999, answer="42")

    await cache.add_user_data(user)
    await cache.add_guild_data(guild)
    await cache.add_problem(55, prob)

    # Quick sanity check: Ensure things were actually written
    all_items_before = await cache.get_all_things()
    assert len(all_items_before) == 3

    # 2. Execute the clear operation
    await cache.clear(force=True)

    # 3. Assert that the database is completely empty
    all_items_after = await cache.get_all_things()
    assert len(all_items_after) == 0, "Database should be completely empty after clear(force=True)"

    # 4. Double check individual key lookups throw ThingNotFound
    with pytest.raises(ThingNotFound):
        await cache.get_user_data(12345)

    with pytest.raises(ThingNotFound):
        await cache.get_problem(999, 55)


@pytest.mark.asyncio
async def test_cache_items_starting_with(cache):
    # Setup mixed keys
    user1 = UserData(user_id=101, xp=10)
    user2 = UserData(user_id=102, xp=20)
    quiz = Quiz(quiz_id=555)

    await cache.add_user_data(user1)
    await cache.add_user_data(user2)
    await cache.add_quiz(555, quiz)

    # Grab only items starting with the "UserData" namespace prefix
    user_items = await cache.get_all_items_starting_with("UserData")
    assert len(user_items) == 2

    keys = [item[0] for item in user_items]
    assert user1.key in keys
    assert user2.key in keys
    assert quiz.key not in keys


@pytest.mark.asyncio
async def test_get_all_things_for_func(cache):
    user_low = UserData(user_id=1, xp=10)
    user_high = UserData(user_id=2, xp=500)  # Target

    await cache.add_user_data(user_low)
    await cache.add_user_data(user_high)

    # Filter for UserData types with high XP scores
    def is_high_xp_user(thing):
        return isinstance(thing, UserData) and thing.xp > 100

    results = await cache.get_all_things_for_func(is_high_xp_user)
    assert len(results) == 1
    assert results[0].user_id == 2