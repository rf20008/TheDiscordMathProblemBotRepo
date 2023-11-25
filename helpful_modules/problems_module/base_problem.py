import asyncio
import pickle
import sys
import traceback
import typing
import warnings
from copy import deepcopy
from typing import Optional
import disnake
from .dict_convertible import DictConvertible
from .errors import *

ANSWER_CHAR_LIMIT = 1000
QUESTION_CHAR_LIMIT = 2000


class BaseProblem(DictConvertible):
    """For readability purposes :) This also isn't an ABC."""

    def __init__(
        self,
        question: str,
        id: int,
        author: int,
        answer: str = None,
        guild_id: typing.Optional[int] = None,
        voters: list = None,
        solvers: list = None,
        cache=None,
        answers: list = None,
    ):
        if voters is None:
            voters = []
        if solvers is None:
            solvers = []
        if answers is None:
            answers = []
        if guild_id is not None and not isinstance(guild_id, str):
            raise TypeError("guild_id is not an string")
        if not isinstance(id, int):
            raise TypeError("id is not an integer")
        if not isinstance(question, str):
            raise TypeError("question is not a string")
        if (
            not isinstance(answer, str) and answer is not None
        ):  # answer is None because of answers
            raise TypeError("answer is not a string")
        if not isinstance(author, int):
            raise TypeError("author is not an integer")
        if not isinstance(voters, list):
            raise TypeError("voters is not a list")
        if not isinstance(solvers, list):
            raise TypeError("solvers is not a list")
        if not isinstance(answers, list):
            raise TypeError("answers isn't a list")

        if cache is None:
            warnings.warn("_cache is None. This may cause errors", RuntimeWarning)
        # if not isinstance(cache,MathProblemCache) and cache is not None:
        #    raise TypeError("_cache is not a MathProblemCache.")
        if len(question) > QUESTION_CHAR_LIMIT:
            raise TooLongQuestion(
                f"Your question is {len(question) - QUESTION_CHAR_LIMIT} characters too long. Questions may be up to 250 characters long."
            )
        self.question = question
        if answer is not None:
            if len(answer) > ANSWER_CHAR_LIMIT:
                raise TooLongAnswer(
                    f"Your answer is {len(answer) - ANSWER_CHAR_LIMIT} characters too long. Answers may be up to 100 characters long."
                )
            self.answer = answer
        self.id = id
        self.guild_id = guild_id
        self.voters = voters
        self.solvers = solvers
        self.author = author
        self._cache = cache
        self.answers = answers

    async def edit(
        self,
        question: str = None,
        answer: Optional[str] = None,
        id: Optional[int] = None,
        guild_id: Optional[int] = None,
        voters: typing.Optional[typing.List[str]] = None,
        solvers: typing.Optional[typing.List[str]] = None,
        author: typing.Optional[int] = None,
        answers: typing.Optional[typing.Union[int, str, bool]] = None,
    ) -> None:
        """Edit a problem. The edit is in place."""
        if answers is not None and not isinstance(answers, list):
            raise TypeError("Answers is not a list!")
        else:
            for item in range(len(answers)):
                if not isinstance(answers[item], (int, str, bool)):
                    raise TypeError(
                        f"Item #{item} is not an integer, string, or boolean!"
                    )

        if guild_id not in [None, None] and not isinstance(guild_id, int):
            raise TypeError("guild_id is not an integer")
        if not isinstance(id, int) and id is not None:
            raise TypeError("id is not an integer")
        if not isinstance(question, str) and question is not None:
            raise TypeError("question is not a string")
        if not isinstance(answer, str) and answer is not None:
            raise TypeError("answer is not a string")
        if not isinstance(author, int) and author is not None:
            raise TypeError("author is not an integer")
        if not isinstance(voters, list) and voters is not None:
            raise TypeError("voters is not a list")
        if not isinstance(solvers, list) and solvers is not None:
            raise TypeError("solvers is not a list")
        if (
            id is not None
            or guild_id is not None
            or voters is not None
            or solvers is not None
            or author is not None
        ):
            warnings.warn(
                "You are changing one of the attributes that you should not be changing.",
                category=RuntimeWarning,
            )
        if question is not None and len(question) > QUESTION_CHAR_LIMIT:
            raise TooLongQuestion(
                f"Your question is {len(question) - QUESTION_CHAR_LIMIT} characters too long. Questions may be up to {QUESTION_CHAR_LIMIT} characters long."
            )
        self.question = question
        if answer is not None and len(answer) > ANSWER_CHAR_LIMIT:
            raise TooLongAnswer(
                f"Your question is {len(answer) - ANSWER_CHAR_LIMIT} characters too long. Questions may be up to {ANSWER_CHAR_LIMIT} characters."
            )
        for answer in answers:
            if answer is None or not isinstance(answer, str):
                raise TypeError("One of your answers is `None` or not a string.")

            if len(answer) > ANSWER_CHAR_LIMIT:
                raise TooLongAnswer(
                    f"Answer #{answer} is {len(answers[answer]) - ANSWER_CHAR_LIMIT} characters too long. Answers can be up to a {ANSWER_CHAR_LIMIT} characters long"
                )
        self.answers = answers
        if answer is not None:
            self.answer = answer
        if id is not None:
            self.id = id
        if guild_id is not None:
            self.guild_id = guild_id
        if voters is not None:
            self.voters = voters
        if solvers is not None:
            self.solvers = solvers
        if author is not None:
            self.author = author

    async def update_self(self):
        """A helper method to update the cache with my version"""
        warnings.warn(
            "This method no longer automatically updates the problem. You must be in an async context and update the problem in the cache yourself.",
            PMDeprecationWarning,
        )
        if self._cache is not None:
            await self._cache.update_problem(self.id, self)

    @classmethod
    def from_row(cls, row: dict, cache=None):
        """Convert a dictionary-ified row into a MathProblem"""
        if not isinstance(row, dict):
            raise TypeError("The problem has not been dictionary-ified")

        try:
            answers = pickle.loads(
                row["answers"]
            )  # Load answers from bytes to a list (which should contain only pickleable objects)!
            voters = pickle.loads(row["voters"])  # Do the same for voters and solvers
            solvers = pickle.loads(row["voters"])
            _Row = {
                "guild_id": row["guild_id"],  # Could be None
                "problem_id": row["problem_id"],
                "answer": Exception,  # Placeholder,
                "answers": answers,
                "voters": voters,
                "solvers": solvers,
                "author": row["author"],
                "question": row["question"],
                "id": row["problem_id"],
            }
            return cls.from_dict(_Row, cache=cache)
        except BaseException as e:
            traceback.print_exception(
                type(e), e, e.__traceback__, file=sys.stderr
            )  # Log to stderr
            raise SQLException(
                "Uh oh..."
            ) from e  # Re-raise the exception to the user (so that they can help me debug (error_logs/** is git-ignored))

    @classmethod
    def from_dict(cls, _dict: dict, cache=None):
        """Convert a dictionary to a math problem. cache must be a valid MathProblemCache"""
        assert isinstance(_dict, dict)
        assert _dict["guild_id"] is None or isinstance(_dict["guild_id"], int)
        problem = _dict
        guild_id = problem["guild_id"]
        if (
            guild_id is None
        ):  # Remove the guild_id null (used for global problems), which is not used any more because of conflicts with sql.
            problem = cls(
                question=problem["question"],
                answers=problem["answers"],
                id=int(problem["id"]),
                guild_id=None,
                voters=problem["voters"],
                solvers=problem["solvers"],
                author=problem["author"],
                cache=cache,
            )  # Problem-ify the problem, but set the guild_id to None and return it
            return problem
        problem2 = cls(
            question=problem["question"],
            answer=problem["answer"],
            id=int(problem["id"]),
            guild_id=guild_id,
            voters=problem["voters"],
            solvers=problem["solvers"],
            author=problem["author"],
            cache=cache,
        )
        return problem2

    def to_dict(self, show_answer: bool = True):
        """Convert myself to a dictionary"""
        _dict = {
            "type": "MathProblem",
            "question": self.question,
            "id": str(self.id),
            "guild_id": str(self.guild_id),
            "voters": self.voters,
            "solvers": self.solvers,
            "author": self.author,
        }
        if show_answer:
            _dict["answers"] = self.get_answers()
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

    def add_answer(self, answer: str):
        """Add an answer"""
        if len(self.answers) + 1 > self._cache.max_answers_per_problem:
            raise MathProblemsModuleException("Too many answers!")
        self.answers.append(answer)
        asyncio.run(self.update_self())

    def get_answer(self):
        """Return my answer. This has been deprecated"""
        warnings.warn("This has been deprecated!", DeprecationWarning, stacklevel=1)
        return self.answer

    def get_answers(self):
        """Return my possible answers"""
        return list(self.answers)

    def get_question(self):
        """Return my question."""
        return self.question

    def check_answer_and_add_checker(self, answer, potential_solver):
        """Checks the answer. If it's correct, it adds potentialSolver to the solvers."""
        if not isinstance(potential_solver, disnake.User) and not isinstance(
            potential_solver, disnake.Member
        ):
            raise TypeError("potentialSolver is not a User object")
        if answer in self.answers:
            self.add_solver(potential_solver)
            warnings.warn(
                "This method no longer automatically updates the problem. You must be in an async context and update the problem in the cache yourself.",
                PMDeprecationWarning,
            )

    def check_answer(self, answer):
        """Checks the answer. Returns True if it's correct and False otherwise."""
        warnings.warn("This method is deprecated. please use .", PMDeprecationWarning)
        return answer in self.get_answers()

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
        return user.id == self.get_author()

    def __eq__(self, other: typing.Any) -> bool:
        """Return self==other"""
        if not isinstance(self, type(other)):
            return False
        try:
            return self.question == other.question and other.answer == self.answer
        except AttributeError:
            return False

    def __repr__(self: "BaseProblem") -> str:
        """A method that when called, returns a string, that when executed, returns an object that is equal to this one. Also implements repr(self)"""
        return f"""problems_module.BaseProblem(question={self.question},
        answers = {self.answers}, id = {self.id}, guild_id={self.guild_id},
        voters={self.voters},solvers={self.solvers},author={self.author},cache={None})"""  # If I stored the problems, then there would be an infinite loop

    def __str__(self, include_answer: bool = False) -> str:
        _str = f"""Question: '{self.question}', 
        id: {self.id}, 
        guild_id: {self.guild_id}, 
        solvers: {[f'<@{id}>' for id in self.solvers]},
        author: <@{self.author}>"""
        if include_answer:
            _str += f"\nAnswer: {self.answer}"
        return str(_str)

    def __deepcopy__(self: "BaseProblem", memo: typing.Any):
        """Deepcopy myself. Required for MathProblemCache.update_cache() to work.
        Time complexity: O(V^2+S^2) (uh oh)
        """
        return BaseProblem(
            question=deepcopy(self.question),
            voters=deepcopy(self.voters),
            answers=deepcopy(self.answers),
            solvers=deepcopy(self.solvers),
            author=deepcopy(self.author),
            id=deepcopy(self.id),
            guild_id=deepcopy(self.guild_id),
            cache=self._cache,
        )
