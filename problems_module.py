from types import *
from sqlite3 import *
from typing import *
import nextcord, json, warnings, dislash
from copy import deepcopy
from nextcord import *
import pickle, sqlite3
import sqldict #https://github.com/skylergrammer/sqldict/
def make_sql_table(kv_list, db_name, key_format="String", value_format="BLOB", serializer=pickle):
    #A simple fix from https://github.com/skylergrammer/sqldict/blob/master/sqldict/__init__.py
    #(I opened a pull request, but it has not been merged (the last commit was 5 years ago))
    with connect(db_name) as conn:
        cur = conn.cursor()
        try:
            cur.execute('''CREATE TABLE kv_store (key {} PRIMARY KEY, val  {})'''.format(key_format, value_format))
        except OperationalError:
            pass
        for k,v in kv_list:
            if serializer is None:
                cur.execute('INSERT OR IGNORE INTO kv_store VALUES (?,?)', (k, v))
            else:
                cur.execute('INSERT OR IGNORE INTO kv_store VALUES (?,?)', (k, serializer.dumps(v)))

# This is a module containing MathProblem and MathProblemCache objects. (And exceptions as well!) This may be useful outside of this discord bot so feel free to use it :) Just follow the MIT+GNU license
#Exceptions
class MathProblemsModuleException(Exception):
    "The base exception for problems_module."
class TooLongArgument(MathProblemsModuleException):
    '''Raised when an argument passed into MathProblem() is too long.'''
    pass
class TooLongAnswer(TooLongArgument):
    """Raised when an answer is too long."""
    pass
class TooLongQuestion(TooLongArgument):
    """Raised when a question is too long."""
    pass
class GuildAlreadyExistsException(MathProblemsModuleException):
    "Raised when MathProblemCache.add_empty_guild tries to run on a guild that already has problems."
    pass
class ProblemNotFoundException(MathProblemsModuleException):
    "Raised when a problem is not found."
    pass
class TooManyProblems(MathProblemsModuleException):
    "Raised when trying to add problems when there is already the maximum number of problems."
    pass
class ProblemNotFound(MathProblemsModuleException):
    "Raised when a problem isn't found"
    pass
class ProblemNotWrittenException(MathProblemsModuleException):
    "Raised when trying to grade a written problem but the problem is not graded"
    pass
class MathProblem:
    "For readability purposes :)"
    def __init__(self,question,answer,id,author,guild_id="null", voters=[],solvers=[], cache=None,answers=[]):
        if guild_id != "null" and not isinstance(guild_id, str):
            raise TypeError("guild_id is not an string")
        if not isinstance(id, int):
            raise TypeError("id is not an integer")
        if not isinstance(question, str):
            raise TypeError("question is not a string")
        if not isinstance(answer, str):
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
        if not isinstance(cache,MathProblemCache) and cache is not None:
            raise TypeError("_cache is not a MathProblemCache.")
        if len(question) > 250:
            raise TooLongQuestion(f"Your question is {len(question) - 250} characters too long. Questions may be up to 250 characters long.")
        self.question = question
        if len(answer) > 100:
            raise TooLongAnswer(f"Your answer is {len(question) - 100} characters too long. Answers may be up to 100 characters long.")
        self.answer = answer
        self.id = id
        self.guild_id = guild_id
        self.voters = voters
        self.solvers=solvers
        self.author=author
        self._cache = cache
        self.answers = answers
    def edit(self,question=None,answer=None,id=None,guild_id=None,voters=None,solvers=None,author=None, answers = None):
        """Edit a math problem."""
        if guild_id not in [None,"null"] and not isinstance(guild_id, int):
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
        if not isinstance(answers, list) and answers is not None:
            raise TypeError("answers is not a list")
        if id is not None or guild_id is not None or voters is not None or solvers is not None or author is not None:
            warnings.warn("You are changing one of the attributes that you should not be changing.", category=RuntimeWarning)
        if question is not None:
            if (self._cache is not None and len(question) > self._cache.max_question_length) or (len(question) > 250 and self._cache is None):
                if self._cache is not None:
                    raise TooLongQuestion(f"Your question is {len(question) - self._cache.max_question_length} characters too long. Questions may be up to {self._cache.max_question_length} characters long.")
                else:
                    raise TooLongQuestion(f"Your question is {len(question) - 250} characters too long. Questions may be up to 250 characters long.")
            self.question = question
        if (self._cache is not None and len(question) > self._cache.max_question_length) or (len(answer) > 100 and self._cache is None):
            if self._cache is not None:
                raise TooLongAnswer(f"Your answer is {len(question) - self._cache.max_answer_length} characters too long. Answers may be up to {self._cache.max_answer_length} characters long.")
            else:
                raise TooLongAnswer(f"Your answer is {len(question) - 100} characters too long. Answers may be up to 100 characters long.")
        for answer in range(len(answers)):
            if self._cache is not None:
                if len(answers[answer]) > 100:
                    raise TooLongAnswer(f"Answer #{answer} is {len(answers[answer])-100} characters too long. Answers can be up to a 100 characters long")
            else:
                if len(answers[answer]) > self._cache.max_answer_length:
                    raise TooLongAnswer(f"Answer #{answer} is {len(answers[answer]) - self._cache.max_answer_length} characters too long. Answers can be up to {self._cache.max_answer_length} characters long.")
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
    @classmethod
    def from_dict(_class,_dict):
        assert isinstance(_dict, dict)
        problem = _dict
        guild_id = problem["guild_id"]
        if guild_id == "null":
            guild_id = "null"
        else:
            guild_id = int(guild_id)
        problem2 = MathProblem(
            question=problem["question"],
            answer=problem["answer"],
            id = int(problem["id"]),
            guild_id = guild_id,
            voters = problem["voters"],
            solvers=problem["solvers"],
            author=problem["author"]
        )
        return problem2

    def convert_to_dict(self):
        """Convert self to a dictionary"""

        return {
            "question": self.question,
            "answer": self.answer,
            "id": str(self.id),
            "guild_id": str(self.guild_id),
            "voters": self.voters,
            "solvers": self.solvers,
            "author": self.author
        }
    def add_voter(self,voter):
        """Adds a voter. Voter must be a nextcord.User object or nextcord.Member object."""
        if not isinstance(voter,nextcord.User) and not isinstance(voter,nextcord.Member):
            raise TypeError("User is not a User object")
        if not self.is_voter(voter):
            self.voters.append(voter.id)
    def add_solver(self,solver):
        """Adds a solver. Solver must be a nextcord.User object or nextcord.Member object."""
        if not isinstance(solver,nextcord.User) and not isinstance(solver,nextcord.Member):
            raise TypeError("Solver is not a User object")
        if not self.is_solver(solver):
            self.solvers.append(solver.id)
    def get_answer(self):
        "Return my answer. This has been deprecated"
        return self.answer
    def get_answers(self):
        "Return my possible answers"
        return [self.answer, *self.answers] 
    def get_question(self):
        "Return my question."
        return self.question
    def check_answer_and_add_checker(self,answer,potentialSolver):
        "Checks the answer. If it's correct, it adds potentialSolver to the solvers."
        if not isinstance(potentialSolver,nextcord.User) and not isinstance(potentialSolver,nextcord.Member):
            raise TypeError("potentialSolver is not a User object")
        if self.check_answer(answer):
            self.add_solver(potentialSolver)
    def check_answer(self,answer):
        "Checks the answer. Returns True if it's correct and False otherwise."
        return answer in self.get_answers()
        
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
            raise TypeError("User is not actually a User")
        return User.id in self.get_voters()
    def get_solvers(self):
        "Returns self.solvers"
        return self.solvers
    def is_solver(self,User):
        "Returns True if user is a solver. False otherwise. User must be a nextcord.User or nextcord.Member object."
        if not isinstance(User,nextcord.User) and not isinstance(User,nextcord.Member):
            raise TypeError("User is not actually a User")
        return User.id in self.get_solvers()
    def __str__(self):
        "Return str(self) by converting it to a dictionary and converting the dictionary to a string"
        return str(self.convert_to_dict())
    def get_author(self):
        "Returns self.author"
        return self.author
    def is_author(self,User):
        "Returns if the user is the author"
        if not isinstance(User,nextcord.User) and not isinstance(User,nextcord.Member):
            raise TypeError("User is not actually a User")
        return User.id == self.get_author()
    def __eq__(self,other):
        "Return self==other"
        if not isinstance(self, type(other)):
            return False
        try:
            return self.question == other.question and other.answer == self.answer
        except:
            return False
    def __repr__(self):
        "A method that when called, returns a string, that when executed, returns an object that is equal to this one. Also implements repr(self)"
        return f"""problems_module.MathProblem(question={self.question},
        answer = {self.answer}, id = {self.id}, guild_id={self.guild_id},
        voters={self.voters},solvers={self.solvers},author={self.author},cache={None})""" # If I stored the problems, then there would be an infinite loop

class Quiz: 
    pass


class QuizMathProblem(MathProblem):
    "A class that represents a Quiz Math Problem"
    def __init__(self,question,answer,id,author,guild_id="null", voters=[],solvers=[], cache=None,answers=[],is_written=False,quiz: Quiz= None, max_score=-1):
        "A method that allows the creation of new QuizMathProblems"
        if not isinstance(quiz. Quiz):
            raise TypeError(f"quiz is of type {quiz.__class.__name}, not Quiz") # Here to help me debug
        
        super().__init__(question,answer,id,author,guild_id,voters,solvers,cache,answers) # 
        self.is_written = False
        self.quiz = quiz
        self.max_score = max_score
        self.min_score = 0

    def grade(self,ctx: Union(nextcord.ext.commands.Context, dislash.BaseInteraction), score):
        if not isinstance(ctx, (nextcord.ext.commands.Context, dislash.BaseInteraction)):
            raise TypeError

class MathProblemCache:
    def __init__(self,max_answer_length=100,max_question_limit=250,
    max_guild_problems=125,warnings_or_errors = "warnings",
    sql_dict_db_name = "problems_module.db",name="1",
    update_cache_by_default_when_requesting=True):
        sqldict.make_sql_table([], db_name = sql_dict_db_name)
        self.sql_dict_db_name = sql_dict_db_name
        if warnings_or_errors not in ["warnings", "errors"]:
            raise ValueError(f"warnings_or_errors is {warnings_or_errors}, not 'warnings' or 'errors'")
        if warnings_or_errors == "warnings":
            self.warnings = True
        else:
            self.warnings = False

        self.load_from_sql()
        self._max_answer = max_answer_length
        self._max_question = max_question_limit
        self._guild_limit = max_guild_problems
        self._sql_dict = sqldict.SqlDict(name=f"MathProblemCache{name}")
        self.update_cache_by_default_when_requesting=update_cache_by_default_when_requesting
    @property
    def max_answer_length(self):
        return self._max_answer
    @property
    def max_question_length(self):
        return self._max_question
    @property
    def max_guild_problems(self):
        return self._guild_limit
    #def load_from_sql(self):
    #    for item in self._sql_dict.keys():
    #        MathProblem.from_dict(self._sql_dict[item])


    def convert_to_dict(self):
        e = {}
        for guild_id in self._dict.keys():
            e[guild_id] = {}
            for problem_id in self._dict[guild_id].keys():
                print(guild_id, problem_id)
                e[guild_id][problem_id] = self.get_problem(guild_id,problem_id).convert_to_dict()
        return e
  
    def convert_dict_to_math_problem(self,problem):
        "Convert a dictionary into a math problem. It must be in the expected format."
        try:
            assert isinstance(problem,dict)
        except AssertionError:
            raise TypeError("problem is not actually a Dictionary")
        guild_id = problem["guild_id"]
        if guild_id == "null":
            guild_id = "null"
        else:
            guild_id = int(guild_id)
        problem2 = MathProblem(
            question=problem["question"],
            answer=problem["answer"],
            id = int(problem["id"]),
            guild_id = guild_id,
            voters = problem["voters"],
            solvers=problem["solvers"],
            author=problem["author"]
        )
        return problem2
    def update_cache(self):
        "Method revamped! This method updates the cache of the guilds, the guild problems, and the cache of the global problems"
        guild_problems = {}
        guild_ids = []
        global_problems = []
        for key in self._sql_dict.keys():
            p = key.partition(":")
            if p[0] not in guild_ids: #Update guild ids: Check if here
                guild_ids.append(p[0])
                guild_problems[p[0]] = {} #Also do this so I don't need to worry about keyerrors because it will update too
            #Check for guild problems
            #guaranteed to be a new problem :-)
            guild_problems[p[0]] = MathProblem.from_dict(self._sql_dict[key]) #Convert it to a math problem
        global_problems = guild_problems["null"] #contention            
        self.guild_problems = guild_problems
        self.guild_ids = guild_ids
        self.global_problems = global_problems
    def get_problem(self,guild_id,problem_id):
        "Gets the problem with this guild id and problem id"
        if not isinstance(guild_id, str):
            if self.warnings:
                warnings.warn("guild_id is not a string", category=RuntimeWarning)
            else:
                raise TypeError("guild_id is not a string")
        if not isinstance(problem_id,str):
            if self.warnings:
                warnings.warn("problem_id is not a string",category=RuntimeWarning)
            else:
                raise TypeError("problem_id is not a string")
        #Iterate through all problems! This takes O(N^2) time. However, nested SQLDicts don't exist. Any ideas? Please help :-)
        try:
            return self._sql_dict[f"{guild_id}:{problem_id}"]
        except:
            raise ProblemNotFound(f"*** No problem found with guild_id {guild_id} and problem_id {problem_id}!***")

    def get_guild_problems(self,Guild):
        """Gets the guild problems! Guild must be a Guild object. If you are trying to get global problems, use get_global_problems."""
        if self.update_cache_by_default_when_requesting:
            self.update_cache()
        return self.guild_problems[Guild.id]
        
    def get_global_problems(self):
        "Returns global problems"
        if self.update_cache_by_default_when_requesting:
            self.update_cache()
        return self.global_problems
    def add_empty_guild(self,Guild):
        "Adds an dictionary that is empty for the guild. Guild must be a nextcord.Guild object"
        pass #No longer needed
        #if not isinstance(Guild, nextcord.Guild):
        #    raise TypeError("Guild is not actually a Guild")
        #try:
        #    if self._dict[str(Guild.id)] != {}:
        #        raise GuildAlreadyExistsException
        #except KeyError:
        #    self._dict[str(Guild.id)] = {}
        #    
        #self._dict[Guild.id] = {}
    def add_problem(self,guild_id,problem_id,Problem):
        "Adds a problem and returns the added MathProblem"
        if not isinstance(guild_id,str):
            if self.warnings:
                warnings.warn("guild_id is not a string.... this may cause an exception")
            else:
                raise TypeError("guild_id is not a string.")
        if not isinstance(problem_id,str):
            if self.warnings:
                warnings.warn("problem_id is not a string.... this may cause an exception")
            else:
                raise TypeError("problem_id is not a string.")
        if len(self.guild_problems[guild_id]) > self.max_guild_problems:
            raise TooManyProblems(f"There are already {self.max_guild_problems} problems!")
        if not isinstance(Problem,(MathProblem, dict)):
            raise TypeError("Problem is not a valid MathProblem object.")
        if isinstance(Problem,MathProblem):
            try:
                Problem = Problem.convert_to_dict()
            except Exception:
                raise MathProblemsModuleException("Not a valid problem!")
        else:
            try: # make sure this is a valid problem
                MathProblem.from_dict(Problem) # If this is invaid, then there will be a keyerror
            except KeyError:
                raise MathProblemsModuleException("Problem is not a valid problem")
        try:
            if self.get_problem(guild_id,problem_id) is not None:
                raise MathProblemsModuleException("Problem already exists")
        except BaseException as e:
            if not isinstance(e,KeyError):
                raise RuntimeError("Something bad happened... please report this! And maybe try to fix it?") from e
            
        self._sql_dict[f"{guild_id}:{problem_id}"] = Problem
#        if guild_id != 'null':
#            try:
#                if self._dict[guild_id] != {}:
#                    raise GuildAlreadyExistsException
#                else:
#                    self._dict[guild_id] = {}
#            except:
#                self._dict[guild_id] = {}
        
        return Problem
    def remove_problem(self,guild_id,problem_id):
        "Removes a problem. Returns the deleted problem"
        if not isinstance(guild_id, str):
            if self.warnings:
                warnings.warn("guild_id is not a string. There might be an error...", Warning)
            else:
                raise TypeError("guild_id is not a string")

        Problem = self.get_problem(guild_id,problem_id)
        with sqlite3.connect(self.sql_dict.name) as connection: # The sqldict does not implement deletion, so I have to do sql magic
            connection.cursor.execute(f"DELETE FROM {self._sql_dict.__tablename__} WHERE key = \"{str(guild_id)}:{str(problem_id)}")
        
        return Problem
    def remove_duplicate_problems(self):
        "Deletes duplicate problems"
        problemsDeleted = 0
        c = deepcopy(self._dict)
        d = deepcopy(c)
        for g1 in self._dict.keys():
            for p1 in self._dict[g1].keys():
                for g2 in c.keys():
                    for p3 in c[g2].keys():
                        if self._dict[g1][p1] == c[g2][p3] and not (g1 == g2 and p1 != p3):
                            try:
                                del d[g1][p1]
                            except KeyError:
                                continue
                            problemsDeleted += 1
        self._dict = d
        return problemsDeleted
    def get_guilds(self):
        if self.update_cache_by_default_when_requesting:
            self.update_cache()
        return self.guild_ids
    def __str__(self):
        raise NotImplementedError

main_cache = MathProblemCache(max_answer_length=100,max_question_limit=250,max_guild_problems=125,warnings_or_errors="errors")
def get_main_cache():
    "Returns the main cache."
    return main_cache
