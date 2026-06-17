import pytest
from unittest.mock import MagicMock

# Ensure these match the exact import paths of your data models and exceptions
from .your_cache_module import (
    BaseProblem,
    Quiz,
    UserData,
    Appeal,
    AppealViewInfo,
    VerificationCodeInfo,
    GuildData,
    ThingNotFound,
)


# Assuming StubCache is imported from your stub file
# from .your_stub_file import StubCache


@pytest.fixture
def cache():
    """Initializes your existing StubCache implementation."""
    return StubCache()


# ==============================================================================
# 1. CORE THING CONTRACTS
# ==============================================================================

@pytest.mark.asyncio
async def test_thing_lifecycle_with_real_models(cache):
    """Validates that add_thing, get_thing, and remove_thing handle data model type parameters correctly."""
    # UserData inherits from IdentifiableDictConvertible via its structure
    user_id = 55555
    real_user = UserData.default(user_id=user_id)

    # Contract: add_thing accepts the object
    await cache.add_thing(real_user)

    # Contract: get_thing returns the precise type requested or matches structural signature
    retrieved = await cache.get_thing(str(user_id), cls=UserData)
    assert retrieved == real_user
    assert retrieved.user_id == user_id

    # Contract: get_all_things contains the item
    all_things = await cache.get_all_things()
    assert real_user in all_things

    # Contract: remove_thing evicts the item from the structural contract
    await cache.remove_thing(str(user_id))
    assert await cache.get_thing(str(user_id), cls=UserData) is None


# ==============================================================================
# 2. PROBLEMS CONTRACTS
# ==============================================================================

@pytest.mark.asyncio
async def test_problems_contract_with_real_base_problem(cache):
    """Validates parameters constraints and type safety metrics using an actual BaseProblem instance."""
    guild_id = 999111
    problem_id = 42

    # Constructing a real BaseProblem instance from a valid layout dictionary
    problem_data = {
        "guild_id": guild_id,
        "description": "Solve for x: 2x + 4 = 10",
        "answer": "3",
    }
    real_problem = BaseProblem.from_dict(problem_data)

    # Contract: add_problem safely maps parameters
    await cache.add_problem(problem_id=problem_id, problem=real_problem)

    # Contract: num_guild_problems returns an accurate count
    assert await cache.num_guild_problems(guild_id) == 1

    # Contract: get_problem maps types and returns a working instance matching the parameters
    retrieved = await cache.get_problem(guild_id=guild_id, problem_id=problem_id)
    assert isinstance(retrieved, BaseProblem)
    assert retrieved.guild_id == guild_id

    # Contract: get_all_problems matches the total array length signature
    all_probs = await cache.get_all_problems()
    assert len(all_probs) == 1
    assert all_probs[0].guild_id == guild_id

    # Contract: remove_problem handles targeted deletion constraints
    await cache.remove_problem(problem_id=problem_id, guild_id=guild_id)
    assert await cache.num_guild_problems(guild_id) == 0


# ==============================================================================
# 3. QUIZZES CONTRACTS
# ==============================================================================

@pytest.mark.asyncio
async def test_quiz_contract_with_real_quiz(cache):
    """Validates parameters constraints for Quiz lifecycle tracking routines using a structural Quiz instance."""
    quiz_id = 707
    quiz_data = {
        "quiz_id": quiz_id,
        "questions": ["What is 1+1?", "What is 2+2?"],
        "title": "Basic Calculus",
    }
    real_quiz = Quiz.from_dict(quiz_data)

    # Contract: add_quiz returns the exact Quiz instance passed in
    returned_quiz = await cache.add_quiz(quiz_id=quiz_id, quiz=real_quiz)
    assert isinstance(returned_quiz, Quiz)
    assert returned_quiz.quiz_id == quiz_id

    # Contract: get_quiz returns the matched entity structure
    retrieved = await cache.get_quiz(quiz_id=quiz_id)
    assert retrieved == real_quiz

    # Contract: remove_quiz handles deletion
    await cache.remove_quiz(quiz_id=quiz_id)
    assert await cache.get_quiz(quiz_id=quiz_id) is None


# ==============================================================================
# 4. USER DATA CONTRACTS
# ==============================================================================

@pytest.mark.asyncio
async def test_user_data_contract_with_real_user_data(cache):
    """Validates structural contracts for UserData state changes and type fallbacks."""
    user_id = 88888888
    user_payload = {
        "user_id": user_id,
        "trusted": True,
        "denylisted": False,
        "xp": 150,
    }
    real_user = UserData.from_dict(user_payload)

    await cache.add_user_data(real_user)
    retrieved = await cache.get_user_data(user_id)
    assert isinstance(retrieved, UserData)
    assert retrieved.trusted is True
    assert retrieved.denylisted is False

    # Contract: get_user_data default type fallback parameter safety checks
    fallback_user = UserData.default(user_id=111)
    result = await cache.get_user_data(999, default=fallback_user)
    assert result == fallback_user


# ==============================================================================
# 5. APPEALS AND VIEWS CONTRACTS
# ==============================================================================

@pytest.mark.asyncio
async def test_appeals_and_views_contract_with_real_models(cache):
    """Validates signature constraints for system Appeals and UI tracking layouts."""
    special_id = 100002
    appeal_data = {
        "_id": special_id,
        "user_id": 12345,
        "reason": "I am not a bot.",
        "status": "pending",
    }
    real_appeal = Appeal.from_dict(appeal_data)

    await cache.add_appeal(real_appeal)
    assert await cache.get_appeal(special_id) == real_appeal
    assert len(await cache.get_all_appeals()) == 1

    # Appeal View Contract Validation
    message_id = 444555666
    view_data = {
        "message_id": message_id,
        "guild_id": 1234,
        "channel_id": 5678,
    }
    real_view = AppealViewInfo.from_dict(view_data)

    await cache.set_appeal_view_info(real_view)
    assert await cache.get_appeal_view_info(real_view) == real_view
    assert len(await cache.get_appeal_view_infos()) == 1

    # Cleanup
    await cache.del_appeal_view_info(message_id)
    await cache.remove_appeal(real_appeal)


# ==============================================================================
# 6. GUILDS & VERIFICATION CODES CONTRACTS
# ==============================================================================

@pytest.mark.asyncio
async def test_guild_and_verification_contract_with_real_models(cache):
    """Validates structural contracts for Guild configurations and Verification pipeline assets."""
    guild_id = 555666777
    guild_payload = {
        "_id": guild_id,
        "prefix": "!",
        "premium": True,
    }
    real_guild = GuildData.from_dict(guild_payload)

    await cache.add_guild_data(real_guild)
    assert await cache.get_guild_data(guild_id) == real_guild
    await cache.remove_guild_data(guild_id)

    # Verification Code Verification
    user_id = 999111
    verify_payload = {
        "user_id": user_id,
        "code": "XYZ-789",
        "timestamp": 1627512000,
    }
    real_verify = VerificationCodeInfo.from_dict(verify_payload)

    await cache.set_verification_code_info(real_verify)
    assert await cache.get_verification_code_info(user_id) == real_verify
    await cache.del_verification_code_info(user_id)


# ==============================================================================
# 7. MULTI-TENANT & CLEAR EXECUTION SCOPES
# ==============================================================================

@pytest.mark.asyncio
async def test_scoped_deletion_and_clear_contracts_with_real_models(cache):
    """Validates that multi-tenant scopes function cleanly on actual domain models."""
    guild_id = 888222
    problem_data = {
        "guild_id": guild_id,
        "description": "Calculus problem",
        "answer": "0",
    }
    real_problem = BaseProblem.from_dict(problem_data)

    await cache.add_problem(problem_id=99, problem=real_problem)
    assert await cache.num_guild_problems(guild_id) == 1

    # Contract: delete_all_by_guild_id drops exactly the isolated tenant group scope
    await cache.delete_all_by_guild_id(guild_id)
    assert await cache.num_guild_problems(guild_id) == 0

    # Contract: clear(force=True) sweeps all storage items
    user = UserData.default(user_id=777)
    await cache.add_thing(user)

    await cache.clear(force=True)
    assert len(await cache.get_all_things()) == 0


def test_is_locked_boolean_contract(cache):
    """Ensures property definitions evaluate precisely to a valid boolean type match."""
    assert isinstance(cache.is_locked, bool)


# ==============================================================================
# Pytest Fixture
# ==============================================================================

@pytest.fixture
def base_cache():
    """
    Instantiates AbstractCache directly by removing abstract methods checks
    and patching out File I/O dependencies during initialization.
    """
    with patch.multiple(AbstractCache, __abstractmethods__=set()), \
            patch("..FileDictionaryReader.AsyncFileDict") as mock_file_dict:
        cache_instance = AbstractCache()
        # Initialize standard properties
        cache_instance._async_file_dict = MagicMock()
        cache_instance._async_file_dict.read_from_file = AsyncMock()
        cache_instance._async_file_dict.dict = {"permissions_required": {}}

        yield cache_instance


# ==============================================================================
# 1. Tests for fallback core methods & loops (has_thing, add_things)
# ==============================================================================

@pytest.mark.asyncio
async def test_has_thing_returns_true_when_found(base_cache):
    """has_thing should return True if get_thing retrieves an object without exception."""
    base_cache.get_thing = AsyncMock(return_value=MagicMock())

    with pytest.warns(UserWarning, match="This is a slow method"):
        result = await base_cache.has_thing("some_key")

    assert result is True
    base_cache.get_thing.assert_called_once_with("some_key", default=None)


@pytest.mark.asyncio
async def test_has_thing_returns_false_on_not_found(base_cache):
    """has_thing should return False if get_thing raises a ThingNotFound exception."""
    base_cache.get_thing = AsyncMock(side_effect=ThingNotFound)

    with pytest.warns(UserWarning, match="This is a slow method"):
        result = await base_cache.has_thing("missing_key")

    assert result is False


@pytest.mark.asyncio
async def test_add_things_warns_and_loops_over_add_thing(base_cache):
    """add_things must issue a RuntimeWarning and sequentially call add_thing for each object."""
    mock_things = [MagicMock(), MagicMock(), MagicMock()]
    base_cache.add_thing = AsyncMock()

    with pytest.warns(RuntimeWarning, match="This method is slow"):
        await base_cache.add_things(mock_things)

    assert base_cache.add_thing.call_count == 3


# ==============================================================================
# 2. Tests for Filter & Lookup Helpers
# ==============================================================================

@pytest.mark.asyncio
async def test_get_all_problems_by_guild(base_cache):
    """get_all_problems_by_guild should return items filtered by the target guild_id."""
    prob_match = MagicMock(spec=BaseProblem, guild_id=123)
    prob_unmatch = MagicMock(spec=BaseProblem, guild_id=456)

    base_cache.get_all_problems = AsyncMock(return_value=[prob_match, prob_unmatch])

    with pytest.warns(RuntimeWarning, match="This method is slow"):
        results = await base_cache.get_all_problems_by_guild(123)

    assert len(results) == 1
    assert results[0].guild_id == 123


@pytest.mark.asyncio
async def test_get_global_problems(base_cache):
    """get_global_problems should look specifically for items where guild_id is None."""
    prob_global = MagicMock(spec=BaseProblem, guild_id=None)
    prob_guild = MagicMock(spec=BaseProblem, guild_id=789)

    base_cache.get_all_problems = AsyncMock(return_value=[prob_global, prob_guild])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        results = await base_cache.get_global_problems()

    assert len(results) == 1
    assert results[0].guild_id is None


@pytest.mark.asyncio
async def test_get_all_problems_by_func(base_cache):
    """get_all_problems_by_func should correctly apply an arbitrary functional lambda filter."""
    prob_low_id = MagicMock(spec=BaseProblem)
    prob_low_id.id = 5
    prob_high_id = MagicMock(spec=BaseProblem)
    prob_high_id.id = 500

    base_cache.get_all_problems = AsyncMock(return_value=[prob_low_id, prob_high_id])

    results = await base_cache.get_all_problems_by_func(lambda p: p.id > 100)
    assert len(results) == 1
    assert results[0].id == 500


# ==============================================================================
# 3. Tests for Forwarding Aliases
# ==============================================================================

@pytest.mark.asyncio
async def test_update_problem_alias_calls_add_problem(base_cache):
    """update_problem should act as a pass-through wrapper for add_problem."""
    base_cache.add_problem = AsyncMock()
    mock_problem = MagicMock(spec=BaseProblem)

    await base_cache.update_problem(42, mock_problem)
    base_cache.add_problem.assert_called_once_with(42, mock_problem)


@pytest.mark.asyncio
async def test_set_appeal_alias_calls_add_appeal(base_cache):
    """set_appeal should act as a pass-through wrapper for add_appeal."""
    base_cache.add_appeal = AsyncMock()
    mock_appeal = MagicMock()

    await base_cache.set_appeal(mock_appeal)
    base_cache.add_appeal.assert_called_once_with(mock_appeal)


@pytest.mark.asyncio
async def test_del_guild_data_alias_calls_remove_guild_data(base_cache):
    """del_guild_data should act as a pass-through wrapper for remove_guild_data."""
    base_cache.remove_guild_data = AsyncMock()

    await base_cache.del_guild_data(101)
    base_cache.remove_guild_data.assert_called_once_with(101)


@pytest.mark.asyncio
async def test_delete_verification_code_info_alias_calls_del_verification_code_info(base_cache):
    """delete_verification_code_info should act as a wrapper for del_verification_code_info."""
    base_cache.del_verification_code_info = AsyncMock()

    await base_cache.delete_verification_code_info(999)
    base_cache.del_verification_code_info.assert_called_once_with(999)


# ==============================================================================
# 4. Tests for Permissions Matrix Verifications
# ==============================================================================

@pytest.mark.asyncio
async def test_get_permissions_required_for_command_throws_if_missing_file_dict(base_cache):
    """get_permissions_required_for_command throws NotImplementedError if file dictionary attribute is missing."""
    del base_cache._async_file_dict
    with pytest.raises(NotImplementedError, match="Subclasses must implement this method"):
        await base_cache.get_permissions_required_for_command("test")


@pytest.mark.asyncio
async def test_get_permissions_required_for_command(base_cache):
    """get_permissions_required_for_command reads file configuration and returns expected command structure."""
    base_cache._async_file_dict.dict = {"permissions_required": {"ban": {"admin": True}}}

    res = await base_cache.get_permissions_required_for_command("ban")
    base_cache._async_file_dict.read_from_file.assert_called_once()
    assert res == {"admin": True}


@pytest.mark.asyncio
async def test_user_meets_permissions_denied_by_trusted_flag(base_cache):
    """user_meets_permissions returns False if trusted requirement fails."""
    base_cache.get_permissions_required_for_command = AsyncMock(return_value={"trusted": True})

    mock_user = MagicMock(spec=UserData, trusted=False)
    with patch.object(UserData, "default", return_value=mock_user):
        base_cache.get_user_data = AsyncMock(return_value=mock_user)

        result = await base_cache.user_meets_permissions_required_to_use_command(user_id=1, command_name="cmd")
        assert result is False


@pytest.mark.asyncio
async def test_user_meets_permissions_denied_by_denylisted_flag(base_cache):
    """user_meets_permissions returns False if user matches a blocked denylist configuration rule."""
    base_cache.get_permissions_required_for_command = AsyncMock(return_value={"denylisted": False})

    mock_user = MagicMock(spec=UserData, denylisted=True)
    with patch.object(UserData, "default", return_value=mock_user):
        base_cache.get_user_data = AsyncMock(return_value=mock_user)

        result = await base_cache.user_meets_permissions_required_to_use_command(user_id=1, command_name="cmd")
        assert result is False


@pytest.mark.asyncio
async def test_user_meets_permissions_evaluation_pass(base_cache):
    """user_meets_permissions returns True if all operational criteria matches successfully."""
    base_cache.get_permissions_required_for_command = AsyncMock(return_value={"custom_flag": False})

    mock_user = MagicMock(spec=UserData)
    mock_user.custom_flag = True  # user.custom_flag (True) != required val (False) -> evaluates to True via all()
    base_cache.get_user_data = AsyncMock(return_value=mock_user)

    result = await base_cache.user_meets_permissions_required_to_use_command(user_id=1, command_name="cmd")
    assert result is True


# ==============================================================================
# 5. Tests for Deprecations & Hard Environment Barriers
# ==============================================================================

@pytest.mark.asyncio
async def test_update_cache_raises_not_implemented(base_cache):
    """update_cache must immediately trigger a baseline crash pathway for deprecation safety."""
    with pytest.raises(NotImplementedError, match="removed due to its expensiveness"):
        await base_cache.update_cache()


@pytest.mark.asyncio
async def test_bgsave_raises_must_implement_error(base_cache):
    """bgsave triggers MUST_IMPLEMENT_ERROR by default."""
    with pytest.raises(NotImplementedError) as exc_info:
        await base_cache.bgsave(schedule="hourly")
    assert exc_info.value is MUST_IMPLEMENT_ERROR


@pytest.mark.asyncio
async def test_run_sql_raises_must_implement_error(base_cache):
    """run_sql triggers MUST_IMPLEMENT_ERROR by default."""
    with pytest.raises(NotImplementedError) as exc_info:
        await base_cache.run_sql("SELECT 1")
    assert exc_info.value is MUST_IMPLEMENT_ERROR


@pytest.mark.asyncio
async def test_initialize_sql_table_raises_sql_not_supported(base_cache):
    """initialize_sql_table always throws SQLNotSupportedInRedisException."""
    with pytest.raises(SQLNotSupportedInRedisException, match="SQL is not supported in Redis"):
        await base_cache.initialize_sql_table()


# ==============================================================================
# 6. Tests for Static Environment Checks (is_production)
# ==============================================================================

def test_is_production_defaults_to_true_when_unset(monkeypatch):
    """is_production should fallback to True when APP_ENV is completely absent from variables."""
    monkeypatch.delenv("APP_ENV", raising=False)
    assert AbstractCache.is_production() is True


def test_is_production_evaluates_prod_keywords(monkeypatch):
    """is_production should identify production configurations with string substrings."""
    monkeypatch.setenv("APP_ENV", "production")
    assert AbstractCache.is_production() is True

    monkeypatch.setenv("APP_ENV", "PROD_SERVER")
    assert AbstractCache.is_production() is True


def test_is_production_returns_false_for_dev_and_local(monkeypatch):
    """is_production should return False for non-prod values like staging or development."""
    monkeypatch.setenv("APP_ENV", "development")
    assert AbstractCache.is_production() is False

    monkeypatch.setenv("APP_ENV", "staging")
    assert AbstractCache.is_production() is False