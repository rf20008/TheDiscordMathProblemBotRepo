import asyncio
from helpful_modules import threads_or_useful_funcs
import disnake
import disnake.ext
import unittest
import unittest.mock
import datetime


class TestGenerateId(unittest.TestCase):
    def test_id_range(self):
        for i in range(500):
            self.assertIn(threads_or_useful_funcs.generate_new_id(), range(2**53))

    def test_id_type(self):
        self.assertIsInstance(threads_or_useful_funcs.generate_new_id(), int)


class TestGitCommitHash(unittest.TestCase):
    """This is a test class testing the GitCommitHash
    It's from ChatGPT!"""

    @unittest.mock.patch("subprocess.check_output")
    def test_get_git_commit_hash(self, mock_check_output):
        # Set the return value of subprocess.check_output
        mock_check_output.return_value = b"abcdef123456\n"

        # Now call your function
        result = threads_or_useful_funcs.get_git_revision_hash()

        # Check that subprocess.check_output was called with the correct arguments
        mock_check_output.assert_called_once_with(
            ["git", "rev-parse", "HEAD"], encoding="ascii", errors="ignore"
        )

        # Check the result
        self.assertEqual(result, "abcdef123456")


class TestWraps(unittest.IsolatedAsyncioTestCase):
    async def test_async_wrap(self):
        def f(x):
            return x * x + 3 * x + 2

        wrapped_f = threads_or_useful_funcs.async_wrap(f)
        self.assertEqual(f(0), await wrapped_f(0))
        self.assertEqual(f(3), await wrapped_f(3))
        self.assertEqual(f(100), await wrapped_f(100))
        self.assertNotEqual(f(0), await wrapped_f(30333))

    async def test_async_wrap_with_executor(self):
        # NOTE: THIS CAME FROM CHATGPT
        # Define a synchronous function
        def sync_function():
            return "Hello, World!"

        # Wrap the synchronous function with async_wrap, providing an executor
        async_wrapped_function = threads_or_useful_funcs.async_wrap(sync_function)

        # Mock an executor
        executor_mock = unittest.mock.Mock()

        # Call the wrapped function with the executor within an async context
        await async_wrapped_function(executor=executor_mock)

        # Assert that the executor's run_in_executor method was called
        executor_mock.run_in_executor.assert_called_once()


# TODO: tests for base_on_error
class TestBaseOnError(unittest.IsolatedAsyncioTestCase):
    async def setUp(self):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot

    async def test_pass_on_non_exceptions(self):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        with self.assertRaises(KeyboardInterrupt):
            await threads_or_useful_funcs.base_on_error(inter, error=KeyboardInterrupt)
            inter.bot.close.assert_awaited()

    # TODO: finish
    # TODO: there are so many more tests, that need to be made :)
    @unittest.mock.patch("disnake.utils.utcnow")
    async def test_cooldown_errors(self, mock_utcnow):
        mock_utcnow.return_value = datetime.datetime(
            year=2000, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        result = await threads_or_useful_funcs.base_on_error(
            inter, error=disnake.ext.commands.CommandOnCooldown(retry_after=3.0)
        )
        inter.send.assert_not_awaited()
        # content = f"This command is on cooldown; please retry **{disnake.utils.format_dt(disnake.utils.utcnow() + datetime.timedelta(seconds=error.retry_after), style='R')}**."
        # return {"content": content, "delete_after": error.retry_after}
        self.assertEqual(
            result,
            {
                "content": f"This command is on cooldown; please retry **'<t:946702803:R>'**.",
                "delete_after": 3.0,
            },
        )
        # return {"content": content, "delete_after": error.retry_after}, "delete_after": 3.0})
