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

from ._error_logging import log_error
from .cooldowns import OnCooldown
from .custom_embeds import ErrorEmbed, SimpleEmbed, SuccessEmbed
from .problems_module.errors import (
    LinearAlgebraUserInputErrorException,
    LockedCacheException,
)
from .error_handler.handle_known_errors import handle_known_error
from .error_handler.handle_unexpected_error import handle_unexpected_error
from .the_documentation_file_loader import DocumentationFileLoader


async def base_on_error(
    inter: disnake.ApplicationCommandInteraction, error: BaseException | Exception
):
    """The base on_error event. Call this and use the dictionary as keyword arguments to print to the user"""
    print("OH NO AN ERROR OCCURRED!!!!")
    if isinstance(error, BaseException) and not isinstance(error, Exception):
        # Errors that do not inherit from Exception are not meant to be caught
        await inter.bot.close()
        if exc_info()[0] is not None:
            raise
        raise error
    known_error_result = handle_known_error(error)
    if known_error_result is not None:
        return known_error_result
    return await handle_unexpected_error(inter, error)
