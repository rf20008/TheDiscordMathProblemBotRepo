"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

TheDiscordMathProblemRepo - AppealCog

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
(with the assistance of Google Gemini)
"""

import asyncio
from os import urandom
import json

import disnake
from disnake.ext import commands

from helpful_modules.checks import has_privileges
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import SuccessEmbed, ErrorEmbed

from cogs.helper_cog import HelperCog
from .appeal_modals import UserDenylistAppealModal, GuildDenylistAppealModal
from .errors import NoAppealQuestionsException
from helpful_modules.problems_module import AppealType, APPEAL_QUESTION_TYPE_NAMES, AppealQuestion

# Hard-capped safely below 15 minutes to guarantee token life and stability
SAFE_MODAL_TIMEOUT = 600.0


class AppealsCog(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)
        self.bot = bot
        self.cache = bot.cache

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.slash_command(name="appeal", description="Access the formal restrictions appeal system.")
    async def appeal(self, inter: disnake.ApplicationCommandInteraction):
        """/appeal

        Appeal your punishments! It uses a modal.
        There are subcommands!"""
        pass

    def load_questions(self):
        """Loads and converts multi-category question sets into AppealQuestion objects."""
        if not getattr(self.bot, "appeal_questions", None):
            try:
                with open("appeal_questions.json", "r", encoding='utf-8') as file5:
                    question_sets: dict = json.load(fp=file5)

                parsed_sets = {}
                for key, question_set in question_sets.items():
                    parsed_sets[key] = [
                        AppealQuestion.from_dict(question) for question in question_set
                    ]

                self.bot.appeal_questions = parsed_sets
            except Exception as e:
                print(f"[AppealsCog Exception] Failed file load: {e}")
                self.bot.appeal_questions = {}
                raise NoAppealQuestionsException("The appeal questions failed to load.") from e

        if not self.bot.appeal_questions:
            raise NoAppealQuestionsException("There are no appeal questions configurations online.")

    @commands.cooldown(3, 30, commands.BucketType.user)
    @appeal.sub_command(name="view_questions", description="Publicly view the current active appeal questionnaires.")
    async def view_questions(self, inter: disnake.ApplicationCommandInteraction):
        """/appeal view_questions
        Public informational command to preview the active rules and questionnaire criteria.
        Allows users to pre-draft long statements safely offline before executing a form request.
        """
        try:
            self.load_questions()
        except NoAppealQuestionsException:
            await inter.send(embed=ErrorEmbed("No active question validation schemas could be parsed."), ephemeral=True)
            return

        user_questions = self.bot.appeal_questions.get("user_denylist", [])
        user_text = "".join([f"**{i}. {q.question}**\n*{q.long_prompt}*\n\n" for i, q in enumerate(user_questions, 1)]) or "*None configured.*"

        guild_questions = self.bot.appeal_questions.get(APPEAL_QUESTION_TYPE_NAMES[AppealType.GUILD_DENYLIST_APPEAL], [])
        guild_text = "".join([f"**{i}. {q.question}**\n*{q.long_prompt}*\n\n" for i, q in enumerate(guild_questions, 1)]) or "*None configured.*"

        preview_embed = disnake.Embed(
            title="📋 System Appeal Questionnaires",
            description="Below are the active live requirements for restrictions processing:\n\n---",
            color=disnake.Color.blue()
        )
        preview_embed.add_field(name="👤 User Profile Appeal Questions", value=user_text, inline=False)
        preview_embed.add_field(name="🏰 Guild Ecosystem Appeal Questions", value=guild_text, inline=False)
        preview_embed.set_footer(
            text="NOTE: When you prepare an appeal, use /view_questions to prepare your answers. Please prepare them in an external text editor."
                 "WARNING: If you close the modal (for example by clicking outside it), your answers will be lost FOREVER!"
        )
        await inter.send(embed=preview_embed, ephemeral=True)

    @has_privileges(denylisted=True)
    @commands.cooldown(2, 86400, commands.BucketType.user)
    @appeal.sub_command(name="denylist", description="Appeal your profile-level system denylist.")
    async def denylist(self, inter: disnake.ApplicationCommandInteraction):
        """/appeal denylist
        Submit a formal appeal for your profile-level system restriction.

        This command utilizes an interactive, multi-stage submission workflow:
        1. Pre-flight Panel: Displays the active questionnaire text directly in chat.
        2. Launch Gate: Requires you to click a button to launch the formal entry fields.
        3. Modal Popup: Allows you to safely paste your answers into the platform panel.

        ⏳ TIME CONSTRAINTS & CRITICAL SAFETY DATA:
        • Form Launcher Gate: You have exactly 2 minutes (120 seconds) to click the launch button.
        • Modal Submission Panel: Once the popup is active, you have 10 minutes to submit your text.
        • WARNING: If you click outside the modal interface, YOUR WORK WILL BE LOST FOREVER!

        💡 PREPARATION STRATEGY:
        Do not type answers live into the form windows. Use `/appeal view_questions` to preview
        all active prompt criteria beforehand, draft your responses entirely in an external
        text editor, and copy-paste them into the fields immediately upon launching.
        """
        try:
            self.load_questions()
        except NoAppealQuestionsException:
            await inter.send(embed=ErrorEmbed("No active validation question schemas could be loaded."), ephemeral=True)
            return

        user_questions = self.bot.appeal_questions.get("user_denylist", [])
        questionnaire_text = "".join([f"**{i}. {q.question}**\n*Instructions:* {q.long_prompt}\n\n" for i, q in enumerate(user_questions, 1)])

        warning_embed = disnake.Embed(
            title="⚠️ CRITICAL APPEAL REQUIREMENTS",
            description=(
                "**DO NOT TYPE DIRECTLY IN THE MODAL WINDOW!**\n\n"
                "Warning: If you close the popup or take too long, your work will be **LOST FOREVER**.\n\n"
                f"### 📝 Required Questionnaire:\n{questionnaire_text}"
                "Copy these questions, draft your text inside an external editor first, then click "
                "the confirmation button below to copy-paste responses into form fields immediately.\n"
                f"*(Form submission window expires in {int(SAFE_MODAL_TIMEOUT / 60)} minutes)*"
            ),
            color=disnake.Color.red()
        )
        warning_embed.set_footer(
            text="Don't worry. If this message disappears before you're ready, you can use this command again to "
                 "re-display the questions. \n"
                 "Note: If you close the actual appeal modal layout, your answers will be lost FOREVER!"
        )
        unique_gate_id = f"gate_user_{inter.author.id}_{urandom(4).hex()}"
        components = [
            disnake.ui.Button(label="I have prepared my text, launch form", custom_id=unique_gate_id, style=disnake.ButtonStyle.danger)
        ]
        await inter.send(embed=warning_embed, components=components, ephemeral=True)

        try:
            btn_inter: disnake.MessageInteraction = await self.bot.wait_for(
                "button_click", check=lambda b_i: b_i.data.custom_id == unique_gate_id and b_i.author.id == inter.author.id, timeout=120.0
            )
        except asyncio.TimeoutError:
            return

        modal_custom_id = f"user_appeal_{inter.author.id}_{urandom(4).hex()}"
        text_inputs = [q.to_textinput(index=i) for i, q in enumerate(user_questions, 1)]

        modal = UserDenylistAppealModal(
            title="User System Appeal Form",
            components=text_inputs,
            timeout=SAFE_MODAL_TIMEOUT,
            custom_id=modal_custom_id,
        )
        if modal.components and modal.components[0].children:
            modal.undenylist_custom_id = modal.components[0].children[0].custom_id

        await btn_inter.response.send_modal(modal)

        try:
            modal_inter: disnake.ModalInteraction = await self.bot.wait_for(
                "modal_submit", check=lambda m_i: m_i.custom_id == modal_custom_id and m_i.author.id == inter.author.id, timeout=SAFE_MODAL_TIMEOUT
            )
        except asyncio.TimeoutError:
            try:
                await inter.followup.send(embed=ErrorEmbed("Submission lifespan reached. Form window closed."), ephemeral=True)
            except disnake.HTTPException:
                pass
            return

        await modal_inter.response.send_message(
            embed=SuccessEmbed("Your profile restriction appeal has been securely cataloged for administrative assessment."), ephemeral=True
        )

    @commands.cooldown(2, 15, commands.BucketType.user)
    @appeal.sub_command(name="guild_denylist", description="Appeal your guild denylists")
    async def guild_denylist(self, inter: disnake.ApplicationCommandInteraction):
        """/appeal guild_denylist
        Request a formal administrative review for server infrastructure bans.

        This command uses a safe, multi-stage submission system:
        1. Pre-flight Warning: Displays active requirements and rules before opening the form.
        2. Launch Gate: You must click a verification button to open the submission fields.
        3. Modal Form: Paste your answers directly into the pop-up panel.

        ⏳ CRITICAL TIME & SAFETY LIMITS:
        • Pre-launch Gate: You have 2 minutes (120 seconds) to click the confirmation button.
        • Form Submission: Once the pop-up modal is open, you have exactly 10 minutes to submit.
        • WARNING: If you click outside the modal or close it, YOUR WORK IS LOST FOREVER.

        📝 CRITERIA QUESTIONS INCLUDED:
        1) Guild ID Target: A verified integer sequence identifying the restricted ecosystem.
        2) Validation of Authority: Evidence of your administrative permissions inside that server.
        3) Remediation Narrative: Context detailing rule compliance adjustments and improvements.

        💡 PRO-TIP FOR SUCCESSFUL APPLICATIONS:
        Do not type answers live in the form. Use `/appeal view_questions` to extract current layouts,
        draft essays offline within an external text editor, and copy-paste them cleanly once ready.
        """
        try:
            self.load_questions()
        except NoAppealQuestionsException:
            await inter.send(embed=ErrorEmbed("No active validation question schemas could be loaded."), ephemeral=True)
            return

        questions = self.bot.appeal_questions[APPEAL_QUESTION_TYPE_NAMES[AppealType.GUILD_DENYLIST_APPEAL]]
        guild_questionnaire_text = "".join([f"**{i}. {q.question}**\n*Instructions:* {q.long_prompt}\n\n" for i, q in enumerate(questions, 1)])

        warning_embed = disnake.Embed(
            title="⚠️ CRITICAL GUILD APPEAL REQUIREMENTS",
            description=(
                "**DO NOT TYPE DIRECTLY IN THE MODAL WINDOW!**\n\n"
                "If you close the popup or take too long, your work will be **LOST FOREVER**.\n\n"
                f"### 📝 Required Questionnaire:\n{guild_questionnaire_text}"
                "Please draft these answers entirely inside an external editor first, then click "
                "the confirmation button below to copy-paste into the active modal submission fields.\n"
                f"*(Form submission window expires in {int(SAFE_MODAL_TIMEOUT / 60)} minutes)*"
            ),
            color=disnake.Color.red()
        )
        warning_embed.set_footer(
            text="Don't worry. If this message disappears before you're ready, you can use this command again to "
                 "re-display the questions. Note: If you close the actual appeal modal layout, your answers will be lost forever."
        )
        unique_gate_id = f"gate_guild_{inter.author.id}_{urandom(4).hex()}"
        components = [
            disnake.ui.Button(
                label="I have prepared my text, launch form",
                custom_id=unique_gate_id,
                style=disnake.ButtonStyle.danger
            )
        ]
        await inter.send(embed=warning_embed, components=components, ephemeral=True)

        try:
            btn_inter: disnake.MessageInteraction = await self.bot.wait_for(
                "button_click", check=lambda b_i: b_i.data.custom_id == unique_gate_id and b_i.author.id == inter.author.id, timeout=120.0
            )
        except asyncio.TimeoutError:
            return

        modal_custom_id = f"guild_appeal_{inter.author.id}_{urandom(4).hex()}"
        textinputs = [q.to_textinput(index=i) for i, q in enumerate(questions, 1)]
        question_custom_ids = {question: textinput.custom_id for question, textinput in zip(questions, textinputs)}

        modal = GuildDenylistAppealModal(
            timeout=SAFE_MODAL_TIMEOUT,
            title="Guild Restriction Appeal Form",
            components=textinputs,
            custom_id=modal_custom_id,
        )
        modal.guild_id_custom_id = textinputs[0].custom_id
        modal.reason_custom_id = textinputs[-1].custom_id
        modal.custom_ids = question_custom_ids

        await btn_inter.response.send_modal(modal)

        try:
            modal_inter: disnake.ModalInteraction = await self.bot.wait_for(
                "modal_submit", check=lambda m_i: m_i.custom_id == modal_custom_id and m_i.author.id == inter.author.id, timeout=SAFE_MODAL_TIMEOUT
            )
        except asyncio.TimeoutError:
            try:
                await inter.followup.send(embed=ErrorEmbed("Submission lifespan reached. Form window closed."), ephemeral=True)
            except disnake.HTTPException:
                pass
            return

        await modal_inter.response.send_message(
            embed=SuccessEmbed("The server ecosystem restriction appeal payload was securely forwarded for internal assessment."), ephemeral=True
        )


def setup(bot):
    bot.add_cog(AppealsCog(bot))


def teardown(bot):
    bot.remove_cog("AppealsCog")