[![Powered by Nextcord](https://custom-icon-badges.herokuapp.com/badge/-Powered%20by%20Nextcord-0d1620?logo=nextcord)](https://github.com/nextcord/nextcord "Powered by Nextcord Python API Wrapper")
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Frf20008%2FTheDiscordMathProblemBotRepo.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Frf20008%2FTheDiscordMathProblemBotRepo?ref=badge_shield)

# If you run into issues
If you run into any issues create an issue or DM me (ay136416#2707)). 

# Contribute :-)

If you open a PR/Issue, I'll look at it and maybe merge it! 
A few guidelines:
1) Use the main branch, not master
2) If you are pull requesting to my bot directly into the main branch, please make sure your code works!
3) If you are pull requesting to my bot via the beta branch, please make sure your code works, but it is okay if it doesn't (for now), but later, not so much
4) This bot is coded using OOP and abstraction, so if you want to add a new feature or change an existing one, please keep this in mind.
5) main.py is used to run the bot! helpful_modules include essential elements of the bot, but are not exposed to the user. cogs is the cogs!
6) No syntax errors, please!
7) You should lint your code.
8) Follow common sense

# Invite my bot!

Recommended invite: https://discord.com/api/oauth2/authorize?client_id=845751152901750824&permissions=2147568640&scope=bot%20applications.commands

# Documentation

https://github.com/rf20008/TheDiscordMathProblemBotRepo/tree/master/docs

# Attribution
https://stackoverflow.com/a/21901260 for the get_git_revision_hash :-)
nextcord + discord devs for their libraries
SQLDict: https://github.com/skylergrammer/sqldict

# DISCLAIMER

My bot is just a platform for storing problems. If someone submits a copyrighted problem, I'm not responsible, but they are. You can look up who submitted a problem using /show_problem_info.
(If you need to, you can submit a request using /submit_a_request)


# Self-host my bot
My code is open source, so you can! There are bugs, so you should probably help me instead. I won't stop you from self-hosting though.

(I'd prefer if you didn't, though)


## Steps
(This assumes you already have knowledge of the command line and how to make a new discord application)
If you don't, you can either help me with my code (if you want to modify the code and help everyone out) or invite my bot.
No privileged intents are required (the bot has been designed to not require privileged intents, but this is causing some non-essential features to be not-so-great)
1. Create a new Discord application with a bot user. Save the token (you will need it later)
2. Update Python to 3.9/3.10
3. Create a venv (execute ``python3.10 -m venv /path/to/new/virtual/environment``)
4. move to your new venv (use the cd command)
5. Install poetry, a dependency installer (``pip3 install git+https://github.com/python-poetry/poetry.git``). You can also optionally install it outside.
6. Clone my repo (``git clone https://github.com/rf20008/TheDiscordMathProblemBotRepo``)
7. move to the new directory containing the repository you cloned (which should be this one. The folder name is the same name as the repository name)
8. Create a .env file inside the repository folder. Inside it, you need to put 
``DISCORD_TOKEN = `<your discord token>` `` (Replace `<your discord token>`) with the discord bot token you got from the bot user you made.
9. Run the main.py file (```python3.10 main.py```) Don't use the -O / -OO option (assert statements are necessary to run the bot, and they only run if \_\_debug\_\_ is true, which is not the case if the -O option is selected)
10. Invite the bot bot (use the invite link, but replace the client_id field with your bot's client id)
## Update the bot with my changes

1. Run ``cd path/to/your/repo/``
2. Run ``git pull`` (updates the repo)
3. If there are any merge conflicts, please fix them. Then do step 2. If there are no merge conflicts, skip this step
4. Stop your bot! And then re-start it again


## License
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Frf20008%2FTheDiscordMathProblemBotRepo.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Frf20008%2FTheDiscordMathProblemBotRepo?ref=badge_large)