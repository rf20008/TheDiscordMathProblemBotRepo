import logging
import random
import subprocess
import traceback
import datetime
import asyncio
import types
from copy import deepcopy
from functools import partial, wraps
from logging import handlers
from sys import exc_info, stderr
from time import asctime
from typing import Optional, Any

import disnake
from disnake.ext import commands

from ._error_logging import log_error
from .cooldowns import OnCooldown
from .custom_embeds import *
from .the_documentation_file_loader import DocumentationFileLoader

# Licensed under GPLv3

log = logging.getLogger(__name__)

TYPE_CLASS = type(int)  # the class 'type'


def generate_new_id():
    """Generate a random number from 0 to 2**53-1"""
    return random.randint(0, 2**53 - 1)


def get_git_revision_hash() -> str:
    """A method that gets the git revision hash. Credit to https://stackoverflow.com/a/21901260 for the code :-)"""
    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"])
        .decode("ascii")
        .strip()[:7]
    )  # [7:] is here because of the commit hash, the rest of this function is from stack overflow


def async_wrap(func):
    """Turn a sync function into an asynchronous function
    Source: https://dev.to/0xbf/turn-sync-function-to-async-python-tips-58nn
    """

    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


def modified_async_wrap(func):
    assert isinstance(func, types.FunctionType)
    if asyncio.iscoroutinefunction(func):
        return func
    return async_wrap(func)


def loading_documentation_thread():
    """This thread reloads the documentation."""
    d = DocumentationFileLoader()
    d.load_documentation_into_readable_files()
    del d


async def base_on_error(
    inter: disnake.ApplicationCommandInteraction, error: BaseException | Exception
):
    """The base on_error event. Call this and use the dictionary as keyword arguments to print to the user"""
    error_traceback = "\n".join(traceback.format_exception(error))
    if isinstance(error, BaseException) and not isinstance(error, Exception):
        # Errors that do not inherit from Exception are not meant to be caught
        await inter.bot.close()
        raise
    if isinstance(error, (OnCooldown, disnake.ext.commands.CommandOnCooldown)):
        # This is a cooldown exception
        content = f"This command is on cooldown; please retry **{disnake.utils.format_dt(disnake.utils.utcnow() + datetime.timedelta(seconds=error.retry_after), style='R')}**."
        return {"content": content, "delete_after": error.retry_after}
    if isinstance(error, (disnake.Forbidden,)):
        extra_content = """There was a 403 error. This means either
        1) You didn't give me enough permissions to function correctly, or
        2) There's a bug! If so, please report it!
        
        The error traceback is below."""
        return {"content": extra_content + error_traceback}

    if isinstance(error, commands.NotOwner):
        return {"embed": ErrorEmbed("You are not the owner of this bot.")}
    if isinstance(error, disnake.ext.commands.errors.CheckFailure):
        return {"embed": ErrorEmbed(str(error))}
    # Embed = ErrorEmbed(custom_title="⚠ Oh no! Error: " + str(type(error)), description=("Command raised an exception:" + str(error)))
    logging.error("Uh oh - an error occurred ", exc_info=exc_info())
    print(
        "\n".join(traceback.format_exception(error)),  # python 3.10 only!
        file=stderr,
    )
    await log_error(error)  # Log the error
    error_msg = """An error occurred!
    
    Steps you should do:
    1) Please report this bug to me! (Either create a github issue, or report it in the support server)
    2) If you are a programmer, please suggest a fix by creating a Pull Request.
    3) Please don't use this command until it gets fixed in a later update!
    
    The error traceback is shown below; this may be removed/DMed to the user in the future.
    
    """ + disnake.utils.escape_markdown(
        error_traceback
    )  # TODO: update when my support server becomes public & think about providing the traceback to the user
    try:
        embed = disnake.Embed(
            colour=disnake.Colour.red(),
            description=error_msg,
            title="Oh, no! An error occurred!",
        )
    except (TypeError, NameError) as e:
        # send as plain text
        plain_text = (
            """Oh no! An Exception occurred! And it couldn't be sent as an embed!```"""
        )
        plain_text += error_traceback
        plain_text += f"```Time: {str(asctime())} Commit hash: {get_git_revision_hash()} The stack trace is shown for debugging purposes. The stack trace is also logged (and pushed), but should not contain identifying information (only code which is on github)"

        plain_text += f"Error that occurred while attempting to send it as an embed:"
        plain_text += disnake.utils.escape_markdown(
            "".join(traceback.format_exception(e))
        )[: -(1650 - len(plain_text))]
        the_new_exception = deepcopy(e)
        the_new_exception.__cause__ = error
        if len(plain_text) > 2000:
            # uh oh
            raise RuntimeError(
                "An error occurred; could not send it as an embed nor as plain text!"
            ) from the_new_exception

        return {"content": plain_text}
    footer = f"Time: {str(asctime())} Commit hash: {get_git_revision_hash()} The stack trace is shown for debugging purposes. The stack trace is also logged (and pushed), but should not contain identifying information (only code which is on github)"
    embed.set_footer(text=footer)
    return {"embed": embed}


def get_log(name: Optional[str]) -> logging.Logger:
    _log = logging.getLogger(name)
    TRFH = handlers.TimedRotatingFileHandler(
        filename="logs/bot.log", when="midnight", encoding="utf-8", backupCount=300
    )
    _log.addHandler(TRFH)
    return _log


def _generate_special_id(guild_id, quiz_id, user_id, attempt_num):
    return str(
        {
            "quiz_id": quiz_id,
            "guild_id": guild_id,
            "user_id": user_id,
            "attempt_num": attempt_num,
        }
    )


def assert_type_or_throw_exception(
    thing: Any,
    err_type: TYPE_CLASS,
    msg: str = "Wrong type provided!",
    exc_type: Exception = TypeError,
):
    """
    Assert that `thing` is of type `type` or throw an exception.
    Parameters
    ---------
    thing : Any
        The thing to test
    type: `py:class:type`
        A thing to test the type against
    msg: str
        The message of the error that will be raised if the thing is not of type
    exc_type: BaseException
        The exception type thrown. Defaults to `py:class:TypeError`.
    """
    if not isinstance(thing, err_type):
        raise exc_type(msg)
    return


def extended_gcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        gcd, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return (gcd, x, y)


def miller_rabin(n, k=100):
    if not isinstance(n, int) or n < 2:
        raise ValueError("no; n is not an int or n<2")
    if n % 2 == 0:
        return n == 2
    s = 0
    d = n - 1
    while d & 1 == 0:
        d = d >> 1
        s += 1
    for _ in range(k):
        a = random.randint(2, n - 2)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        y = x
        for j in range(s):
            y = (x * x) % n
            if y == 1:
                return False  # n is composite, we have a witness
            if y == n - 1:
                break
            x = y
        if y != 1:
            return False
    return True
