import nextcord
import traceback
from nextcord.ext import commands
from Main import formatOutput, errorResponse
from BotData.colors import *

class FeedbackView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction):
        super().__init__(timeout=None)
        self.interaction = interaction

        feedback_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Feedback", emoji="🗨️")
        feedback_button.callback = self.create_callback("Feedback")
        self.add_item(feedback_button)

        suggestion_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Suggestion", emoji="📝")
        suggestion_button.callback = self.create_callback("Suggestion")
        self.add_item(suggestion_button)

        bug_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Bug Report", emoji="🐛")
        bug_button.callback = self.create_callback("Bug Report")
        self.add_item(bug_button)

    def create_callback(self, feedback_type):
        async def callback(interaction: nextcord.Interaction):
            try: await interaction.response.send_modal(modal=FeedbackModal(interaction, feedback_type))
            except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

        return callback

class FeedbackModal(nextcord.ui.Modal):
    def __init__(self, interaction: nextcord.Interaction, feedback_type):
        super().__init__(title=feedback_type, timeout=None)
        self.interaction = interaction
        self.feedback_type = feedback_type

        self.input = nextcord.ui.TextInput(
            label=feedback_type,
            style=nextcord.TextInputStyle.paragraph,
            placeholder=f"Input {feedback_type} Here",
            min_length=1,
            max_length=1000)

        self.input.callback = self.callback
        self.add_item(self.input)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            embed = nextcord.Embed(title=f"{self.feedback_type} Preview", description=self.input.value, color=White)
            await interaction.response.edit_message(embed=embed, view=ConfirmationView(interaction, self.feedback_type))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

class ConfirmationView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, feedback_type):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.feedback_type = feedback_type

        send_button = nextcord.ui.Button(style=nextcord.ButtonStyle.success, label="Send")
        send_button.callback = self.create_callback("Send")
        self.add_item(send_button)

        edit_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Edit")
        edit_button.callback = self.create_callback("Edit")
        self.add_item(edit_button)

        cancel_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="Cancel")
        cancel_button.callback = self.create_callback("Cancel")
        self.add_item(cancel_button)

    def create_callback(self, action):
        async def callback(interaction: nextcord.Interaction):
            try:
                if action == "Send":
                    embed = nextcord.Embed(title=self.feedback_type, description=interaction.message.embeds[0].description, color=White)

                    from Main import bot # Not the best way to do this, but limitations make it the only way
                    from Keys import ERROR_REPORT_GUILD_ID, ERROR_REPORT_CHANNEL_ID
                    if ERROR_REPORT_GUILD_ID and ERROR_REPORT_CHANNEL_ID:
                        channel = await bot.get_guild(ERROR_REPORT_GUILD_ID).fetch_channel(ERROR_REPORT_CHANNEL_ID)
                        await channel.send(embed=embed)

                    embed = nextcord.Embed(title=f"{self.feedback_type} Submitted", description="Thank you for your feedback.", color=Green)
                    await interaction.response.edit_message(embed=embed, view=None)

                elif action == "Edit":
                    await interaction.response.send_modal(modal=FeedbackModal(interaction, self.feedback_type))

                elif action == "Cancel":
                    embed = nextcord.Embed(title=f"{self.feedback_type} Cancelled", description="Your feedback has not been sent", color=Red)
                    await interaction.response.edit_message(embed=embed)

            except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

        return callback

class Command_feedback_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="feedback", description="Submit Feedback / Suggestions / Bug Reports to the maintainers")
    async def feedback(self, interaction: nextcord.Interaction):
        global command
        command = {"name": interaction.application_command.name, "userID": interaction.user.id, "guildID": interaction.guild.id}
        formatOutput(output=f"/{command['name']} Used by {command['userID']} | @{interaction.user.name}", status="Normal", guildID=command["guildID"])

        try: await interaction.response.defer(ephemeral=True)
        except: pass # Discord can sometimes error on defer()

        try:
            embed = nextcord.Embed(title="Feedback Form", description="Select the type of feedback you would like to submit.", color=White)
            embed.set_footer(text="Clicking on any button will immediately open a text input to submit your feedback.")
            await interaction.edit_original_message(embed=embed, view=FeedbackView(interaction))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

def setup(bot):
    bot.add_cog(Command_feedback_Cog(bot))