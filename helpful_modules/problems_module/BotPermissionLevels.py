"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - BotPermissionLevels

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
"""
from enum import IntFlag


class BotPermissionLevel(IntFlag):
    USER = 0
    TRUSTED = 1<<0
    MOD = 1<<1
    ADMIN = 1<<2
    DEVELOPER = 1<<3
    OWNER = 1<<4

    def __getattr__(self, name: str) -> bool:
        """
        Allows checking if a flag is present using dot notation on an instance.
        Example: user_perms.MOD -> returns True or False
        """
        try:
            # Look up the flag by name in the Enum class
            flag = self.__class__[name]
            return flag in self
        except KeyError:
            # Fallback to standard attribute behavior if it's not a valid flag name
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

class BotRestrictionLevel(IntFlag):
    NONE = 0
    DENYLISTED = 1<<0
    APPEAL_DENYLISTED = 1<<1
    VERIFICATION_CODE_DENYLISTED = 1<<2

    def __getattr__(self, name: str) -> bool:
        """
        Allows checking if a flag is present using dot notation on an instance.
        Example: user_perms.MOD -> returns True or False
        """
        try:
            # Look up the flag by name in the Enum class
            flag = self.__class__[name]
            return flag in self
        except KeyError:
            # Fallback to standard attribute behavior if it's not a valid flag name
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
