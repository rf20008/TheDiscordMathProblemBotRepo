import json, problems_module
numFileSavers=0
class FileSaver:
  def __init__(self,name=None,enabled=False,printSuccessMessagesByDefault=False,):
    """Creates a new FileSaver object."""
    global numFileSavers
    numFileSavers+=1
    if name == None:
      name = "FileSaver" + str(numFileSavers)
    self.id = numFileSavers
    self.printSuccessMessagesByDefault=printSuccessMessagesByDefault
    self.enabled=True
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
      print(f"{str(self)}: Attempting to load guild_math_problems_dict from {self.guild_math_problems_file_name}, vote_threshold from {self.vote_threshold_file_name}, trusted_users_list from {self.trusted_users_file_name}, and math_problems_dict from {self.math_problems_file_name}...")
    problems_module.get_main_cache().update_cache()
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
    return {"guildMathProblems":guildMathProblems,"trusted_users":trusted_users,"vote_threshold":vote_threshold}
  def save_files(self,printSuccessMessages=None,guild_math_problems_dict={},vote_threshold=3,math_problems_dict={},trusted_users_list={}):
    "Saves files to file names specified in __init__."
    if not self.enabled:
      raise RuntimeError("I'm not enabled! I can't load files!")
    if printSuccessMessages or printSuccessMessages==None and self.printSuccessMessagesByDefault:
      print(f"{str(self)}: Attempting to save guild_math_problems_dict to {self.guild_math_problems_file_name}, vote_threshold to {self.vote_threshold_file_name}, trusted_users_list to  {self.trusted_users_file_name}, and math_problems_dict to {self.math_problems_file_name}...")
    problems_module.get_main_cache().update_file_cache()
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