import nextcord
import traceback
from nextcord import TextInputStyle
from nextcord.ext import commands
from Main import formatOutput, errorResponse, getScrims, getScrim, getTeams, getChannels, logAction
from BotData.herodata import MATCH_FORMATS
from BotData.colors import *
from Keys import DB

async def returnToMain(interaction: nextcord.Interaction, scrims, current_view, note):
    if note == None: embed = nextcord.Embed(title=f"Scrim Manager // {interaction.guild.name}", description="Use the dropdown below to select a scrim to view/edit\n**Or** Select 'View All' to view all currently scheduled scrims", color=White)
    else: embed = nextcord.Embed(title=f"Scrim Manager // {interaction.guild.name}", description=f"Use the dropdown below to select a scrim to view/edit\n**Or** Select 'View All' to view all currently scheduled scrims\n\n{note}", color=White)
    await interaction.response.edit_message(embed=embed, view=MainView(interaction, scrims, current_view=current_view))

class MainView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrims, current_view):
        super().__init__(timeout=None)
        self.add_item(MainDropdown(interaction, scrims, current_view))

class MainDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, scrims, current_view):
        self.interaction = interaction
        self.scrims = scrims
        self.current_view = current_view

        emojis = ["","🔴", "🔵", "🟢", "🟡", "🟣", "🟠", "⚪"]
        count = 1
        options = []

        if current_view == None: # Only show if not currently viewing all
            options.append(nextcord.SelectOption(label="View All", value="View All", description="View all scrims", emoji="🌐"))

        for scrim in scrims:
            team_type = scrim["scrimConfiguration"]["teamType"]
            options.append(nextcord.SelectOption(label=scrim["scrimName"], value=scrim["scrimName"], description=f"{team_type} Scrim", emoji=emojis[count]))
            count += 1

        super().__init__(placeholder="Select a Scrim", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            scrims = getScrims(command['guildID'])

            if interaction.data["values"][0] == "View All": # All Scrims
                embed = nextcord.Embed(title=f"Scrim Manager // {interaction.guild.name}", description="Viewing all scheduled scrims, to edit a specific scrim, select it from the dropdown", color=White)
                for scrim in scrims:
                    teams = getTeams(command['guildID'], scrim['scrimName'])
                    teams_signed_up = len(teams)
                    if teams_signed_up > scrim['scrimConfiguration']['maxTeams']:
                        reserve_teams = teams_signed_up - scrim['scrimConfiguration']['maxTeams']
                        teams_signed_up = scrim['scrimConfiguration']['maxTeams']
                        team_display = f"**({teams_signed_up}/{scrim['scrimConfiguration']['maxTeams']})** (+ {reserve_teams})"
                    else: team_display = f"**({teams_signed_up}/{scrim['scrimConfiguration']['maxTeams']})**"

                    embed.add_field(name=f"{scrim['scrimName']}", value=f"Teams: {team_display}\nTime: <t:{scrim['scrimEpoch']}:f> (**{scrim['scrimEpoch']}**)\nMatch Format: **{scrim['scrimConfiguration'].get('matchFormat', 'Bo1')}**\nPick/Ban Mode: **{scrim['scrimConfiguration'].get('pickBanMode', 'None')}**\nTeam Type: **{scrim['scrimConfiguration']['teamType']}**\nRegistration Channel: <#{scrim['scrimConfiguration']['registrationChannel']}>", inline=False)

                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=MainView(interaction, scrims, current_view="View All"))

            else: # Individual Scrim
                selected = interaction.data["values"][0]
                scrim = next((s for s in scrims if s["scrimName"] == selected), None)
                if not scrim:
                    await interaction.followup.send("Scrim not found.", ephemeral=True)
                    return
                information = []

                # Build scrim information
                teams = getTeams(command['guildID'], scrim['scrimName'])
                teams_signed_up = len(teams)
                if teams_signed_up > scrim['scrimConfiguration']['maxTeams']:
                    reserve_teams = teams_signed_up - scrim['scrimConfiguration']['maxTeams']
                    teams_signed_up = scrim['scrimConfiguration']['maxTeams']
                    information.append(f"Teams: **({teams_signed_up}/{scrim['scrimConfiguration']['maxTeams']})** (+ {reserve_teams})")
                else: information.append(f"Teams: **({teams_signed_up}/{scrim['scrimConfiguration']['maxTeams']})**")
                information.append(f"Time: <t:{scrim['scrimEpoch']}:f> (**{scrim['scrimEpoch']}**)")
                information.append(f"Match Format: **{scrim['scrimConfiguration'].get('matchFormat', 'Bo1')}**")
                information.append(f"Pick/Ban Mode: **{scrim['scrimConfiguration'].get('pickBanMode', 'None')}**")
                information.append(f"Team Type: **{scrim['scrimConfiguration']['teamType']}**")
                information.append(f"Max Teams: **{scrim['scrimConfiguration']['maxTeams']}**")
                information.append(f"Total Games: **{scrim['scrimConfiguration']['totalGames']}**")
                if scrim['scrimConfiguration']['interval']['repeating'] == True: information.append(f"Interval: **{scrim['scrimConfiguration']['interval']['interval']}** | **Next:** <t:{scrim['scrimConfiguration']['interval']['next']}:f>")
                else: information.append(f"Interval: **None**")
                information.append(f"Registration Channel: <#{scrim['scrimConfiguration']['registrationChannel']}>")

                description = "\n".join(information)
                embed = nextcord.Embed(title=f"Scrim Manager // {scrim['scrimName']}", description=description, color=White)

                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=MainInterface(interaction, scrims, description))

        except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

class MainInterface(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrim, description):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.scrim = scrim
        self.description = description

        edit_button = nextcord.ui.Button(style=nextcord.ButtonStyle.blurple, label="Edit", emoji="📝")
        edit_button.callback = self.create_callback("Edit")
        self.add_item(edit_button)

        return_button = nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label="Return", emoji="↩️")
        return_button.callback = self.create_callback("Return")
        self.add_item(return_button)

        danger_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="Danger Zone", emoji="🔥")
        danger_button.callback = self.create_callback("Danger Zone")
        self.add_item(danger_button)

    def create_callback(self, value):
        async def callback(interaction: nextcord.Interaction):
            try:
                if value == "Edit":
                    embed = nextcord.Embed(title=f"Scrim Manager // {self.scrim[0]['scrimName']}", description=f"{self.description}\n\n**Select a setting to edit**", color=White)
                    await interaction.response.edit_message(embed=embed, view=EditView(interaction, self.scrim))

                elif value == "Return":
                    await returnToMain(interaction, scrims=getScrims(command['guildID']), current_view=None, note=None)

                elif value == "Danger Zone":
                    embed = nextcord.Embed(title=f"Scrim Manager // {self.scrim[0]['scrimName']}", description="Are you sure you want to enter the danger zone\nSettings beyond this point have great impact on your scrims", color=Red)
                    await interaction.response.edit_message(embed=embed, view=DangerConfirmView(interaction, self.scrim))

            except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

        return callback

class EditView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrim):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.scrim = scrim

        buttons = ["Scrim Name", "Date & Time", "Match Format", "Interval Settings"]
        for button in buttons:
            button = nextcord.ui.Button(style=nextcord.ButtonStyle.blurple, label=button)
            button.callback = self.create_callback(button.label)
            self.add_item(button)

        return_button = nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label="Return", emoji="↩️")
        return_button.callback = self.create_callback("Return")
        self.add_item(return_button)

    def create_callback(self, value):
        async def callback(interaction: nextcord.Interaction):
            try:
                if value != "Return":
                    if value == "Scrim Name" or value == "Date & Time":
                        await interaction.response.send_modal(modal=InputModal(interaction, self.scrim, setting=value))

                    elif value == "Match Format":
                        embed = nextcord.Embed(title=f"Scrim Manager // {self.scrim[0]['scrimName']}", description="Select a new match format", color=White)
                        embed.add_field(name="Current", value=f"**{self.scrim[0]['scrimConfiguration'].get('matchFormat', 'Bo1')}**", inline=True)
                        await interaction.response.edit_message(embed=embed, view=MatchFormatView(interaction, self.scrim))

                    elif value == "Interval Settings":
                        embed = nextcord.Embed(title=f"Scrim Manager // {self.scrim[0]['scrimName']}", description=f"Editing {value.lower()}\nCurrent settings", color=White)
                        embed.add_field(name="Interval", value=f"**{self.scrim[0]['scrimConfiguration']['interval']['interval']}**", inline=True)
                        if self.scrim[0]['scrimConfiguration']['interval']['next'] != None: embed.add_field(name="Next Scrim", value=f"<t:{self.scrim[0]['scrimConfiguration']['interval']['next']}:f> (**{self.scrim[0]['scrimConfiguration']['interval']['next']}**)", inline=True)
                        else: embed.add_field(name="Next Scrim", value="None", inline=True)

                        await interaction.response.edit_message(embed=embed, view=IntervalView(interaction, self.scrim))

                else: # Return
                    await returnToMain(interaction, scrims=getScrims(command['guildID']), current_view=None, note=None)

            except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

        return callback

class InputModal(nextcord.ui.Modal):
    def __init__(self, interaction: nextcord.Interaction, scrim, setting):
        super().__init__(f"Enter New {setting}", timeout=None)
        self.interaction = interaction
        self.scrim = scrim
        self.setting = setting

        if setting == "Scrim Name": placeholder = "Enter new scrim name"
        elif setting == "Date & Time": placeholder = "Enter new scrim time (In Epoch)"

        self.input = nextcord.ui.TextInput(
            style=TextInputStyle.short,
            label=setting,
            placeholder=placeholder,
            min_length=0,
            max_length=100
        )

        self.input.callback = self.callback
        self.add_item(self.input)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            if self.setting == "Scrim Name":
                print(interaction.data)
                new_name = self.input.value
                DB[str(command['guildID'])]["ScrimData"].update_one({"scrimName": self.scrim[0]['scrimName']}, {"$set": {"scrimName": new_name}})
                note = f"Scrim Name Changed to {new_name} (from {self.scrim[0]['scrimName']})"

            elif self.setting == "Date & Time":
                new_time = self.input.value
                DB[str(command['guildID'])]["ScrimData"].update_one({"scrimName": self.scrim[0]['scrimName']}, {"$set": {"scrimEpoch": new_time}})
                if self.scrim[0]['scrimConfiguration']['interval']['repeating'] == True: # Update Next (if set)
                    if self.scrim[0]['scrimConfiguration']['interval']['interval'] == "Daily": add = 86400
                    if self.scrim[0]['scrimConfiguration']['interval']['interval'] == "Weekly": add = 604800
                    if self.scrim[0]['scrimConfiguration']['interval']['interval'] == "Fortnightly": add = 1209600
                    if self.scrim[0]['scrimConfiguration']['interval']['interval'] == "Monthly": add = 2419200
                    DB[str(command['guildID'])]["ScrimData"].update_one({"scrimName": self.scrim[0]['scrimName']}, {"$set": {"scrimConfiguration.interval.next": new_time + add}})
                note = f"Scrim Time Changed to {new_time} (from {self.scrim[0]['scrimEpoch']})"

            formatOutput(output=note, status="Normal", guildID=command['guildID'])

            await logAction(command['guildID'], interaction.user.name, note, "Scrim Manager")

        except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

class MatchFormatView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrim):
        super().__init__(timeout=None)
        self.add_item(MatchFormatDropdown(interaction, scrim))

class MatchFormatDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, scrim):
        self.interaction = interaction
        self.scrim = scrim
        options = [nextcord.SelectOption(label=fmt, value=fmt) for fmt in MATCH_FORMATS]
        super().__init__(placeholder="Select Match Format", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            new_format = interaction.data["values"][0]
            old_format = self.scrim[0]['scrimConfiguration'].get('matchFormat', 'Bo1')
            DB[str(command['guildID'])]["ScrimData"].update_one(
                {"scrimName": self.scrim[0]['scrimName']},
                {"$set": {"scrimConfiguration.matchFormat": new_format}},
            )
            note = f"Match Format changed to {new_format} (from {old_format})"
            formatOutput(output=note, status="Normal", guildID=command['guildID'])
            await logAction(command['guildID'], interaction.user.name, f"{self.scrim[0]['scrimName']}, {note}", "Scrim Manager")
            await returnToMain(interaction, scrims=getScrims(command['guildID']), current_view=None, note=note)
        except Exception as e:
            await errorResponse(e, command, interaction, traceback.format_exc())

class IntervalView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrim):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.scrim = scrim

        if self.scrim[0]['scrimConfiguration']['interval']['repeating'] == True:
            edit_button = nextcord.ui.Button(style=nextcord.ButtonStyle.blurple, label="Edit Interval")
            edit_button.callback = self.create_callback("Edit Interval")
            self.add_item(edit_button)

        else:
            add_button = nextcord.ui.Button(style=nextcord.ButtonStyle.green, label="Add Interval")
            add_button.callback = self.create_callback("Add Interval")
            self.add_item(add_button)

        remove_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="Remove Interval")
        remove_button.callback = self.create_callback("Remove Interval")
        self.add_item(remove_button)

        return_button = nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label="Return", emoji="↩️")
        return_button.callback = self.create_callback("Return")
        self.add_item(return_button)

    def create_callback(self, value):
        async def callback(interaction: nextcord.Interaction):
            try:
                if value != "Return":
                    if value == "Edit Interval" or value == "Add Interval":
                        await interaction.response.edit_message(view=IntervalViewOpen(interaction, self.scrim, action="Edit"))

                    elif value == "Remove Interval":
                        DB[str(command['guildID'])]["ScrimData"].update_one({"scrimName": self.scrim[0]['scrimName']}, {"$set": {"scrimConfiguration.interval": {"repeating": False, "interval": None, "next": None}}})
                        note = f"Interval Removed"

                        formatOutput(output=note, status="Normal", guildID=command['guildID'])
                        await returnToMain(interaction, scrims=getScrims(command['guildID']), current_view=None, note=note)

                        await logAction(command['guildID'], interaction.user.name, f"{self.scrim[0]['scrimName']}, Interval Removed", "Scrim Manager")

                else: # Return
                    await returnToMain(interaction, scrims=getScrims(command['guildID']), current_view=None, note=None)

            except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

        return callback

class IntervalViewOpen(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrim, action):
        super().__init__(timeout=None)
        self.add_item(IntervalViewDropdown(interaction, scrim, action))

class IntervalViewDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, scrim, action):
        self.interaction = interaction
        self.scrim = scrim
        self.action = action

        option_list = []
        options = ["Daily", "Weekly", "Fortnightly", "Monthly"]
        for option in options:
            if option == self.scrim[0]['scrimConfiguration']['interval']['interval']: continue
            else: option_list.append(nextcord.SelectOption(label=option, value=option))

        super().__init__(placeholder="Select an Interval", min_values=1, max_values=1, options=option_list)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            if self.action == "Edit":
                interval = interaction.data["values"][0]
                if interval == "Daily": add = 86400
                if interval == "Weekly": add = 604800
                if interval == "Fortnightly": add = 1209600
                if interval == "Monthly": add = 2419200

                epoch = int(self.scrim[0]['scrimEpoch'])

                DB[str(command['guildID'])]["ScrimData"].update_one({"scrimName": self.scrim[0]['scrimName']}, {"$set": {"scrimConfiguration.interval": {"repeating": True, "interval": interval, "next": epoch + add}}})
                note = f"Interval Changed to {interval} (from {self.scrim[0]['scrimConfiguration']['interval']['interval']})"

            formatOutput(output=note, status="Normal", guildID=command['guildID'])
            await logAction(command['guildID'], interaction.user.name, f"{self.scrim[0]['scrimName']}, {note}", "Scrim Manager")

            await returnToMain(interaction, scrims=getScrims(command['guildID']), current_view=None, note=note)

        except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

class DangerConfirmView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrim):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.scrim = scrim

        confirm_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="Enter Danger Zone", emoji="🔥")
        confirm_button.callback = self.create_callback("Enter Danger Zone")
        self.add_item(confirm_button)

        return_button = nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label="Return", emoji="↩️")
        return_button.callback = self.create_callback("Return")
        self.add_item(return_button)

    def create_callback(self, value):
        async def callback(interaction: nextcord.Interaction):
            try:
                if value == "Enter Danger Zone":
                    embed = nextcord.Embed(title=f"Scrim Manager // {self.scrim[0]['scrimName']}", description="Danger Zone\n**ALL** settings in here are non-reversable, proceed with caution!", color=Red)
                    await interaction.response.edit_message(embed=embed, view=DangerZoneView(interaction, self.scrim))

                elif value == "Return":
                    await returnToMain(interaction, scrims=getScrims(command['guildID']), current_view=None, note=None)

            except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

        return callback

class DangerZoneView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrim):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.scrim = scrim

        delete_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="Delete Scrim", emoji="❌")
        delete_button.callback = self.create_callback("Delete Scrim")
        self.add_item(delete_button)

        return_button = nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label="Return", emoji="↩️")
        return_button.callback = self.create_callback("Return")
        self.add_item(return_button)

    def create_callback(self, value):
        async def callback(interaction: nextcord.Interaction):
            try:
                if value == "Delete Scrim":
                    await interaction.response.send_message(
                        embed=nextcord.Embed(title="Confirm Delete", description="This cannot be undone.", color=Red),
                        view=DangerActionConfirmView(interaction, self.scrim, action="Delete Scrim"),
                        ephemeral=True,
                    )

            except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

        return callback

class DangerActionConfirmView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrim, action):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.scrim = scrim
        self.action = action

        confirm_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label=f"Confirm {action}", emoji="❌")
        confirm_button.callback = self.create_callback(f"Confirm {action}")
        self.add_item(confirm_button)

        return_button = nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label="Return", emoji="↩️")
        return_button.callback = self.create_callback("Return")
        self.add_item(return_button)

    def create_callback(self, value):
        async def callback(interaction: nextcord.Interaction):
            try:
                if value == f"Confirm {self.action}":
                    if self.action == "Delete Scrim":
                        DB[str(command['guildID'])]["ScrimData"].delete_one({"scrimName": self.scrim[0]['scrimName']})
                        note = f"Scrim Deleted: {self.scrim[0]['scrimName']}"

                        formatOutput(output=note, status="Normal", guildID=command['guildID'])
                        await returnToMain(interaction, scrims=getScrims(command['guildID']), current_view=None, note=note)

                        await logAction(command['guildID'], interaction.user.name, f"{self.scrim[0]['scrimName']}, Scrim Deleted", "Scrim Manager")

            except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

        return callback

class Command_scrims_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="scrims", description="View and edit all currently scheduled scrims **Admin Only**", default_member_permissions=(nextcord.Permissions(administrator=True)))
    async def scrims(self, interaction: nextcord.Interaction):
        global command
        command = {"name": interaction.application_command.name, "userID": interaction.user.id, "guildID": interaction.guild.id}
        formatOutput(output=f"/{command['name']} Used by {command['userID']} | @{interaction.user.name}", status="Normal", guildID=command["guildID"])

        try: await interaction.response.defer(ephemeral=True)
        except: pass # Discord can sometimes error on defer()

        try:
            scrims = getScrims(command['guildID'])
            if len(scrims) == 0: # No Scrims
                embed = nextcord.Embed(title=f"Scrim Manager // {interaction.guild.name}", description="No scrims have been scheduled\nSchedule a scrim using `/schedule`", color=Yellow)
                await interaction.edit_original_message(embed=embed)
                return

            else: # 1 or more scrims
                embed = nextcord.Embed(title=f"Scrim Manager // {interaction.guild.name}", description="Use the dropdown below to select a scrim to view/edit\n**Or** Select 'View All' to view all currently scheduled scrims", color=White)
                await interaction.edit_original_message(embed=embed, view=MainView(interaction, scrims, current_view=None))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

def setup(bot):
    bot.add_cog(Command_scrims_Cog(bot))