import nextcord, json

# This is a module containing MathProblem, MathProblemHandler, and MathProblemCache objects. (And exceptions as well!)

class TooLongArgument(Exception):
  '''Raised when an argument passed into MathProblem() is too long.'''
  pass
class TooLongAnswer(TooLongArgument):
  """Raised when an answer is too long."""
  pass
class TooLongQuestion(TooLongArgument):
  """Raised when a question is too long."""

class GuildAlreadyExistsException(Exception):
  "Raised when MathProblemCache.add_empty_guild tries to run on a guild that already has problems."

class MathProblem:
  "For readability purposes :)"
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
    if self.guild_id == None:
      guild_id = "None"
    else:
      guild_id = self.guild_id

    return {
      "question": self.question,
      "answer": self.answer,
      "id": self.id,
      "guild_id": guild_id
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
  def get_answer(self):
    "Return my answer."
    return self.answer
  def get_question(self):
    "Return my question."
    return self.question
  def check_answer_and_add_checker(self,answer,potentialSolver):
    "Checks the answer. If it's correct, it adds potentialSolver to the solvers."
    if not isinstance(potentialSolver,nextcord.User) and not isinstance(potentialSolver,nextcord.Member):
      raise TypeError
    if self.check_answer(answer):
      self.add_solver(potentialSolver)
  def check_answer(self,answer):
    "Checks the answer. Returns True if it's correct and False otherwise."
    return answer == self.get_answer()
  def my_id(self):
    "Returns id & guild_id in a list. id is first and guild_id is second."
    return [self.id, self.guild_id]
  def get_voters(self):
    "Returns self.voters"
    return self.voters
  def get_num_voters(self):
    "Returns the number of solvers."
    return len(self.get_voters())
  def is_voter(self,User):
    "Returns True if user is a voter. False otherwise. User must be a nextcord.User or nextcord.Member object."
    if not isinstance(User,nextcord.User) and not isinstance(User,nextcord.Member):
      raise TypeError
    return User.id in self.get_voters()
  def get_solvers(self):
    "Returns self.solvers"
    return self.solvers
  def is_solver(self,User):
    "Returns True if user is a solver. False otherwise. User must be a nextcord.User or nextcord.Member object."
    if not isinstance(User,nextcord.User) and not isinstance(User,nextcord.Member):
      raise TypeError
    return User.id in self.get_solvers()
  def __str__(self):
    "Return str(self) by converting it to a dictionary and converting the dictionary to a string"
    return str(self.convert_to_dict)

class MathProblemCache:
   def __init__(self):
    self._dict = {}
    self.update_cache()
  def convert_dict_to_math_problem(self,problem: dict) -> MathProblem:
    "Convert a dictionary into a math problem. It must be in the expected format."
    guild_id = problem["guild_id"]
    if guild_id == "None":
      guild_id = None 
  
    problem2 = MathProblem(
      question=problem["question"],
      answer=problem["answer"],
      id = problem["id"]
      guild_id = guild_id,
      voters = problem["voters"],
      solvers=problem["solvers"]
    )
    return problem2
  def update_cache(self):
    "This method replaces the new cache with the cache from the file."
    with open("math_problems.json","r") as file:
      dict = json.loads("\n".join(fp))
    for item in dict.keys():
      self._dict[item] = {}
      for item2 in dict[item].keys():
        self._dict[item][item2] = self.convert_dict_to_math_problem(dict[item][item2])
   def update_file_cache(self):
    "This method updates the file cache."
    thing_to_write = ""
    for guild_id in self._dict.keys():
      thing_to_write += "{" + str(guild_id) + ": " 
      for problem_id in self._dict[guild_id].keys():
        thing_to_write += str(problem_id) + ": "
        thing_to_write += str(self._dict[guild_id][problem_id])
        thing_to_write += ","
      thing_to_write = thing_to_write.remove_suffix(",")    
      thing_to_write += "},"
    thing_to_write.remove_suffix(",")
    thing_to_write += "}"
    with open("math_problems.json", "w") as file:
      file.write(thing_to_write)
  def get_problem(self,guild_id,problem_id):
    "Gets the problem with this guild id and problem id"
    return self._dict[guild_id][problem_id]
  def fetch_problem(self,guild_id,problem_id):
    "Reloads the cache with the file and then loads the problem."
    self.update_cache()
    return self.get_problem(guild_id, problem_id)
  def get_guild_problems(self,Guild):
    """Gets the guild problems! Guild must be a Guild object. If you are trying to get global problems, use get_global_problems."""
    if not isinstance(Guild, nextcord.Guild):
      raise TypeError
    return self._dict[Guild.id].values()
  def get_global_problems(self):
    "Returns global problems"
    return self._dict[None].values()
  def add_empty_guild(self,Guild):
    "Adds an dictionary that is empty for the guild. Guild must be a nextcord.Guild object"
    if not isinstance(Guild, nextcord.Guild):
      raise TypeError
    try:
      if self._dict[Guild.id] != {}:
        raise GuildAlreadyExistsException
    except:
      pass
      
    self._dict[Guild.id] = {}
  def add_problem(self,guild_id,problem_id,Problem):
    "Adds a problem and returns the added MathProblem"
    if not isinstance(Problem,(MathProblem, dict)):
      raise TypeError("Problem is not a valid MathProblem object.")
    if isinstance(Problem,dict):
      try:
        Problem = self.convert_dict_to_math_problem(Problem)
      except KeyError:
        raise Exception("Not a valid problem!")
    if guild_id != None:
      try:
        if self._dict[guild_id] != {}:
          raise GuildAlreadyExistsException
        else:
          self._dict[guild_id] = {}
      except:
        self._dict[guild_id] = {}
    self._dict[guild_id][problem_id] = Problem
    return Problem
  def remove_problem(self,guild_id,problem_id):
    "Removes a problem. Returns the deleted problem"
    Problem = self._dict[guild_id][problem_id]
    del self._dict[guild_id][problem_id]
    return Problem

