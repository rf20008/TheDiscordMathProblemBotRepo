import json
from warnings import warn
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
        self.cache = cache
        self.guild_id = guild_id
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

    def get_mod_check(self):
        return self.mods_check

    def set_mod_check(self, value: CheckForUserPassage):
        if not isinstance(value, CheckForUserPassage):
            warnings.warn(
                "The mod check is being set to an object that is not of type CheckForUserPassage, instead it is of type "
                + value.__class__.__name__
                + "...",
                stacklevel=2,
            )  # noqa: E401
        self.mods_check = value

    def del_mod_check(self):
        del self.mods_check

    mod_check = property(get_mod_check, set_mod_check, del_mod_check)

    @classmethod
    def default(cls, guild_id: int) -> "GuildData":
        return cls(
            guild_id=guild_id,
            blacklisted=False,
            can_create_quizzes_check=CheckForUserPassage.default(),
            can_create_problems_check=CheckForUserPassage.default(),
            mods_check=CheckForUserPassage.default_mod_check(),
        )

    def __eq__(self, other: typing.Any):
        if not isinstance(other, GuildData):
            return False  # There is no way that these objects are equal if they are of different types
        return (
            self.guild_id == other.guild_id
            and self.blacklisted == other.blacklisted
            and self.mod_check == other.mod_check
            and self.can_create_quizzes_check== other.can_create_quizzes_check
            and self.can_create_problems_check==other.can_create_problems_check
        )
    def is_default(self):
        return self == GuildData.default(self.guild_id)
