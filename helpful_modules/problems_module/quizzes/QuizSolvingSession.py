import pickle
import time
import typing
from asyncio import run

from helpful_modules.problems_module.errors import *
from helpful_modules.threads_or_useful_funcs import generate_new_id

from .quiz_problem import QuizProblem
from .quiz_submissions import QuizSubmission, QuizSubmissionAnswer

# Licensed under GPLv3 (as all other code in this repository is)


class QuizSolvingSession:
    __slots__ = (
        "__dict__",
        "user_id",
        "quiz_id",
        "special_id",
        "cache",
        "answer",
        "start_time",
        "_quiz",
        "guild_id",
        "answers",
        "is_finished",
        "expire_time",
    )

    def __init__(
        self, user_id: int, quiz_id: int, cache, guild_id: int, attempt_num: int
    ):
        self.user_id = user_id
        self.quiz_id = quiz_id
        self.special_id = generate_new_id()
        self.cache: "MathProblemCache" = cache
        self.answers: typing.Dict[int, QuizSubmissionAnswer] = {}
        self.start_time = time.time()
        self._quiz = self._get_quiz()
        self.guild_id = guild_id
        self.attempt_num = attempt_num
        self.is_finished = False

        try:
            self.expire_time: int = self.start_time + self._quiz.time_limit
        except AttributeError:
            raise NotImplementedError(
                "Quiz descriptions + other metadata needs to be fully implemented!"
            )

        # try:
        #    self.guild_id = self._quiz.guild_id
        # except MathProblemsModuleException as MPME:
        #    raise RuntimeError(
        #        "This quiz does not have a guild id, or it is None."
        #    ) from MPME

        self._reset()

    def _reset(self):
        """Reset myself"""
        pass

    def _get_quiz(self) -> "Quiz":
        """Get the quiz for this QuizSubmissionSession and return it"""
        return run(self.cache.get_quiz(self.quiz_id))

    def add_submission_answer(self, submission_answer: QuizSubmissionAnswer):
        """Add a submission answer to this session!"""
        problem_num = submission_answer.problem_id
        self.answers[problem_num] = submission_answer
        return submission_answer

    def _get_submission_answer(self, problem_num: int):
        """Get this submission answer or raise KeyError if it isn't found"""
        return self.answers[problem_num]

    @property
    def overtime(self: "QuizSolvingSession") -> bool:
        return time.time() > self.expire_time

    @property
    def done(self) -> bool:
        return self.is_finished or self.overtime

    @classmethod
    def better_init(
        cls,
        *,
        user_id: int,
        quiz_id: int,
        cache,
        attempt_num: int,
        is_finished: bool,
        answers: typing.List[QuizSubmissionAnswer],
        guild_id: int,
        start_time: int,
        expire_time: int,
        special_id: int
    ) -> "QuizSolvingSession":
        QuizSession: "QuizSolvingSession" = cls(
            cache=cache, quiz_id=quiz_id, user_id=user_id, attempt_num=attempt_num
        )
        QuizSession.is_finished = is_finished
        QuizSession.answers = answers
        QuizSession.guild_id = guild_id
        QuizSession._quiz = run(cache.get_quiz(quiz_id))
        QuizSession.start_time = start_time
        QuizSession.expire_time = expire_time
        QuizSession.special_id = special_id
        return QuizSession

    @classmethod
    def from_sqlite_dict(cls, dict: dict, cache) -> "QuizSolvingSession":
        """Convert a dict returned from sql into a QuizSolvingSession"""
        _quiz = run(cache.get_quiz(dict["quiz_id"]))
        return cls.better_init(
            cache=cache,
            start_time=dict["start_time"],
            expire_time=dict["expire_time"],
            user_id=dict["user_id"],
            quiz_id=dict["quiz_id"],
            guild_id=dict["guild_id"],
            answers=pickle.loads(dict["answers"]),  # TODO: don't use pickle because RCE
            special_id=dict["special_id"],
            attempt_num=dict["attempt_num"],
            is_finished=bool(dict["is_finished"]),
        )

    @classmethod
    def from_mysql_dict(cls, dict: dict, cache) -> "QuizSolvingSession":
        _quiz = run(cache.get_quiz(dict["quiz_id"]))
        return cls.better_init(
            cache=cache,
            start_time=dict["start_time"],
            user_id=dict["user_id"],
            quiz_id=dict["quiz_id"],
            guild_id=dict["guild_id"],
            expire_time=dict["expire_time"],
            answers=pickle.loads(dict["answers"]),
            special_id=dict["special_id"],
            attempt_num=dict["attempt_num"],
            is_finished=bool(dict["is_finished"]),
        )

    def to_dict(self) -> dict:
        return {
            "start_time": self.start_time,
            "user_id": self.user_id,
            "quiz_id": self.quiz_id,
            "guild_id": self.guild_id,
            "expire_time": self.expire_time,
            "is_finished": self.is_finished,
            "answers": [answer.to_dict() for answer in self.answers.values()],
        }

    async def update_self(self):
        """Update myself in SQL"""
        try:
            await self.cache.update_quiz_session(self.special_id, self)
        except QuizSessionNotFoundException:
            await self.cache.add_quiz_session(self)

    async def add_answer(self, answer_to_add: QuizSubmissionAnswer):
        """Add an answer"""
        if self.editable:
            raise QuizSessionOvertimeException("Quiz session overtime")
        assert isinstance(answer_to_add, QuizSubmissionAnswer)
        try:
            self.answers[answer_to_add.problem_id] = answer_to_add
        except IndexError:
            raise MathProblemsModuleException("Question number out of range")

        await self.update_self()

    @property
    def editable(self):
        return (not self.overtime) and (not self.is_final)

    async def modify_answer(self, answer_to_add: QuizSubmissionAnswer, index: int):
        if self.editable:
            raise QuizSessionOvertimeException("Quiz session overtime")

        assert isinstance(new, QuizSubmissionAnswer)
        try:
            self.answers[answer_to_add.problem_id] = new_answer
        except IndexError:
            raise MathProblemsModuleException("Question number out of range")
        await self.update_self()

    def get_answer(self, index: int) -> "QuizSubmissionAnswer":

        try:
            return self.answers[index]
        except IndexError:
            raise MathProblemsModuleException("Index out of range")

    def __copy__(self):

        # inspired from https://stackoverflow.com/questions/1500718/how-to-override-the-copy-deepcopy-operations-for-a-python-object#15774013
        # The next 3 lines are licensed under CC-BY-SA and the GPLv3
        obj = self.__class__.__new__(self.__class__)
        obj.__dict__.update(self.__dict__)
        return obj

    # After this, just the GPLv3 returns
