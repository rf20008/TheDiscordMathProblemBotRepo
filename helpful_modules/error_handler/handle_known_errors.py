# This module is licensed under AGPLv3 (This includes everything in this file.)

# You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
# under the GNU General Public License version 3 or at your option, any  later option.
# But versions of the code created and/or distributed *on or after* that date must be distributed
# under the GNU *Affero* General Public License, version 3, or, at your option, any later version.
#
# This file and this module are part of The Discord Math Problem Bot Repo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
import datetime

import disnake
from disnake.ext import commands


from ..threads_or_useful_funcs import get_error_cause
from ..cooldowns import OnCooldown
from ..custom_embeds import ErrorEmbed
from ..problems_module.errors import (
    LinearAlgebraUserInputErrorException,
    LockedCacheException,
)
def handle_known_error(error: BaseException | Exception) -> dict[str, str | disnake.Embed | int] | None:
    cause = get_error_cause(error)
    if isinstance(error, LockedCacheException):
        return {
            "content": "The bot's cache's lock is currently held. Please try again later."
        }
    # print(isinstance(cause, LinearAlgebraUserInputErrorException))
    # print(type(cause))
    if isinstance(error, LinearAlgebraUserInputErrorException):
        return {"embed": ErrorEmbed(str(cause))}
    if isinstance(error, (OnCooldown, disnake.ext.commands.CommandOnCooldown)):
        # This is a cooldown exception
        content = f"This command is on cooldown; please retry **{disnake.utils.format_dt(disnake.utils.utcnow() + datetime.timedelta(seconds=error.retry_after), style='R')}**."
        return {"content": content, "delete_after": error.retry_after}
    if isinstance(error, commands.NotOwner):
        return {"embed": ErrorEmbed("You are not the owner of this bot.")}
    if isinstance(error, disnake.ext.commands.errors.CheckFailure):
        return {"embed": ErrorEmbed(str(error))}
    return None

