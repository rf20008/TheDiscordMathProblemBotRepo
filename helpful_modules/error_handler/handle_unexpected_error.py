"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - BaseOnError

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""

import asyncio
import datetime
import logging
import os
import subprocess
import traceback
from copy import deepcopy
from sys import exc_info, stderr
from time import asctime

import disnake
from disnake.ext import commands

from helpful_modules.paginator_view import PaginatorView

from .._error_logging import log_error
from ..cooldowns import OnCooldown
from ..custom_embeds import ErrorEmbed, SimpleEmbed, SuccessEmbed
from ..problems_module.errors import (
    LinearAlgebraUserInputErrorException,
    LockedCacheException,
)
from ..threads_or_useful_funcs import get_git_revision_hash


async def log_unexpected_error(error) -> str:
    try:
        await log_error(error)  # Log the error
        return ""
    except Exception as log_error_exc:
        return (
            """Additionally, while trying to log this error, the following exception occurred: \n"""
            + disnake.utils.escape_markdown(
                "\n".join(traceback.format_exception(log_error_exc))
            )
        )


def create_plain_text_for_error(
    error: BaseException,
    yet_other_exception: BaseException | None = None,
    error_msg: str = "",
    traceback_msg: str = "",
    additional_error: str = "",
) -> str:
    # send as plain text
    plain_text = (
        """Oh no! An Exception occurred! And it couldn't be sent as an embed!```"""
    )
    plain_text += error_msg + traceback_msg + additional_error
    plain_text += f"```Time: {str(asctime())} Commit hash: {get_git_revision_hash()} The stack trace is shown for debugging purposes. The stack trace is also logged (and pushed), but hopefully does not contain identifying information\n"
    plain_text += f"Error that occurred while attempting to send it as an embed:"
    plain_text += disnake.utils.escape_markdown("".join(traceback.format_exception(e)))[
        : -(1650 - len(plain_text))
    ]
    if yet_other_exception is not None:
        the_new_exception = deepcopy(yet_other_exception)
        the_new_exception.__cause__ = error
    if len(plain_text) > 2000:
        logging.warning(
            f"Plain text is too long. It could not be sent as an embed, and the plain text ({plain_text}) is too long"
        )
        # uh oh
        return plain_text[:2000]
    return plain_text


async def handle_unexpected_error(
    inter, error, should_log_error=True, print_error=True
):
    # Embed = ErrorEmbed(custom_title="⚠ Oh no! Error: " + str(type(error)), description=("Command raised an exception:" + str(error)))
    logging.error("Uh oh - an unexpected error occurred ", exc_info=exc_info())
    error_traceback = "\n".join(traceback.format_exception(error))
    if print_error:
        print(
            "\n".join(traceback.format_exception(error)),  # python 3.10 only!
            file=stderr,
        )

    error_msg = """An error occurred!

        Steps you should do:
        1) Please report this bug to me! (Either create a github issue, or report it in the support server)
        2) If you are a programmer, please suggest a fix by creating a Pull Request.
        3) Please don't use this command until it gets fixed in a later update!

        The error traceback is shown below; this may be removed/DMed to the user in the future.

        """  # TODO: update when my support server becomes public & think about providing the traceback to the user
    traceback_msg = disnake.utils.escape_markdown(error_traceback)
    additional_error = ""
    if should_log_error:
        additional_error = await log_unexpected_error(error)
    try:
        embed = ErrorEmbed(
            description=error_msg + traceback_msg + additional_error,
            title="Oh, no! An error occurred!",
        )
    except (TypeError, NameError) as e:
        return create_plain_text_for_error(
            error, e, error_msg, traceback_msg, additional_error
        )
    footer = f"Time: {str(asctime())} Commit hash: {get_git_revision_hash()} The stack trace is shown for debugging purposes. The stack trace is also logged (and pushed), but should not contain identifying information (only code which is on github)"
    embed.set_footer(text=footer)
    if len(embed.description) < 2048:
        return {"embed": embed}
    paginator = PaginatorView.paginate(
        user_id=inter.author.id,
        text=error_msg,
        breaking_chars="\n",
        max_page_length=1800,
        special_color=disnake.Color.red(),
    )
    paginator.add_pages(
        PaginatorView.break_into_pages(
            traceback_msg, max_page_length=1800, breaking_chars="\n"
        )
    )
    if additional_error:
        paginator.add_pages(
            PaginatorView.break_into_pages(
                additional_error, max_page_length=1800, breaking_chars="\n"
            )
        )
    accounted_for = len(error_msg) + len(traceback_msg) + len(additional_error)
    if len(embed.description) != accounted_for:
        paginator.add_pages(
            PaginatorView.break_into_pages(
                embed.description[accounted_for:],
                max_page_length=1800,
                breaking_chars="\n",
            )
        )
    first_page = paginator.create_embed()
    return {"embed": first_page, "view": paginator}
