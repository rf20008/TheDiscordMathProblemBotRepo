import json

from . import problems_module

numFileSavers = 0


class FileSaver:
    """A class that saves files"""

    def __init__(
        self,
        name=None,
        enabled=False,
        printSuccessMessagesByDefault=False,
    ):
        """Creates a new FileSaver object."""
        global numFileSavers
        numFileSavers += 1
        if name is None:
            name = "FileSaver" + str(numFileSavers)
        self.id = numFileSavers
        self.printSuccessMessagesByDefault = printSuccessMessagesByDefault
        self.enabled = True
        self.name = name

    def __str__(self):
        return self.name

    def enable(self):
        """Enables self."""
        self.enabled = True

    def disable(self):
        """Disables self"""
        self.enabled = False

    def load_files(self, main_cache, printSuccessMessages=None):
        """Loads files from file names specified in self.__init__."""
        if not isinstance(main_cache, problems_module.MathProblemCache):
            raise TypeError("main_cache is not a MathProblemCache.")
        if not self.enabled:
            raise RuntimeError("I'm not enabled! I can't load files!")
        trusted_users = []
        if (
            printSuccessMessages
            or printSuccessMessages is None
            and self.printSuccessMessagesByDefault
        ):
            print(
                f"{str(self)}: Attempting to load vote_threshold from vote_threshold.txt, trusted_users_list from trusted_users.txt, and math_problems  from math_problems.json..."
            )
        with open("math_problems.json", "r") as file:
            mathProblems = json.load(fp=file)

        with open("trusted_users.txt", "r") as file2:
            for line in file2:
                trusted_users.append(int(line))
        vote_threshold = False
        with open("vote_threshold.txt", "r") as file3:
            for line in file3:
                if str(
                    line
                ).isnumeric():  # Make sure that an empty string does not become the new vote threshold
                    vote_threshold = int(line)
        if not vote_threshold:
            raise RuntimeError("vote_threshold not given!!")

        with open("guild_math_problems.json", "r") as file4:
            guildMathProblems = json.load(fp=file4)
        if (
            printSuccessMessages
            or printSuccessMessages is None
            and self.printSuccessMessagesByDefault
        ):
            print(f"{self.name}: Successfully loaded files.")

        return {
            "guildMathProblems": guildMathProblems,
            "trusted_users": trusted_users,
            "mathProblems": mathProblems,
            "vote_threshold": vote_threshold,
        }

    def save_files(
        self,
        main_cache=None,
        printSuccessMessages=None,
        guild_math_problems_dict={},
        vote_threshold=3,
        math_problems_dict={},
        trusted_users_list={},
    ):
        """Saves files to file names specified in __init__."""

        if not isinstance(main_cache, problems_module.MathProblemCache):
            raise TypeError("main_cache is not a MathProblemCache.")
        if not self.enabled:
            raise RuntimeError("I'm not enabled! I can't load files!")
        if (
            printSuccessMessages
            or printSuccessMessages is None
            and self.printSuccessMessagesByDefault
        ):
            print(
                f"{str(self)}: Attempting to save math problems vote_threshold to vote_threshold.txt, trusted_users_list to  trusted_users.txt..."
            )
        # main_cache.update_file_cache() #Removed method

        with open("trusted_users.txt", "w") as file2:
            for user in trusted_users_list:
                file2.write(str(user))
                file2.write("\n")
                # print(user)

        with open("vote_threshold.txt", "w") as file3:
            file3.write(str(vote_threshold))
        with open("guild_math_problems.json", "w") as file4:
            e = json.dumps(obj=guild_math_problems_dict)
            file4.write(e)
        if (
            printSuccessMessages
            or printSuccessMessages is None
            and self.printSuccessMessagesByDefault
        ):
            print(f"{self.name}: Successfully saved files.")

    def change_name(self, new_name):
        self.name = new_name

    def my_id(self):
        return self.id

    def goodbye(self):
        print(str(self) + ": Goodbye.... :(")
        del self
