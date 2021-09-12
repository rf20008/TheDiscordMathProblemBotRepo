<<<<<<< HEAD
import json
numFileSavers=0
class FileSaver:
  def __init__(self,name=None,enabled=False,printSuccessMessagesByDefault=False,math_problems_file_name="math_problems.json",guild_math_problems_file_name="guild_math_problems.json",trusted_users_file_name="trusted_users.txt",vote_threshold_file_name="vote_threshold.txt"):
=======
import json, problems_module
numFileSavers=0
class FileSaver:
  "A class that save files"
  def __init__(self,name=None,enabled=False,printSuccessMessagesByDefault=False,):
>>>>>>> 830e1461955a931eb77d437c428d93c8961b2221
    """Creates a new FileSaver object."""
    global numFileSavers
    numFileSavers+=1
    if name == None:
      name = "FileSaver" + str(numFileSavers)
    self.id = numFileSavers
    self.printSuccessMessagesByDefault=printSuccessMessagesByDefault
    self.enabled=True
<<<<<<< HEAD
    self.math_problems_file_name=math_problems_file_name
    self.guild_math_problems_file_name=guild_math_problems_file_name
    self.trusted_users_file_name=trusted_users_file_name
    self.vote_threshold_file_name=vote_threshold_file_name
=======
>>>>>>> 830e1461955a931eb77d437c428d93c8961b2221
    self.name=name
  def __str__(self):
    return self.name
  def enable(self):
    "Enables self."
    self.enabled=True
  def disable(self):
    "Disables self"
    self.enabled=False
  def load_files(self,printSuccessMessages=None):
    "Loads files from file names specified in self.__init__."
    if not self.enabled:
      raise RuntimeError("I'm not enabled! I can't load files!")
    trusted_users=[]
    if printSuccessMessages or printSuccessMessages==None and self.printSuccessMessagesByDefault:
<<<<<<< HEAD
      print(f"{str(self)}: Attempting to load guild_math_problems_dict from {self.guild_math_problems_file_name}, vote_threshold from {self.vote_threshold_file_name}, trusted_users_list from {self.trusted_users_file_name}, and math_problems_dict from {self.math_problems_file_name}...")
    with open("math_problems.json", "r") as file:
      mathProblems = json.load(fp=file)
=======
      print(f"{str(self)}: Attempting to load vote_threshold from vote_threshold.txt, trusted_users_list from trusted_users.txt, and math_problems  from math_problems.json...")
    problems_module.get_main_cache().update_cache()
>>>>>>> 830e1461955a931eb77d437c428d93c8961b2221
    with open("trusted_users.txt", "r") as file2:
      for line in file2:
        trusted_users.append(int(line))
    with open("vote_threshold.txt", "r") as file3:
      for line in file3:
        vote_threshold = int(line)
        
    with open("guild_math_problems.json", "r") as file4:
      guildMathProblems = json.load(fp=file4)
    if printSuccessMessages or printSuccessMessages==None and self.printSuccessMessagesByDefault:
      print(f"{self.name}: Successfully loaded files.")
<<<<<<< HEAD
    return {"guildMathProblems":guildMathProblems,"trusted_users":trusted_users,"mathProblems":mathProblems,"vote_threshold":vote_threshold}
=======
    return {"guildMathProblems":guildMathProblems,"trusted_users":trusted_users,"vote_threshold":vote_threshold}
>>>>>>> 830e1461955a931eb77d437c428d93c8961b2221
  def save_files(self,printSuccessMessages=None,guild_math_problems_dict={},vote_threshold=3,math_problems_dict={},trusted_users_list={}):
    "Saves files to file names specified in __init__."
    if not self.enabled:
      raise RuntimeError("I'm not enabled! I can't load files!")
    if printSuccessMessages or printSuccessMessages==None and self.printSuccessMessagesByDefault:
<<<<<<< HEAD
      print(f"{str(self)}: Attempting to save guild_math_problems_dict to {self.guild_math_problems_file_name}, vote_threshold to {self.vote_threshold_file_name}, trusted_users_list to  {self.trusted_users_file_name}, and math_problems_dict to {self.math_problems_file_name}...")
    with open("math_problems.json", "w") as file:
      file.write(json.dumps(math_problems_dict))
=======
      print(f"{str(self)}: Attempting to save math problems vote_threshold to vote_threshold.txt, trusted_users_list to  trusted_users.txt...")
    problems_module.get_main_cache().update_file_cache()
>>>>>>> 830e1461955a931eb77d437c428d93c8961b2221
    with open("trusted_users.txt", "w") as file2:
      for user in trusted_users_list:
        file2.write(str(user))
        file2.write("\n")
        #print(user)
  
    with open("vote_threshold.txt", "w") as file3:
      file3.write(str(vote_threshold))
    with open("guild_math_problems.json", "w") as file4:
      e=json.dumps(obj=guild_math_problems_dict)
      file4.write(e)
    if printSuccessMessages or printSuccessMessages==None and self.printSuccessMessagesByDefault:
      print(f"{self.name}: Successfully saved files.")
  def change_name(self,new_name):
    self.name=new_name
  def my_id(self):
    return self.id
  def goodbye(self):
    print(str(self)+": Goodbye.... :(")
    del self