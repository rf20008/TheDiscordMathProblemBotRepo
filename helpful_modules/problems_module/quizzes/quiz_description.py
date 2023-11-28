import typing as t
from dataclasses import dataclass
from ..dict_convertible import DictConvertible
from .related_enums import QuizIntensity, QuizTimeLimit
from ..errors import FormatException


@dataclass
class QuizDescription(DictConvertible):
    """A dataclass that holds quiz description"""

    category: str
    intensity: t.Union[QuizIntensity, int]
    description: str
    license: str
    time_limit: t.Union[int, QuizTimeLimit]
    guild_id: int
    author: int

    def __init__(
        self,
        *,
        cache: "MathProblemCache",
        quiz_id: int,
        author: int,
        guild_id: int,
        category: str = "Unspecified",
        intensity: t.Union[QuizIntensity, float] = QuizIntensity.IMPOSSIBLE,
        description="No description given",
        license="Unspecified (the default is GNU GDL)",
        time_limit=QuizTimeLimit.UNLIMITED
    ):
        self.guild_id = guild_id
        self.author = author
        self.quiz_id = quiz_id
        self.cache = cache
        self.category = category
        self.intensity = intensity
        self.description = description
        self.license = license
        self.time_limit = time_limit

    @classmethod
    def from_dict(cls, data: dict) -> "QuizDescription":
        try:
            return cls(
                author=data["author"],
                quiz_id=data["quiz_id"],
                category=data["category"],
                intensity=data["intensity"],
                description=data["description"],
                license=data["license"],
                time_limit=data["timelimit"],
                guild_id=data["guild_id"],
            )
        except KeyError as ke:
            raise FormatException("Bad formatting!") from ke

    @property
    def id(self):
        return self.quiz_id + self.author

    def to_dict(self):
        return {
            "author": self.author,
            "quiz_id": self.quiz_id,
            "category": self.category,
            "intensity": self.intensity,
            "description": self.description,
            "license": self.license,
            "time_limit": self.license,
            "guild_id": self.guild_id,
        }
