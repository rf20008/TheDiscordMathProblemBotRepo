from enum import Enum
from typing import *


class AppealType(Enum):
    BLACKLIST_APPEAL = 0
    GUILD_BLACKLIST_APPEAL = 1
    SUPPORT_SERVER_BAN = 2
    SUPPORT_SERVER_MISC_PUNISHMENT = 3
    OTHER = 4

class Appeal:
    __slots__ = (
        "user_id",
        "appeal_msg",
        "timestamp",
        "appeal_num",
        "cache",
        "special_id",
        "type",
    )

    def __init__(
        self,
        *,
        user_id: int,
        appeal_msg: str,
        timestamp: int,
        appeal_num: int,
        special_id: int,
        cache: "MathProblemCache",
        type: int,
    ):
        try:
            self.type = AppealType(type)
        except:
            raise ValueError(f"{type} is not a valid AppealType")
        self.user_id = user_id
        self.appeal_msg = appeal_msg
        self.timestamp = timestamp
        self.appeal_num = appeal_num
        self.special_id = special_id
        self.cache = cache

    @classmethod
    def from_dict(cls, data: dict, cache: "MathProblemCache"):
        return cls(
            user_id=data["user_id"],
            appeal_msg=data["appeal_msg"],
            timestamp=data["timestamp"],
            appeal_num=data["appeal_num"],
            special_id=data["special_id"],
            type=data["type"],
            cache=cache,
        )

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "appeal_msg": self.appeal_num,
            "timestamp": self.timestamp,
            "appeal_num": self.appeal_num,
            "special_id": self.special_id,
            "appeal_type": str(self.type.name),
        }

    def __str__(self):
        return f"""
        Appeal from <@{self.user_id}>:
        type: {str(self.type.name)}
        timestamp: {disnake.utils.format_dt(self.timestamp)}
        
        Appeal message: {self.appeal_msg}
        
        This is appeal #{self.appeal_num}
        and its special id is {self.special_id}
        
"""
