# This is a module containing MathProblem, MathProblemHandler, and MathProblemCache objects. (And exceptions as well!)

class TooLongArgument(Exception):
  '''Raised when an argument passed into MathProblem() is too long.'''
  pass
class TooLongAnswer(TooLongArgument):
  """Raised when an answer is too long."""
  pass
class TooLongQuestion(TooLongArgument):
  """Raised when a question is too long."""

class MathProblem:
  def __init__(self,question,answer,id,guild_id=None,voters=[],solvers=[]):
    if guild_id != None and not isinstance(guild_id, int):
      raise TypeError
    if len(question) > 250:
      raise TooLongQuestion(f"Question {question} is too long (250+ characters)")
    self.question = question
    if len(answer) > 100:
      raise TooLongAnswer(f"Answer {answer} is too long.")
    self.answer = answer
    self.id = id
    self.guild_id = guild_id
    self.voters = voters
    self.solvers=solvers
  def edit(self,question=None,answer=None,id,guild_id=None,voters=None,solvers=None):
    """Edit a math problem."""
    if question != None:
      self.question = question
    if answer != None:
      if len(answer) > 100:
        raise TooLongAnswer(f"Answer {answer} is too long.")
      self.answer = answer