"""Licensed under GPLv3"""
import aiomysql


class MathProblemsModuleException(Exception):
    """The base exception for problems_module."""

    pass


class TooLongArgument(MathProblemsModuleException):
    """Raised when an argument passed into MathProblem() is too long."""

    pass


class TooLongAnswer(TooLongArgument):
    """Raised when an answer is too long."""

    pass


class TooLongQuestion(TooLongArgument):
    """Raised when a question is too long."""

    pass


class GuildAlreadyExistsException(MathProblemsModuleException):
    """Raised when MathProblemCache.add_empty_guild tries to run on a guild that already has problems."""

    pass


class TooManyProblems(MathProblemsModuleException):
    """Raised when trying to add problems when there is already the maximum number of problems."""

    pass

class ThingNotFound(KeyError, IndexError, MathProblemsModuleException):
    """Raised when a thing is not found"""
    pass


class ProblemNotFound(ThingNotFound):
    """Raised when a problem isn't found"""

    pass


class ProblemNotFoundException(ProblemNotFound):
    """Raised when a problem is not found."""

    pass


class ProblemNotWrittenException(ThingNotFound):
    """Raised when trying to grade a written problem but the problem is not a written problem"""

    pass


class QuizAlreadySubmitted(MathProblemsModuleException):
    """Raised when trying to submit a quiz that has already been submitted"""

    pass


class SQLException(MathProblemsModuleException):
    """Raised when an error happens relating to SQL!"""

    pass


class MySQLException(SQLException, aiomysql.Error):
    """A generic MYSQL exception"""

    def __init__(self, message, base_error):
        SQLException.__init__(self, message)
        self.base_error = base_error


class QuizNotFound(ThingNotFound):
    """Raised when a quiz isn't found"""

    pass

class FormatException(KeyError, MathProblemsModuleException):
    """Raised when something is not formatted correctly"""
    pass
class IsRowException(FormatException):
    """Raised when expecting a dictionary but got a row instead."""

    pass


class TooMuchUserDataException(FormatException):
    """Raised when there is too much user data!"""

    pass


class UserDataNotExistsException(ThingNotFound):
    """Raised by MathProblemCache.set_user_data when user data does not exist!"""

    pass


class TooManyQuizzesException(MathProblemsModuleException):
    """Raised a guild has too many quizzes"""

    def __init__(self, num_quizzes: int):
        message: str = (
            f"The guild already has {num_quizzes} quizzes, which is too much!"
        )
        super().__init__(message)


class QuizSessionNotFoundException(ThingNotFound):
    """Raised when trying to find quiz sessions but they are not found"""

    pass


class QuizSessionOvertimeException(MathProblemsModuleException):
    """Raised when a quiz session is attempted to be modified but they ran out of time"""

    pass


class QuizDescriptionNotFoundException(ThingNotFound):
    """Raised when Quiz Description is not found"""

    pass


class InvalidDictionaryInDatabaseException(FormatException):
    """Raised when a dictionary is expected in the database as part of a string data type, but it could not be compiled"""

    def __init__(self, msg: str):
        super().__init__(msg)

    @classmethod
    def from_invalid_data(cls, invalid_data: str):
        return cls(
            f"""I expected a dictionary here, but instead I got {invalid_data} -- OH NO!"""
        )


class PMDeprecationWarning(DeprecationWarning):
    """Raised when someone tries to use a feature of the problems module that is deprecated"""
    pass

class LockedCacheException(RuntimeError):
    """Raised when an operation is done on a locked RedisCache"""
    pass
