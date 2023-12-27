import asyncio
import subprocess
from sys import executable
from typing import NoReturn

import disnake

# from .custom_bot import TheDiscordMathProblemBot


## This code is licensed under GPLv3, like all the other Python code in this repo
## TODO: fix this
RESTART_MESSAGE_WARNING = (
    "The bot will automatically restart to apply an update after 20 seconds. "
    "It should be back in a few seconds!"
)
RESTART_MESSAGE_FINAL_WARNING = (
    "The bot is automatically restarting! It should be back in a few seconds!"
)


class RestartTheBot:
    def __init__(self, bot: "TheDiscordMathProblemBot"):
        self.bot = bot

    async def notify_before_restarting(self) -> None:
        warnings.warn(category=RuntimeWarning, message="This may not do what it actually does")
        channel = await self.bot.fetch_channel(self.bot.constants.BOT_RESTART_CHANNEL)
        await channel.send(RESTART_MESSAGE_WARNING)
        await asyncio.sleep(20)
        await channel.send(RESTART_MESSAGE_FINAL_WARNING)

    async def restart_the_bot(self) -> NoReturn:
        print("The bot is now restarting!")
        await self.notify_before_restarting()
        await self.actual_restart()

    async def actual_restart(self) -> NoReturn:
        await asyncio.sleep(3)
        await self.bot.close()
        await asyncio.sleep(5)
        ## I learned that starting a new process that starts a new copy of the bot is better than starting the bot directly
        # the hard way

        command = executable + " actual_restarter.py" #
        subprocess.run(command.split(), capture_output=True, shell=True)
        os._exit(1)
