import nextcord

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
  def edit(self,question=None,answer=None,id=None,guild_id=None,voters=None,solvers=None):
    """Edit a math problem."""
    if question != None:
        raise TooLongQuestion(f"Question {question} is too long (250+ characters)")
      self.question = question
    if answer != None:
      if len(answer) > 100:
        raise TooLongAnswer(f"Answer {answer} is too long.")
      self.answer = answer
    if id != None:
      self.id = id
    if guild_id != None:
      self.guild_id = guild_id
    if voters != None:
      self.voters = voters
    if solvers != None:
      self.solvers = solvers
  def convert_to_dict(self):
    """Convert self to a dictionary"""
    return {
      "question": self.question,
      "answer": self.answer,
      "id": self.id,
      "guild_id": self.guild_id,
      "voters": self.voters,
      "solvers": self.solvers
    }
  def add_voters(self,voter):
    """Adds a voter. Voter must be a nextcord.User object or nextcord.Member object."""
    if not isinstance(voter,nextcord.User) and not isinstance(voter,nextcord.Member):
      raise TypeError
    self.voters.append(voter.id)
  def add_solver(self,solver):
    """Adds a solver. Solver must be a nextcord.User object or nextcord.Member object."""
    if not isinstance(solver,nextcord.User) and not isinstance(solver,nextcord.Member):
      raise TypeError
    self.solvers.append(solver.id)
    