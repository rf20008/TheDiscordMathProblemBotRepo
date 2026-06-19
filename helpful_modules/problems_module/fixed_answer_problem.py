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

import disnake
import orjson
from .auto_checkable_problem import AutoGradeableProblem

from .dict_convertible import IdentifiableDictConvertible
from .register_problem import register_problem
from .register_dicts import register_dict
from .errors import *

MAX_ANSWERS_PER_PROBLEM = 30
ANSWER_CHAR_LIMIT = 1000



# TODO: finish from_dict so that it knows to convert to a ComputationalProblem or a LinearAlgebraProblem or some other kind of problem
@register_dict("FixedAnswerProblem")
@register_problem("FixedAnswerProblem")
class FixedAnswerProblem(AutoGradeableProblem):
    """For readability purposes :) This also isn't an ABC."""

    def __init__(
        self,
        *,
        question: str,
        id: int,
        author: int,
        answer: str = None,
        guild_id: typing.Optional[str] = None,
        voters: list = None,
        solvers: list = None,
        answers: list = None,
        tolerance: float = 0.0,
    ):
        super().__init__(
            question=question,
            problem_id=id,
            author=author,
            guild_id=guild_id,
            voters=voters,
            solvers=solvers
        )

        if answers is None:
            answers = []

        if not isinstance(answer, str) and answer is not None:  # answer is None because of answers
            raise TypeError("answer is not a string")
        if not isinstance(answers, list):
            raise TypeError("answers isn't a list")

        if answer is not None:
            if len(answer) > ANSWER_CHAR_LIMIT:
                raise TooLongAnswer(
                    f"Your answer is {len(answer) - ANSWER_CHAR_LIMIT} characters too long. Answers may be up to 100 characters long."
                )
            self.answer = answer
        self.answers = answers
        self.tolerance = tolerance

    @classmethod
    def from_dict(cls, info: dict):
        """Convert a dictionary to a math problem. cache must be a valid MathProblemCache"""
        # print(cls)
        assert isinstance(info, dict)
        assert info["guild_id"] is None or isinstance(info["guild_id"], int)
        # Remove the guild_id null (used for global problems), which is not used any more because of conflicts with sql.

        problem_id = info.get("problem_id") or info.get('id')

        problem = cls(
            question=info["question"],  # type: ignore
            id=int(problem_id),
            guild_id=info["guild_id"],
            voters=info["voters"],
            solvers=info["solvers"],
            author=info["author"],
            answer=info["answer"],
            answers=info["answers"],
            tolerance=info["tolerance"],
            **info["extra_stuff"] # type: ignore
        )  # Problem-ify the problem, but set the guild_id to None and return it
        return problem

    def to_dict(self):
        """Convert myself to a dictionary"""
        _dict = {
            **super().to_dict(),
            "answer": self.answer,
            "answers": self.answers,
            "tolerance": self.tolerance,
            **self.get_extra_stuff(),
        }
        return _dict

    def add_answer(self, answer: str):
        """Add an answer"""
        warnings.warn(
            "Warning: Answers are not used in the default implementation",
            category=PMDeprecationWarning,
        )
        if len(self.answers) + 1 > MAX_ANSWERS_PER_PROBLEM:
            raise MathProblemsModuleException("Too many answers!")
        self.answers.append(answer)
        asyncio.run(self.update_self())

    def get_answer(self):
        """Return my answer. This has been deprecated"""
        raise PMDeprecationWarning(
            "I have finally deprecated this, due to the new hirearchy. Use check_answer instead"
        )

    def get_answers(self):
        """Return my possible answers"""
        raise PMDeprecationWarning(
            "I have finally deprecated this, due to the new hirearchy. Use check_answer instead"
        )

    def check_answer(self, answer):
        """Checks the answer. Returns True if it's correct and False otherwise."""
        # warnings.warn("This method is deprecated. please use .", PMDeprecationWarning)
        return answer in self.answers or answer == self.answer

    def __str__(self, include_answer: bool = False, vote_threshold: int = 0) -> str:
        _str = f"""Question: '{self.question}', 
        id: {self.id}, 
        guild_id: {self.guild_id}, 
        solvers: {[f'<@{id}>' for id in self.solvers]},
        author: <@{self.author}>
        number of votes: {len(self.voters)}"""
        if vote_threshold != 0:
            _str += f"/{vote_threshold}"
        _str += "\n"
        for key, value in self.get_extra_stuff().items():
            _str += f"{key}: {value}\n"
        if include_answer:
            _str += f"\nAnswer: {self.answer}"
        return str(_str)

    def __deepcopy__(self, memo):
        if id(self) in memo:
            return memo[id(self)]

        cls = self.__class__

        copied = cls.__new__(cls)
        memo[id(self)] = copied

        for k, v in self.__dict__.items():
            setattr(copied, k, deepcopy(v, memo))

        return copied

