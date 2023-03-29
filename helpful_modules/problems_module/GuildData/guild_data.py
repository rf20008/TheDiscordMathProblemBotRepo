import json

from ..errors import InvalidDictionaryInDatabaseException
from .the_basic_check import CheckForUserPassage


class GuildData:
    blacklisted: bool
    guild_id: int
    can_create_problems_check: CheckForUserPassage
    can_create_quizzes_check: CheckForUserPassage
    mods_check: CheckForUserPassage
    cache: "MathProblemCache"

    def __init__(
        self,
        guild_id: int,
        blacklisted: bool,
        can_create_problems_check: str,
        can_create_quizzes_check: str,
        mods_check: str,
        cache,
    ):
        """
        Do not instantiate this manually! The `py:class:MathProblemCache` will do it for you.
        Parameters
        ----------
        guild_id : int
            The ID of the guild that this `GuildData` is attached to.
        blacklisted : bool
            Whether this guild is blacklisted. If this is not found in the database , then it will be `False` by default.
        can_create_quizzes_check : str
            This is a JSON representation of the `py:class:CheckForUserPassage` to check whether a user can create quizzes.
            Defaults to allowing everyone to create quizzes.
        can_create_problems_check: str
            This is a JSON representation of the `py:class:CheckForUserPassage` used to check whether users can create problems - defaulting to everyone!
        mods_check : str
            This is a JSON representation of the `py:class:CheckForUserPassage` used to check whether someone is a moderator and can do mod commands with the bot.
            Defaults to requiring administrator permissions.
        cache: py:class:MathProblemCache
            Internally used for internal state!
        an instance of py:class:MathProblemCache which is internally used for internal state (but it's not used in this current version)


        Raises
        ---------
        InvalidDictionaryInDatabaseException
            This exception would be raised if `can_create_quizzes_check`, `can_create_problems_check`, or `mods_check` could not be parsed into JSON
        """
        self.cache = cache
        if not isinstance(guild_id, int):
            raise TypeError(
                f"I expected guild_id to be an int, but I got a {guild_id.__class__.name__} instead!"
            )
        self.guild_id = guild_id
        if not isinstance(guild_id, bool):
            raise TypeError(
                f"I expected guild_id to be an int, but I got a {guild_id.__class__.name__} instead!"
            )
        self.blacklisted = blacklisted
        try:
            self.can_create_problems_check = CheckForUserPassage.from_dict(
                json.loads(can_create_problems_check)
            )
        except json.JSONDecodeError as exc:
            raise InvalidDictionaryInDatabaseException.from_invalid_data(
                can_create_problems_check
            ) from exc
        except KeyError as exc:
            raise InvalidDictionaryInDatabaseException(
                f"I was able to parse {can_create_problems_check} into a dictionary, but I couldn't find the key called {str(exc)}!"
            ) from exc
        try:
            self.can_create_quizzes_check = CheckForUserPassage.from_dict(
                json.loads(can_create_quizzes_check)
            )
        except json.JSONDecodeError as exc:
            raise InvalidDictionaryInDatabaseException.from_invalid_data(
                can_create_quizzes_check
            ) from exc
        except KeyError as exc:
            raise InvalidDictionaryInDatabaseException(
                f"I was able to parse {can_create_quizzes_check} into a dictionary, but I couldn't find the key called {str(exc)}!"
            ) from exc

        try:
            self.mods_check = CheckForUserPassage.from_dict(json.loads(mods_check))
        except json.JSONDecodeError as exc:
            raise InvalidDictionaryInDatabaseException.from_invalid_data(
                mods_check
            ) from exc
        except KeyError as exc:
            raise InvalidDictionaryInDatabaseException(
                f"I was able to parse {mods_check} into a dictionary, but I couldn't find the key called {str(exc)}!"
            ) from exc

    @classmethod
    def from_dict(cls, data: dict, cache) -> "GuildData":
        return cls(
            blacklisted=bool(data["blacklisted"]),
            guild_id=data["guild_id"],
            can_create_problems_check=data["can_create_problems_check"],
            mods_check=data["mods_check"],
            can_create_quizzes_check=data["can_create_quizzes_check"],
            cache=cache,
        )

    def to_dict(self, include_cache: bool) -> dict:
        dict_to_return = {
            "blacklisted": int(self.blacklisted),
            "guild_id": self.guild_id,
            "can_create_problems_check": self.can_create_problems_check,
            "can_create_quizzes_check": self.can_create_quizzes_check,
            "mods_check": self.mods_check,
        }
        if include_cache:
            dict_to_return["cache"] = self.cache

        return dict_to_return
