"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - Challenge

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
Assisted by Gemini during drafting; reviewed and adapted by the maintainer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional

from .dict_convertible import IdentifiableDictConvertible
from .errors import OwnershipNotDeterminableException
from .register_dicts import register_dict


class ChallengeStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    EXPIRED = "expired"

@register_dict("Challenge")
class Challenge(IdentifiableDictConvertible):
    """Represents a user-bound verification/ownership challenge."""

    def __init__(
        self,
        *,
        challenge_id: str,
        user_id: int,
        created_by: int,
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        completed: bool = False,
        completed_by: Optional[int] = None,
        completed_at: Optional[datetime] = None,
    ) -> None:
        if not isinstance(challenge_id, str) or not challenge_id:
            raise ValueError("challenge_id must be a non-empty string")
        if not isinstance(user_id, int):
            raise TypeError("user_id is not an integer")
        if not isinstance(created_by, int):
            raise TypeError("created_by is not an integer")

        self.challenge_id = challenge_id
        self.user_id = user_id
        self.created_by = created_by
        self.created_at = created_at or datetime.now(timezone.utc)
        self.expires_at = expires_at
        self.completed = bool(completed)
        self.completed_by = completed_by
        self.completed_at = completed_at

    @staticmethod
    def _parse_dt(value: Optional[str | datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        raise TypeError(f"Expected datetime, ISO str, or None, got {type(value)}")

    @staticmethod
    def _format_dt(value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value is not None else None

    @classmethod
    def from_dict(cls, data: Dict) -> "Challenge":
        return cls(
            challenge_id=data["challenge_id"],
            user_id=data["user_id"],
            created_by=data["created_by"],
            created_at=cls._parse_dt(data.get("created_at")),
            expires_at=cls._parse_dt(data.get("expires_at")),
            completed=data.get("completed", False),
            completed_by=data.get("completed_by"),
            completed_at=cls._parse_dt(data.get("completed_at")),
        )

    def to_dict(self) -> Dict:
        return {
            "challenge_id": self.challenge_id,
            "user_id": self.user_id,
            "created_by": self.created_by,
            "created_at": self._format_dt(self.created_at),
            "expires_at": self._format_dt(self.expires_at),
            "completed": self.completed,
            "completed_by": self.completed_by,
            "completed_at": self._format_dt(self.completed_at),
        }

    @property
    def key(self) -> str:
        return self.key_of(challenge_id=self.challenge_id)

    @classmethod
    def key_of(cls, challenge_id: str) -> str: # type: ignore
        return f"Challenge:{challenge_id}"

    def belongs_to_user(self, user_id: int) -> bool:
        if not isinstance(user_id, int):
            raise TypeError("user_id is not an integer")
        return self.user_id == user_id

    def belongs_to_guild(self, guild_id: int | None) -> bool:
        raise OwnershipNotDeterminableException(
            "Challenge objects are bound to users, not guilds."
        )

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        if self.completed or self.expires_at is None:
            return False
        current = now or datetime.now(timezone.utc)
        return current >= self.expires_at

    def status(self, now: Optional[datetime] = None) -> ChallengeStatus:
        if self.completed:
            return ChallengeStatus.COMPLETED
        if self.is_expired(now):
            return ChallengeStatus.EXPIRED
        return ChallengeStatus.PENDING

    def can_complete(self, actor_user_id: int, now: Optional[datetime] = None) -> bool:
        if self.completed:
            return False
        if self.is_expired(now):
            return False
        return self.belongs_to_user(actor_user_id)

    def mark_completed(self, actor_user_id: int, now: Optional[datetime] = None) -> bool:
        if not self.can_complete(actor_user_id, now=now):
            return False
        self.completed = True
        self.completed_by = actor_user_id
        self.completed_at = now or datetime.now(timezone.utc)
        return True

    def __repr__(self) -> str:
        return repr(self.to_dict())

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Challenge) and self.to_dict() == other.to_dict()