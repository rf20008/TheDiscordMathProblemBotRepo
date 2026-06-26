"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - UserData

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""

import orjson

from . import OwnershipNotDeterminableException
from .BotPermissionLevels import BotPermissionLevel, BotRestrictionLevels
from .denylistable import DenylistMetadata, DenylistType
from .dict_convertible import IdentifiableDictConvertible

def parse_denylist_metadata(value: DenylistMetadata | str | dict | None = None) -> DenylistMetadata:
    """Helper method to handle parsing of input formats into DenylistMetadata instances."""
    if value is None:
        return DenylistMetadata(
            denylisted=False,
            denylist_reason="",
            denylist_expiry=float("-inf"),
            denylisting_moderator="",
            denylist_type=DenylistType.UNKNOWN,
        )
    if isinstance(value, str):
        value = orjson.loads(value)
    if isinstance(value, dict):
        return DenylistMetadata.from_dict(value)
    if isinstance(value, DenylistMetadata):
        return value
    raise TypeError(f"Expected DenylistMetadata, dict, or str, but got {type(value)}")

class UserData(IdentifiableDictConvertible):
    """A dataclass to store user data for the bot!"""

    verification_code_denylist: DenylistMetadata
    denylist: DenylistMetadata
    appeal_denylist: DenylistMetadata
    user_id: int
    permissions: BotPermissionLevel
    appeal_num: int
    def __init__(
        self,
        *,
        user_id: int,
        appeal_num: int,
        permissions: BotPermissionLevel = None,
        denylist: DenylistMetadata | dict | str | None = None,
        verification_code_denylist: DenylistMetadata | dict | str | None = None,
        appeal_denylist: DenylistMetadata | dict | str | None = None,
    ):
        if not isinstance(user_id, int):
            raise TypeError("user_id is not an integer")
        if not isinstance(permissions, BotPermissionLevel):
            raise TypeError("trusted isn't a boolean")
        self.permissions = permissions
        self.user_id = user_id
        self.denylist = parse_denylist_metadata(denylist)
        self.verification_code_denylist = parse_denylist_metadata(verification_code_denylist)
        self.appeal_denylist = parse_denylist_metadata(appeal_denylist)

    @classmethod
    def from_dict(cls, dict: dict) -> "UserData":
        """Create UserData from a dictionary"""
        return cls(
            user_id=dict["user_id"],
            trusted=dict["trusted"],
            denylisted=dict["denylisted"],
            denylist_expiry=dict["denylist_expiry"],
            denylist_reason=dict["denylist_reason"],
            verification_code_denylist=dict.get("verification_code_denylist", None),
        )

    def to_dict(self) -> dict:
        """Convert UserData to a dictionary"""
        return {
            "user_id": self.user_id,
            "trusted": self.trusted,
            "denylisted": self.denylisted,
            "denylist_expiry": self.denylist_expiry,
            "denylist_reason": self.denylist_reason,
            "verification_code_denylist": self.verification_code_denylist,
        }

    @classmethod
    def default(cls, user_id: int):
        """Return a default UserData instance"""
        return cls(
            user_id=user_id,
            trusted=False,
            denylisted=False,
            denylist_reason="",
            denylist_expiry=0.0,
            verification_code_denylist=None,
        )
    def key(self) -> str:
        return self.key_of(user_id=self.user_id)
    @classmethod
    def key_of(cls, user_id: int) -> str:
        return f"UserData:{user_id}"
    def belongs_to_guild(self, guild_id: int | None) -> bool:
        raise OwnershipNotDeterminableException("UserData only belong to users, not guilds.")
    def belongs_to_user(self, user_id: int):
        if not isinstance(user_id, int):
            raise TypeError("user_id is not an integer")
        return self.user_id == user_id
    @property
    def denylisted(self) -> bool:
        return self.denylist.is_denylisted()
    @property
    def denylist_expiry(self) -> float:
        return self.denylist.denylist_expiry
    @property
    def denylist_reason(self) -> str:
        return self.denylist.denylist_reason
    @property
    def trusted(self) -> bool:
        return self.permissions.TRUSTED # type: ignore