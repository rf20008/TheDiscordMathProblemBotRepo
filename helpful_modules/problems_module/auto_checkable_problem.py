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
from .base_problem import BaseProblem
from abc import ABC, abstractmethod
from .errors import *

MAX_ANSWERS_PER_PROBLEM = 30
ANSWER_CHAR_LIMIT = 1000
QUESTION_CHAR_LIMIT = 2000


# TODO: finish from_dict so that it knows to convert to a ComputationalProblem or a LinearAlgebraProblem or some other kind of problem
@register_problem("auto_gradeableproblem")
class AutoGradeableProblem(ABC, BaseProblem):
    @abstractmethod
    def check_answer(self, answer: str) -> bool:
        pass

    def check_answer_and_add_checker(self, answer, potential_solver):
        """Checks the answer. If it's correct, it adds potentialSolver to the solvers."""
        if not isinstance(potential_solver, disnake.User) and not isinstance(
            potential_solver, disnake.Member
        ):
            raise TypeError("potentialSolver is not a User object")
        if self.check_answer(answer):
            self.add_solver(potential_solver)
            warnings.warn(
                "This method no longer automatically updates the problem. You must be in an async context and update the problem in the cache yourself.",
                PMDeprecationWarning,
            )
