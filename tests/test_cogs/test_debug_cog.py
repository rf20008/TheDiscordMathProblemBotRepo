import asyncio
import datetime
import io
import math
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import disnake
from disnake.ext import commands

# Adjust this import to match your project's directory structure
from cogs.debug_cog import DebugCog


@pytest.fixture
def mock_bot():
    """Fixture to generate a mocked instance of TheDiscordMathProblemBot."""
    bot = MagicMock()
    bot.is_owner = AsyncMock(return_value=True)
    bot.is_trusted = AsyncMock(return_value=True)
    bot.is_user_denylisted = AsyncMock(return_value=False)
    bot.restart = AsyncMock()
    bot.close = AsyncMock()
    bot.wait_for = AsyncMock()

    # Mocking cache behavior
    bot.cache = MagicMock()
    bot.cache.run_sql = AsyncMock(return_value="SQL Result Data")
    return bot


@pytest.fixture
def mock_inter():
    """Fixture to generate a mocked Disnake application command interaction."""
    inter = MagicMock(spec=disnake.ApplicationCommandInteraction)
    inter.author = MagicMock()
    inter.author.id = 123456789
    inter.send = AsyncMock()
    inter.response = MagicMock()
    inter.response.defer = AsyncMock()
    inter.response.send_modal = AsyncMock()
    return inter


@pytest.fixture
def cog(mock_bot):
    """Fixture initializing the DebugCog with the mocked bot."""
    return DebugCog(mock_bot)


# ==============================================================================
# 1. Tests for cog_slash_command_check
# ==============================================================================


@pytest.mark.asyncio
async def test_cog_slash_command_check_success(cog, mock_inter):
    """Should return True if the author is the bot owner."""
    cog.bot.is_owner.return_value = True
    result = await cog.cog_slash_command_check(mock_inter)
    assert result is True


@pytest.mark.asyncio
async def test_cog_slash_command_check_failure(cog, mock_inter):
    """Should raise CheckFailure if the author is not the bot owner."""
    cog.bot.is_owner.return_value = False
    with pytest.raises(
        commands.CheckFailure, match="You are not the owner of this bot!"
    ):
        await cog.cog_slash_command_check(mock_inter)


# ==============================================================================
# 2. Tests for eval_code (Internal Execution Logic)
# ==============================================================================


@pytest.mark.asyncio
@patch("your_bot_folder.debug_cog.log_evaled_code", new_callable=AsyncMock)
async def test_eval_code_successful_execution(mock_log, cog, mock_inter):
    """Verifies that running valid arbitrary python code returns a SuccessEmbed."""
    code = "print('Hello World!')"

    with patch("your_bot_folder.debug_cog.SuccessEmbed") as mock_success_embed:
        await cog.eval_code(mock_inter, code, ephemeral=False)

        mock_log.assert_called_once()
        mock_inter.send.assert_called_once()
        # Verify code stdout parsing caught 'Hello World!'
        args, kwargs = mock_inter.send.call_args
        assert (
            "Hello World!" in args[0]
            or "Hello World!" in mock_success_embed.call_args[0][0]
        )


@pytest.mark.asyncio
@patch("your_bot_folder.debug_cog.log_evaled_code", new_callable=AsyncMock)
@patch("your_bot_folder.debug_cog.PaginatorView")
async def test_eval_code_paginator_trigger(mock_paginator, mock_log, cog, mock_inter):
    """Verifies that output too large for regular embeds triggers the custom PaginatorView."""
    # Generating an output greater than 4096 characters
    large_code = "print('A' * 5000)"

    mock_paginator_instance = MagicMock()
    mock_paginator_instance.create_embed = MagicMock(return_value="MockedEmbed")
    mock_paginator.break_into_pages.return_value = ["Page1", "Page2"]
    mock_paginator.return_value = mock_paginator_instance

    await cog.eval_code(mock_inter, large_code, ephemeral=False)

    mock_inter.response.defer.assert_called_once()
    mock_inter.send.assert_called_once_with(
        view=mock_paginator_instance, embed="MockedEmbed"
    )


# ==============================================================================
# 3. Tests for /sql Command
# ==============================================================================


@pytest.mark.asyncio
async def test_sql_command_success_short_output(cog, mock_inter):
    """Should output directly via message if the data return layout is small."""
    cog.bot.cache.run_sql.return_value = "Short Data Output"

    await cog.sql(mock_inter, query="SELECT * FROM users;", ephemeral=False)
    mock_inter.send.assert_called_once_with(
        "Result: Short Data Output", ephemeral=False
    )


@pytest.mark.asyncio
@patch("your_bot_folder.debug_cog.file_version_of_item")
async def test_sql_command_success_long_output(mock_file_version, cog, mock_inter):
    """Should upload output as an attached file wrapper if the data return layout is too long."""
    long_result = "X" * 2000
    cog.bot.cache.run_sql.return_value = long_result
    mock_file_version.return_value = "MockedFilePointer"

    await cog.sql(mock_inter, query="SELECT * FROM heavy_table;", ephemeral=True)

    mock_inter.send.assert_called_once_with(
        "The result is in the attached file!", ephemeral=True, file="MockedFilePointer"
    )


# ==============================================================================
# 4. Tests for /redis Command
# ==============================================================================


@pytest.mark.asyncio
async def test_redis_non_redis_cache(cog, mock_inter):
    """Should return an ErrorEmbed if the bot's runtime cache configuration is not a RedisCache."""
    cog.bot.cache = MagicMock()  # Generic mock object, not an instance of RedisCache

    with patch("your_bot_folder.debug_cog.ErrorEmbed") as mock_error_embed:
        await cog.redis(mock_inter, key="test_key")
        mock_inter.send.assert_called_once()


@pytest.mark.asyncio
async def test_redis_not_implemented(cog, mock_inter):
    """Should raise NotImplementedError if the check-path routes successfully into Redis handling."""
    from helpful_modules.problems_module.cache_rewrite_with_redis import RedisCache

    # Force mock object identification as a RedisCache subclass representation
    mock_redis = MagicMock(spec=RedisCache)
    cog.bot.cache = mock_redis

    with pytest.raises(NotImplementedError, match="This isn't implemented yet"):
        await cog.redis(mock_inter, key="test_key")


# ==============================================================================
# 5. Tests for /stop Command
# ==============================================================================


@pytest.mark.asyncio
async def test_stop_command_immediate(cog, mock_inter):
    """Verifies immediate graceful closing sequence execution when no delay argument exists."""
    with pytest.raises(SystemExit):
        await cog.stop(mock_inter, delay=0.0)

    mock_inter.send.assert_called_with("The bot is now stopping!")
    cog.bot.close.assert_called_once()


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_stop_command_delayed(mock_sleep, cog, mock_inter):
    """Verifies that a scheduled delayed shutdown calls asyncio.sleep properly."""
    with pytest.raises(SystemExit):
        await cog.stop(mock_inter, delay=10.0)

    mock_sleep.assert_called_once_with(10.0)
    cog.bot.close.assert_called_once()


@pytest.mark.asyncio
async def test_stop_command_invalid_input(cog, mock_inter):
    """Should flag bad constraints like NaN delay values instantly with a RuntimeError."""
    with pytest.raises(RuntimeError, match="Negative or NaN delay encountered"):
        await cog.stop(mock_inter, delay=float("nan"))
