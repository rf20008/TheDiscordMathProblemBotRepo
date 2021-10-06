import random, os, warnings, threading, copy, nextcord, subprocess
import dislash, traceback
import nextcord.ext.commands as nextcord_commands
from cooldowns import check_for_cooldown
from dislash import InteractionClient, Option, OptionType, NotOwner, OptionChoice
from time import sleep, time, asctime

from custom_embeds import ErrorEmbed, SuccessEmbed
problems_module = None
FileSaver = None
successEmbed = None
errorEmbed = None
the_documentation_file_loader = None
slash = None
class DeveloperCommands(nextcord_commands.Cog):
    def __init__(self, bot):
        self.bot=bot
    @slash_command(name="force_load_files",description="Force loads files to replace dictionaries. THIS WILL DELETE OLD DICTS!")
    async def force_load_files(self,ctx):
        "Forcefully load files"
        global guildMathProblems, trusted_users,vote_threshold
        await check_for_cooldown(ctx,"force_load_files",5)

        if ctx.author.id not in self.bot.trusted_users:
            await ctx.reply(ErrorEmbed("You aren't trusted and therefore don't have permission to forceload files."))
            return
        try:
            FileSaver3 = FileSaver(enabled=True,printSuccessMessagesByDefault=False)
            FileSaverDict = FileSaver3.load_files(self.bot.main_cache)
            (guildMathProblems,trusted_users,vote_threshold) = (FileSaverDict["guildMathProblems"],FileSaverDict["trusted_users"],FileSaverDict["vote_threshold"])
            FileSaver3.goodbye()
            await ctx.reply(embed=SuccessEmbed("Successfully forcefully loaded files!"))
            return
        except RuntimeError:
            await ctx.reply(embed=ErrorEmbed("Something went wrong..."))
            return
    @slash_command(name="force_save_files",description="Forcefully saves files (can only be used by trusted users).")
    async def force_save_files(self,ctx):
        "Forcefully saves files."
        await check_for_cooldown(ctx,"force_save_files",5)
        if ctx.guild != None and ctx.guild.id not in self.bot.main_cache.get_guilds():
            self.bot.main_cache.add_empty_guild(ctx.guild)
        if ctx.author.id not in self.bot.trusted_users:
            await ctx.reply(embed=ErrorEmbed("You aren't trusted and therefore don't have permission to forcesave files."))
            return
        try:
            FileSaver2 = FileSaver(enabled=True)
            FileSaver2.save_files(self.bot.main_cache,True,guildMathProblems,vote_threshold,{},trusted_users)
            FileSaver2.goodbye()
            await ctx.reply(embed=SuccessEmbed("Successfully saved 4 files!"))
        except RuntimeError as exc:
            await ctx.reply(embed=ErrorEmbed("Something went wrong..."))
            raise exc
    @slash_command(name="raise_error",
                     description = "⚠ This command will raise an error. Useful for testing on_slash_command_error", 
    options=[Option(name="error_type",description = "The type of error", choices=[
        OptionChoice(name="Exception",value="Exception"),
        OptionChoice(name="UserError", value = "UserError")
        ],required=True), Option(name="error_description", description="The description of the error",
                             type=OptionType.STRING,
                             required=False)])
    async def raise_error(self,ctx, error_type,error_description = None):
        "Intentionally raise an Error. Useful for debugging... :-)"
        await check_for_cooldown(ctx,"raise_error",5)
        if ctx.author.id not in self.bot.trusted_users:
            await ctx.send(embed=ErrorEmbed(
                f"⚠ {ctx.author.mention}, you do not have permission to intentionally raise errors for debugging purposes.",
                custom_title="Insufficient permission to raise errors."))
            return
        if error_description == None:
            error_description = f"Manually raised error by {ctx.author.mention}"    
        if error_type == "Exception":
            error = Exception(error_description)
        elif error_type == "UserError":
            error=UserError(error_description)
        await ctx.send(embed=SuccessEmbed(
            f"Successfully created error: {str(error)}. Will now raise the error.",
                                          successTitle="Successfully raised error."))
        raise error
    @slash_command(name="documentation",description = "Returns help!", 
    options=[Option(name="documentation_type", description = "What kind of help you want", choices= [
        OptionChoice(name = "documentation_link",value="documentation_link"),
        OptionChoice(name="command_help", value="command_help"),
        OptionChoice(name="function_help", value="function_help"),
        ],required=True),
        Option(name="help_obj", description = "What you want help on", required=True,type=OptionType.STRING)])
    async def documentation(self,ctx,documentation_type, help_obj):
        "Prints documentation :-)"
        await check_for_cooldown(ctx,"documentation",0.1)
        if documentation_type == "documentation_link":
            await ctx.reply(embed=SuccessEmbed(
                f"""<@{ctx.author.id}> [Click here](https://github.com/rf20008/TheDiscordMathProblemBotRepo/tree/master/docs) for my documentation.
        """),ephemeral=True)
            return None
        documentation_loader = the_documentation_file_loader.DocumentationFileLoader()
        try:
            _documentation =d.get_documentation(
                {"command_help":"docs/commands-documentation.md",
            "function_help":"docs/misc-non-commands-documentation.md"}[documentation_type], help_obj)
        except DocumentationNotFound as e:
            if isinstance(e,DocumentationFileNotFound):
                await ctx.reply(embed=ErrorEmbed("Documentation file was not found. Please report this error!"))
                return
            await ctx.reply(embed=ErrorEmbed(str(e)))
            return
        await ctx.reply(_documentation)

    @slash_command(name="debug",description="Help for debugging :-)",options=[
      Option(name="raw",description="raw debug data?",type=OptionType.BOOLEAN,required=False),
      Option(name="send_ephermally",description="Send the debug message ephermally?",type=OptionType.BOOLEAN,required=False)
    ])
    async def debug(self,ctx,raw=False,send_ephermally=True):
        "Provides helpful debug information :-)"
        await check_for_cooldown(ctx,"debug",0.1,is_global_cooldown=False)
        guild = ctx.guild
        if ctx.guild is None:
            await ctx.reply("This command can only be ran in servers!")
            return
        me = guild.me
        my_permissions = me.guild_permissions
        debug_dict = {}
        debug_dict["guild_id"] = ctx.guild.id
        debug_dict["author_id"] = ctx.author.id
        debug_dict["problem_limit"] = self.bot.main_cache.max_guild_problems # the problem limit
        debug_dict["reached_max_problems?"] = "✅" if len(self.bot.main_cache.get_guild_problems(guild)) >= self.bot.main_cache.max_guild_problems else "❌"
        debug_dict["num_guild_problems"] = len(self.bot.main_cache.get_guild_problems(ctx.guild))
        correct_permissions = {
            "read_message_history": "✅" if my_permissions.read_messages else "❌",
            "read_messages": "✅" if my_permissions.read_messages else "❌", #can I read messages?
            "send_messages": "✅" if my_permissions.send_messages else "❌", #can I send messages?
            "embed_links": "✅" if my_permissions.embed_links else "❌", #can I embed links? 
            "use_application_commands": "✅" if my_permissions.use_slash_commands else "❌"
      }
        debug_dict["correct_permissions"] = correct_permissions
        if raw:
            await ctx.reply(str(debug_dict),ephemeral = send_ephermally)
            return
        else:
            text = ""
            for item in debug_dict:
                if not isinstance([item], dict):
                    text += f"{item}: {debug_dict.get(item)}\n"
                else:
                    for item2 in item:
                        if not isinstance(item2, dict):
                            text += f"{item.get(item2)}: {debug_dict[item]}"
                        else:
                            raise RecursionError from Exception("***Nested too much***")

        await ctx.reply(text,ephemeral = send_ephermally)

def setup(bot):
    global problems_module, SuccessEmbed, ErrorEmbed, the_documentation_file_loader, slash
    b = bot._transport_modules
    (problems_module, SuccessEmbed, ErrorEmbed, the_documentation_file_loader) = (b["problems_module"], b["custom_embeds"].SuccessEmbed, b["custom_embeds"].ErrorEmbed, b["the_documentation_file_loader"])
    slash = bot.slash
    bot.add_cog(DeveloperCommands(bot))
def teardown(bot):
    bot.remove_cog("DeveloperCommands")