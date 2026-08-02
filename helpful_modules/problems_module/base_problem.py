"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

This file is part of The Discord Math Problem Bot Repo

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

import asyncio
import pickle
import sys
import traceback
import typing
import warnings
from copy import deepcopy
from typing import Optional

from .register_problem import register_problem, CLASS_TO_TYPE
import disnake
import orjson

from .dict_convertible import IdentifiableDictConvertible
from .errors import *

QUESTION_CHAR_LIMIT = 2000


# TODO: finish from_dict so that it knows to convert to a ComputationalProblem or a LinearAlgebraProblem or some other kind of problem
@register_problem("base_problem")
class BaseProblem(IdentifiableDictConvertible):
    """For readability purposes :) This is a partial ABC, but shares information related to all information."""

    question: str
    author: int
    problem_id: int
    guild_id: int | None
    voters: list[int]
    solvers: list[int]

    def __init__(
        self,
        *,
        question: str,
        author: int,
        problem_id: int | None = None,
        guild_id: typing.Optional[int] = None,
        voters: list | None = None,
        solvers: list | None = None,
    ):
        self.type = CLASS_TO_TYPE[self.__class__]
        if voters is None:
            voters = []
        if solvers is None:
            solvers = []

        if guild_id is not None and not isinstance(guild_id, int):
            raise TypeError("guild_id is not an integer")
        if not isinstance(problem_id, int) and problem_id is not None:
            raise TypeError("problem_id is not an integer")
        if not isinstance(question, str):
            raise TypeError("question is not a string")
        if len(question) > QUESTION_CHAR_LIMIT:
            raise TooLongQuestion(
                f"Your question is {len(question) - QUESTION_CHAR_LIMIT} characters too long. Questions may be up to 250 characters long."
            )
        if not isinstance(author, int):
            raise TypeError("author is not an integer")
        if not isinstance(voters, list):
            raise TypeError("voters is not a list")
        if not isinstance(solvers, list):
            raise TypeError("solvers is not a list")

        # if not isinstance(cache,MathProblemCache) and cache is not None:
        #    raise TypeError("_cache is not a MathProblemCache.")

        self.question = question

        self.id = problem_id
        self.guild_id = guild_id
        self.voters = voters
        self.solvers = solvers
        self.author = author

    @property
    def problem_id(self) -> int:
        return self.id

    @staticmethod
    def try_to_convert_to_list(thing):
        if isinstance(thing, bytes):
            return pickle.loads(thing)
        elif isinstance(thing, str):
            return orjson.loads(thing)
        else:
            if not isinstance(thing, list):
                raise TypeError(
                    f"{thing} is not of an expected type, but is of type {thing.__class__.__name__}."
                )
            return thing

    @classmethod
    def from_row(cls, row: dict, cache=None):
        """Convert a dictionary-ified row into a MathProblem"""
        if not isinstance(row, dict):
            raise TypeError("The problem has not been dictionary-ified")
        try:
            voters = cls.try_to_convert_to_list(
                row["voters"]
            )  # DO the same for voters and solvers
            solvers = cls.try_to_convert_to_list(row["solvers"])
            our_row = dict()
            our_row.update(row)
            del our_row["problem_id"]
            our_row["id"] = row["problem_id"]
            our_row["voters"] = voters
            our_row["solvers"] = solvers
            our_row["tolerance"] = (row.get("tolerance", None),)
            our_row.update(orjson.loads(row.get("extra_stuff", "{}").replace("'", '"')))
            try:
                del our_row["extra_stuff"]
            except KeyError:
                pass
            return cls.from_dict(our_row, cache=cache)
        except BaseException as e:
            traceback.print_exception(
                type(e), e, e.__traceback__, file=sys.stderr
            )  # Log to stderr
            raise SQLException(
                f"Uh oh... a row {row} is not of the expected format"
            ) from e  # Re-raise the exception to the user (so that they can help me debug (error_logs/** is git-ignored))

    @classmethod
    def from_dict(cls, info: dict):
        """Convert a dictionary to a math problem. cache must be a valid MathProblemCache"""
        # print(cls)
        assert isinstance(info, dict)
        assert info["guild_id"] is None or isinstance(info["guild_id"], int)
        # Remove the guild_id null (used for global problems), which is not used any more because of conflicts with sql.

        problem_id = info.get("problem_id") or info.get("id")

        problem = cls(
            question=info["question"],  # type: ignore
            problem_id=int(problem_id),
            guild_id=info["guild_id"],
            voters=info["voters"],
            solvers=info["solvers"],
            author=info["author"],
            **info["extra_stuff"],  # type: ignore
        )  # Problem-ify the problem, but set the guild_id to None and return it
        return problem

    def to_dict(self):
        """Convert myself to a dictionary"""
        _dict = {
            "type": self.type,
            "question": self.question,
            "id": self.id,
            "guild_id": self.guild_id,
            "voters": self.voters,
            "solvers": self.solvers,
            "author": self.author,
            "extra_stuff": self.get_extra_stuff(),
        }
        return _dict

    def convert_to_dict(self, show_answer: bool = True):
        """Convert self to a dictionary. Alias for to_dict"""
        return self.to_dict(show_answer)

    def add_voter(self, voter: typing.Union[disnake.User, disnake.Member]):
        """Adds a voter. Voter must be a disnake.User object or disnake.Member object."""
        if not isinstance(voter, disnake.User) and not isinstance(
            voter, disnake.Member
        ):
            raise TypeError("User is not a User object")
        if not self.is_voter(voter):
            self.voters.append(voter.id)
        warnings.warn(
            "This method no longer automatically updates the problem. You must be in an async context and update the problem in the cache yourself.",
            PMDeprecationWarning,
        )

    def add_solver(self, solver: typing.Union[disnake.User, disnake.Member]):
        """Adds a solver. Solver must be a disnake.User object or disnake.Member object."""
        if not isinstance(solver, disnake.User) and not isinstance(
            solver, disnake.Member
        ):
            raise TypeError("Solver is not a User object")
        if not self.is_solver(solver):
            self.solvers.append(solver.id)
            warnings.warn(
                "This method no longer automatically updates the problem. You must be in an async context and update the problem in the cache yourself.",
                PMDeprecationWarning,
            )

    def get_question(self):
        """Return my question."""
        return self.question

    def my_id(self):
        """Returns id & guild_id in a list. id is first and guild_id is second."""
        return [self.id, self.guild_id]

    def get_voters(self):
        """Returns self.voters"""
        return self.voters

    def get_num_voters(self):
        """Returns the number of solvers."""
        return len(self.get_voters())

    def is_voter(self, user: typing.Union[disnake.User, disnake.Member]):
        """Returns True if user is a voter. False otherwise. User must be a disnake.User or disnake.Member object."""
        if not isinstance(user, disnake.User) and not isinstance(user, disnake.Member):
            raise TypeError("User is not actually a User")
        return user.id in self.get_voters()

    def get_solvers(self):
        """Returns self.solvers"""
        return self.solvers

    def is_solver(self, user: typing.Union[disnake.User, disnake.Member]) -> bool:
        """Returns True if user is a solver. False otherwise. User must be a disnake.User or disnake.Member object."""
        if not isinstance(user, disnake.User) and not isinstance(user, disnake.Member):
            raise TypeError("User is not actually a User")
        return user.id in self.get_solvers()

    def get_author(self):
        """Returns self.author"""
        return self.author

    @property
    def _int_guild_id(self):
        if self.guild_id:
            return self.guild_id
        return -1

    def is_author(self, user: typing.Union[disnake.User, disnake.Member]):
        """Returns if the user is the author"""
        if not isinstance(user, disnake.User) and not isinstance(user, disnake.Member):
            raise TypeError("User is not actually a User")
        return user.id == self.author

    def __eq__(self, other: typing.Any) -> bool:
        """Return self==other"""
        return isinstance(other, type(self)) and self.to_dict() == other.to_dict()

    def __repr__(self: "BaseProblem") -> str:
        """A method that when called, returns a string, that when executed, returns an object that is equal to this one. Also implements repr(self)"""
        extra_stuff_included = " ".join(
            f"{key}={value}" for key, value in self.get_extra_stuff().items()
        )

        return f"""problems_module.BaseProblem(question='{self.question}', id = {self.id}, guild_id={self.guild_id}, voters={self.voters}, solvers={self.solvers}, author={self.author}, {extra_stuff_included})"""  # If I stored the problems, then there would be an infinite loop

    def __str__(
        self, include_answer: bool = False, vote_threshold: int | None = None
    ) -> str:
        _str = f"""Question: '{self.question}', 
        id: {self.id}, 
        guild_id: {self.guild_id}, 
        solvers: {[f'<@{id}>' for id in self.solvers]},
        author: <@{self.author}>
        number of votes: {len(self.voters)}"""
        if vote_threshold is not None:
            _str += f"/{vote_threshold}"
        _str += "\n"
        if include_answer:
            _str += f"\nAnswer: {self.answer}"
        return str(_str)
        # SUbclasses should avoid it

    def __deepcopy__(self: "FixedAnswerProblem", memo: typing.Any):
        """Deepcopy myself. Required for MathProblemCache.update_cache() to work.
        Time complexity: O(V+S) (uh oh)
        """
        return type(self).from_dict(deepcopy(self.to_dict()))

    def get_extra_stuff(self) -> dict[str, typing.Any]:
        """Return the extra stuff for this dictionary, that doesn't go in just a FixedAnswerProblem. Override this if you're in a subclass"""
        return {}

    @classmethod
    def key_of(cls, *, guild_id: int | None, id: int) -> str:
        return f"Problem:{guild_id}:{id}"

    def key(self) -> str:
        return self.key_of(guild_id=self.guild_id, id=self.id)

    async def belongs_to_user(self, user_id: int) -> bool:
        return self.author == user_id

    async def belongs_to_guild(self, guild_id: int | None) -> bool:
        return self.guild_id == guild_id
