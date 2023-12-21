import asyncio
import datetime
import logging
import math
import random
import unittest
import unittest.mock
from unittest.mock import MagicMock, Mock, AsyncMock, mock_open, patch

import aiofiles
import aiohttp.web_response
import disnake
import disnake.ext
from helpful_modules import threads_or_useful_funcs
from helpful_modules.custom_embeds import ErrorEmbed

#import pyfakefs.fake_filesystem_unittest

def generate_many_randoms(many=1, lows=(), highs=()):
    if len(highs) != len(lows) or len(lows) != many:
        raise ValueError("the arrays given do not match")
    return (random.randint(lows[i], highs[i]) for i in range(many))


def check_embed_equality(expected, result):
    if not isinstance(result, disnake.Embed):
        raise TypeError("the result is not an Embed")
    if not isinstance(expected, disnake.Embed):
        raise TypeError("expected isn't an embed either")
    for slot in expected.__slots__:
        if slot == "colour":
            slot = "color"
        if getattr(expected, slot, None) != getattr(result, slot, None):
            raise ValueError(
                f"""The embeds don't match 
    (slot {slot}) is not the same
    expected's value is "{getattr(expected, slot, None)}"
    but actual's value is "{getattr(result, slot, None)}" """
            )


class TestGenerateManyRandoms(unittest.TestCase):
    def test_valid_input(self):
        # Test with valid inputs
        lows = [1, 10, 5]
        highs = [10, 20, 15]
        many = len(lows)
        result = list(generate_many_randoms(many, lows, highs))

        # Check that the length of the result matches the expected length
        self.assertEqual(len(result), many)

        # Check that each generated random number is within the specified range
        for i in range(many):
            self.assertGreaterEqual(result[i], lows[i])
            self.assertLessEqual(result[i], highs[i])

    def test_invalid_input_lengths(self):
        # Test with invalid input lengths
        lows = [1, 10, 5]
        highs = [10, 20]
        many = len(lows)

        # Check that ValueError is raised for mismatched array lengths
        with self.assertRaises(ValueError):
            generate_many_randoms(many, lows, highs)

    def test_empty_input(self):
        # Test with empty input arrays
        many = 0
        result = list(generate_many_randoms(many, [], []))

        # Check that the result is an empty list
        self.assertEqual(result, [])


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
        self.assertIn(result, ["abcdef1", b"abcdef1"])


class TestWraps(unittest.IsolatedAsyncioTestCase):
    async def test_async_wrap(self):
        def f(x):
            return x * x + 3 * x + 2

        wrapped_f = threads_or_useful_funcs.async_wrap(f)
        self.assertEqual(
            f(0),
            await wrapped_f(0),
            "f and wrapped_f are not functionally equivalent, as f(0) != wrapped_f(0)",
        )
        self.assertEqual(
            f(3),
            await wrapped_f(3),
            "f and wrapped_f are not functionally equivalent, as f(3) != wrapped_f(3)",
        )
        self.assertEqual(
            f(100),
            await wrapped_f(100),
            "f and wrapped_f are not functionally equivalent, as f(100) != wrapped_f(100)",
        )
        self.assertNotEqual(
            f(0), await wrapped_f(30333), "They are equal for some function!"
        )

    async def test_async_wrap_with_executor(self):
        # NOTE: THIS CAME FROM CHATGPT
        # Define a synchronous function
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        def sync_function():
            return "Hello, World!"

        # Wrap the synchronous function with async_wrap, providing an executor
        async_wrapped_function = threads_or_useful_funcs.async_wrap(sync_function)

        # Mock an executor
        executor_mock = unittest.mock.AsyncMock(spec=type(loop))
        # Make run_in_executor an AsyncMock so it can be awaited. Otherwise, this test will fail
        executor_mock.run_in_executor = AsyncMock()  #
        # Call the wrapped function with the executor within an async context
        await async_wrapped_function(loop=executor_mock)

        # Assert that the executor's run_in_executor method was called
        executor_mock.run_in_executor.assert_called_once()


# TODO: all my tests are failing because the _error_log is not working, so patch them
class TestBaseOnError(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot

    async def test_pass_on_non_exceptions(self):
        # TODO: investigate the cause
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        with self.assertRaises(KeyboardInterrupt):
            await threads_or_useful_funcs.base_on_error(
                inter, error=KeyboardInterrupt("Keyboard Interrupt")
            )
            inter.bot.close.assert_awaited()

    # TODO: finish
    # TODO: there are so many more tests, that need to be made :)
    @unittest.mock.patch("disnake.utils.utcnow")
    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_cooldown_errors(self, mock_utcnow, mock_log):
        mock_utcnow.return_value = datetime.datetime(
            year=1970,
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=1,
            microsecond=0,
            tzinfo=datetime.timezone(offset=datetime.timedelta(hours=0)),
        )
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        result = await threads_or_useful_funcs.base_on_error(
            inter,
            error=disnake.ext.commands.CommandOnCooldown(
                retry_after=3.0,
                cooldown=disnake.ext.commands.Cooldown(rate=3, per=1),
                type=disnake.ext.commands.BucketType.default,
            ),
        )
        inter.send.assert_not_awaited()
        # content = f"This command is on cooldown; please retry **{disnake.utils.format_dt(disnake.utils.utcnow() + datetime.timedelta(seconds=error.retry_after), style='R')}**."
        # return {"content": content, "delete_after": error.retry_after}
        self.assertEqual(
            result["content"], f"This command is on cooldown; please retry **<t:1:R>**."
        )
        self.assertEqual(result["delete_after"], 3.0, "Delete afters do not match")
        self.assertEqual(set(result.keys()), {"content", "delete_after"})
        mock_log.assert_called_once()
        # return {"content": content, "delete_after": error.retry_after}, "delete_after": 3.0})

    # these three tests come from ChatGPT
    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_forbidden_error(self, mock_log):
        FORB_RESPONSE = """There was a 403 error. This means either
1) You didn't give me enough permissions to function correctly, or
2) There's a bug! If so, please report it!
The error traceback is below."""
        lines = FORB_RESPONSE.split("\n")
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        result = await threads_or_useful_funcs.base_on_error(
            inter,
            error=disnake.Forbidden(
                message="Insufficient permissions.",
                response=aiohttp.web_response.Response,
            ),
        )
        expected_result = {
            "content": "There was a 403 error. This means either\n"
            "1) You didn't give me enough permissions to function correctly, or\n"
            "2) There's a bug! If so, please report it!\n\n"
            "The error traceback is below."
        }
        for line in lines:
            self.assertIn(
                line,
                result["content"][: len(FORB_RESPONSE) + 55],
                "One of the lines isn' in the beginning of the FORB response",
            )
        expected_result["content"] = result["content"]  # TODO: fix the monkey patch
        self.assertEqual(result, expected_result, "Results do not match")
        mock_log.assert_not_called()

    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_not_owner_error(self, mock_log):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        result = await threads_or_useful_funcs.base_on_error(
            inter, error=disnake.ext.commands.errors.NotOwner()
        )
        expected_result = {"embed": ErrorEmbed("You are not the owner of this bot.")}
        check_embed_equality(expected_result["embed"], result["embed"])
        self.assertEqual(result, expected_result, "Results do not match")
        mock_log.assert_not_called()

    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_check_failure_error(self, mock_log):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        error_message = "Custom check failed."
        result = await threads_or_useful_funcs.base_on_error(
            inter, error=disnake.ext.commands.errors.CheckFailure(error_message)
        )
        expected_result = {"embed": ErrorEmbed(error_message)}
        check_embed_equality(expected_result["embed"], result["embed"])
        # self.assertTrue(expected_result == result, f"The embeds do not match: expected = {repr(expected_result['embed'])} but actual is {repr(result['embed'].__dict__)}")

    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_logging_error(self, mock_log_error):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        error_message = "Test error message"
        mock_log_error.side_effect = RuntimeError("HAHAHAHA!")
        result = await threads_or_useful_funcs.base_on_error(
            inter, error=Exception(error_message)
        )
        inter.send.assert_not_awaited()
        inter.bot.close.assert_not_awaited()
        self.assertIsInstance(result, dict)
        stuff = result["embed"].description

        self.assertIn(error_message, stuff)
        self.assertIn("An error occurred!", stuff)
        self.assertIn("Steps you should do:", stuff)
        self.assertIn(
            "Additionally, while trying to log this error, the following exception occurred: \n",
            stuff,
        )

    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_embed_creation(self, mock_log):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        error_message = "Test error message"
        result = await threads_or_useful_funcs.base_on_error(
            inter, error=Exception(error_message)
        )
        self.assertIsInstance(result, dict)
        inter.send.assert_not_awaited()
        inter.bot.close.assert_not_awaited()
        self.assertIn("Oh, no! An error occurred!", result["embed"].title)
        self.assertIn("Time:", result["embed"].footer.text)
        self.assertIn(
            threads_or_useful_funcs.get_git_revision_hash(), result["embed"].footer.text
        )

    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_embed_fallback_to_plain_text(self, mock_log):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        # Simulate a condition where creating an embed raises an exception
        with unittest.mock.patch(
            "disnake.Embed", side_effect=(TypeError("Test error"))
        ):
            result = await threads_or_useful_funcs.base_on_error(
                inter, error=Exception("Test error message")
            )
        inter.send.assert_not_awaited()
        inter.bot.close.assert_not_awaited()
        self.assertIn("Oh no! An Exception occurred!", result["content"])
        self.assertIn("Test error message", result["content"])
        self.assertIn("Time:", result["content"])
        self.assertIn(
            threads_or_useful_funcs.get_git_revision_hash(), result["content"]
        )


class TestClassOrThrowException(unittest.TestCase):
    def test_pass_basic_1(self):
        self.assertIsNone(
            threads_or_useful_funcs.assert_type_or_throw_exception(3111, int)
        )

    def test_pass_basic_2(self):
        self.assertIsNone(
            threads_or_useful_funcs.assert_type_or_throw_exception("hehe boi", str)
        )

    def test_pass_medium_1(self):
        self.assertIsNone(
            threads_or_useful_funcs.assert_type_or_throw_exception(
                "nope" + "hehe boi", str
            )
        )

    def test_pass_class(self):
        self.assertIsNone(
            threads_or_useful_funcs.assert_type_or_throw_exception(
                KeyboardInterrupt("hehe"), KeyboardInterrupt
            )
        )

    def test_wrong_type(self):
        self.assertRaises(
            TypeError,
            threads_or_useful_funcs.assert_type_or_throw_exception,
            ("no", int),
        )

    def test_raise_correct_error_1(self):
        self.assertRaises(
            ValueError,
            threads_or_useful_funcs.assert_type_or_throw_exception,
            *("no", int, "hehe", ValueError),
        )

    def test_raise_correct_error_2(self):
        self.assertRaises(
            RuntimeError,
            threads_or_useful_funcs.assert_type_or_throw_exception,
            1392929292,
            float,
            "hehe",
            RuntimeError,
        )


class TestExtendedGCD(unittest.TestCase):
    def test_gcd_basic(self):
        self.assertEqual(threads_or_useful_funcs.extended_gcd(3, 1)[0], 1)
        for i in range(300):
            x, y, d = generate_many_randoms(
                3, lows=[1, 1, 1], highs=[30000, 30000, 30000]
            )
            self.assertEqual(
                threads_or_useful_funcs.extended_gcd(x * d, y * d)[0],
                math.gcd(x * d, y * d),
            )

    def test_bezouts_condition(self):
        a, b = 3, 1
        g, x, y = threads_or_useful_funcs.extended_gcd(a, b)

        self.assertEqual(
            abs(x * a + y * b),
            1,
            f"Bezout's condition was not satisfied when a={a}, b={b}",
        )
        for i in range(300):
            a, b, d = generate_many_randoms(
                3, lows=[1, 1, 1], highs=[30000, 30000, 30000]
            )
            g, x, y = threads_or_useful_funcs.extended_gcd(a * d, b * d)
            real_gcd = math.gcd(a * d, b * d)
            self.assertEqual(
                g,
                real_gcd,
                f"Our program said gcd({a}, {b})={g} but in reality it is {real_gcd}",
            )
            self.assertEqual(
                x * a * d + y * b * d,
                g,
                f"Bezout's condition was not satisfied when a={a}, b={b}, d={d} (x={x}, y={y}, d={d}, xy+ab={x * a * d + y * b * d}, g={g}), real_gcd={real_gcd}",
            )


class TestMillerRabin(unittest.TestCase):
    def test_prime_small(self):
        failures = 0
        for _ in range(2000):
            if threads_or_useful_funcs.miller_rabin(100, 3):
                failures += 1
            if not threads_or_useful_funcs.miller_rabin(7, 3):
                failures += 1
        self.assertLess(failures / 1.15, 2000 / 64)

    def test_prime_big(self):
        M = 10**9 + 7
        self.assertFalse(threads_or_useful_funcs.miller_rabin(M * M, 300))
        self.assertTrue(threads_or_useful_funcs.miller_rabin(M, 300))
        self.assertTrue(threads_or_useful_funcs.miller_rabin(10**18 + 3, 300))
        self.assertFalse(threads_or_useful_funcs.miller_rabin(M * M - 1, 300))
        self.assertFalse(threads_or_useful_funcs.miller_rabin(M * M - 2, 300))

    def test_exceptions(self):
        self.assertRaises(
            ValueError, threads_or_useful_funcs.miller_rabin, "hehe boi", 30
        )
        self.assertRaises(ValueError, threads_or_useful_funcs.miller_rabin, 0, 15)


class TestEvalLogsAndLogs(unittest.IsolatedAsyncioTestCase):
    async def test_ensure_eval_logs_exist(self):
        # Test if the logs folder is created successfully
        with patch("builtins.print") as mock_print:
            threads_or_useful_funcs.ensure_eval_logs_exist()
            mock_print.assert_not_called()  # Ensure print is not called on success

        # Test if an exception is caught and a message is printed
        with patch("builtins.print") as mock_print:
            with patch("pathlib.Path.mkdir", side_effect=PermissionError):
                threads_or_useful_funcs.ensure_eval_logs_exist()
                mock_print.assert_any_call(
                    "I don't have permission to create an eval logs folder so logs may be missing!"
                )

    async def test_get_log(self):
        with open("logs/bot.log", "w") as f:
            f.write("hehe boi!!!")
        # Test if a logger is returned with the correct handler
        log = threads_or_useful_funcs.get_log("test_logger")
        handlers = log.handlers
        self.assertTrue(
            any(
                isinstance(handler, logging.handlers.TimedRotatingFileHandler)
                for handler in handlers
            )
        )

    async def test_log_evaled_code(self):
        # TODO: fix the mocking of aiofiles (the problem is __aenter__)
        # Mock async file writing
        mock_file = unittest.mock.MagicMock()
        mock_file.write = unittest.mock.MagicMock()

        def reset_mocks():
            nonlocal mock_file
            mock_file = unittest.mock.AsyncMock(
                spec=aiofiles.threadpool.text.AsyncTextIOWrapper
            )
            mock_file.write = unittest.mock.AsyncMock()

        code = "print('Hello, World!')"
        filepath = "eval_log/test_date"
        time_ran = datetime.datetime.now()
        async def mock_open2(*args, **kwargs):
            return mock_open(*args, **kwargs)
        mock_open2.__aenter__ = MagicMock(return_value=mock_file)
        mock_open2.__aexit__ = MagicMock()

        # Patch aiofiles.open to use the mock_open function
        with patch("aiofiles.open", new_callable=mock_open2):
            reset_mocks()
            # Test if the code is successfully written to the file
            with patch(
                "helpful_modules.threads_or_useful_funcs.humanify_date",
                return_value="test_date",
            ):
                await threads_or_useful_funcs.log_evaled_code(code, filepath, time_ran)
                mock_file.write.assert_awaited_with(f"\n{str(time_ran)}\n{code}\n")

            # Test if the default filepath is sed when not provided
            with patch(
                "helpful_modules.threads_or_useful_funcs.humanify_date",
                return_value="test_date",
            ):
                await threads_or_useful_funcs.log_evaled_code(code, time_ran=time_ran)
                mock_file.write.assert_awaited_with(f"\n{str(time_ran)}\n{code}\n")

            # Test if an exception is raised when writing to the file fails
            reset_mocks()

        with patch("aiofiles.open", side_effect=Exception("File write error")):
            with self.assertRaises(RuntimeError):
                await threads_or_useful_funcs.log_evaled_code(code, filepath, time_ran)


class TestHumanifyDate(unittest.TestCase):
    def test_humanify_date(self):
        # Test with a datetime object
        datetime_obj = datetime.datetime(2023, 1, 15)
        formatted_date = threads_or_useful_funcs.humanify_date(datetime_obj)
        expected_result = "2023 January 15"
        self.assertEqual(formatted_date, expected_result)

        # Test with a date object
        date_obj = datetime.date(2023, 1, 15)
        formatted_date = threads_or_useful_funcs.humanify_date(date_obj)
        expected_result = "2023 January 15"
        self.assertEqual(formatted_date, expected_result)


if __name__ == "__main__":
    unittest.main()
