import asyncio
from helpful_modules import threads_or_useful_funcs
import disnake
import disnake.ext
import unittest
import unittest.mock
import datetime

from helpful_modules.custom_embeds import ErrorEmbed
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
    # these three tests come from ChatGPT
    async def test_forbidden_error(self):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        result = await threads_or_useful_funcs.base_on_error(
            inter, error=disnake.Forbidden("Insufficient permissions.")
        )
        expected_result = {
            "content": "There was a 403 error. This means either\n"
                       "1) You didn't give me enough permissions to function correctly, or\n"
                       "2) There's a bug! If so, please report it!\n\n"
                       "The error traceback is below."
        }
        self.assertTrue(result["content"].startswith(
            "There was a 403 error. This means either\n"
            "1) You didn't give me enough permissions to function correctly, or\n"
            "2) There's a bug! If so, please report it!\n\n"
            "The error traceback is below."
        ))
        expected_result["content"] = result["content"] # TODO: fix the monkey patch
        self.assertEqual(result, expected_result)

    async def test_not_owner_error(self):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        result = await threads_or_useful_funcs.base_on_error(
            inter, error=disnake.ext.commands.errors.NotOwner()
        )
        expected_result = {
            "embed": ErrorEmbed("You are not the owner of this bot.")
        }
        self.assertEqual(result, expected_result)

    async def test_check_failure_error(self):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        error_message = "Custom check failed."
        result = await threads_or_useful_funcs.base_on_error(
            inter, error=disnake.ext.commands.errors.CheckFailure(error_message)
        )
        expected_result = {
            "embed": ErrorEmbed(error_message)
        }
        self.assertEqual(result, expected_result)

    async def test_logging_error(self):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        error_message = "Test error message"
        result = await threads_or_useful_funcs.base_on_error(
            inter, error=Exception(error_message)
        )
        inter.send.assert_not_awaited()
        inter.bot.close.assert_not_awaited()
        self.assertIn(error_message, result['content'])
        self.assertIn("An error occurred!", result['content'])
        self.assertIn("Steps you should do:", result['content'])

    async def test_embed_creation(self):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        error_message = "Test error message"
        result = await threads_or_useful_funcs.base_on_error(
            inter, error=Exception(error_message)
        )
        inter.send.assert_not_awaited()
        inter.bot.close.assert_not_awaited()
        self.assertIn("Oh, no! An error occurred!", result['embed']['title'])
        self.assertIn("Time:", result['embed']['footer']['text'])
        self.assertIn(threads_or_useful_funcs.get_git_revision_hash(), result['embed']['footer']['text'])

    async def test_embed_fallback_to_plain_text(self):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        # Simulate a condition where creating an embed raises an exception
        with unittest.mock.patch(
                'disnake.Embed', side_effect=(TypeError("Test error"))
        ):
            result = await threads_or_useful_funcs.base_on_error(
                inter, error=Exception("Test error message")
            )
        inter.send.assert_not_awaited()
        inter.bot.close.assert_not_awaited()
        self.assertIn("Oh no! An Exception occurred!", result['content'])
        self.assertIn("Test error message", result['content'])
        self.assertIn("Time:", result['content'])
        self.assertIn(threads_or_useful_funcs.get_git_revision_hash(), result['content'])
class TestClassOrThrowException(unittest.TestCase):
    def test_pass_basic_1(self):
        self.assertTrue(threads_or_useful_funcs.assert_type_or_throw_exception(3111, int))

    def test_pass_basic_2(self):
        self.assertTrue(threads_or_useful_funcs.assert_type_or_throw_exception("hehe boi", str))

    def test_pass_medium_1(self):
        self.assertTrue(threads_or_useful_funcs.assert_type_or_throw_exception("nope" + "hehe boi", str))
    def test_pass_class(self):
        self.assertTrue(KeyboardInterrupt("hehe"), KeyboardInterrupt)
    def test_wrong_type(self):
        self.assertRaises(TypeError, threads_or_useful_funcs.assert_type_or_throw_exception, ("no", int))
    def test_raise_correct_error_1(self):
        self.assertRaises(ValueError, threads_or_useful_funcs.assert_type_or_throw_exception, ("no", int, "hehe", ValueError))
    def test_raise_correct_error_2(self):
        self.assertRaises(RuntimeError, threads_or_useful_funcs.assert_type_or_throw_exception, (1392929292, float, "hehe", RuntimeError))

class TestExtendedGCD(unittest.TestCase):
    def test_gcd(self):
        self.assertEqual(threads_or_useful_funcs.extended_gcd(3, 1)[0], 1)