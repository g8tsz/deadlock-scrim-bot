import nextcord
import datetime
import traceback
from nextcord.ext import commands
from Main import formatOutput, errorResponse, getChannels, getMessages, splitMessage, getScrims, getPresets
from Keys import DB
from BotData.colors import *
from BotData.herodata import MATCH_FORMATS, PICKBAN_MODES

class NamingView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrims):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.scrims = scrims

        input_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Input Name")
        input_button.callback = self.create_callback("input")
        self.add_item(input_button)

        cancel_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="Cancel")
        cancel_button.callback = self.create_callback("cancel")
        self.add_item(cancel_button)

    def create_callback(self, custom_id):
        async def callback(interaction: nextcord.Interaction):
            try:
                if custom_id == "input":
                    await interaction.response.send_modal(modal=NamingModal(interaction, self.scrims))

                elif custom_id == "cancel":
                    embed = nextcord.Embed(title="Scrim Scheduling // Scrim Scheduling Cancelled", description="Scrim Scheduling has been cancelled", color=Red)
                    await interaction.response.edit_message(embed=embed, view=None)

            except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())
        return callback

class NamingModal(nextcord.ui.Modal):
    def __init__(self, interaction: nextcord.Interaction, scrims):
        super().__init__(title="Scrim Name", timeout=None)
        self.interaction = interaction
        self.scrims = scrims

        self.input = nextcord.ui.TextInput(
            label="Scrim Name",
            style=nextcord.TextInputStyle.short,
            placeholder="Enter Scrim Name",
            min_length=1,
            max_length=30)

        self.input.callback = self.callback
        self.add_item(self.input)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            name_used = False

            for scrim in self.scrims:
                if self.input.value == scrim["scrimName"]:
                    name_used = True

            if name_used == True:
                embed = nextcord.Embed(title="Scrim Scheduling // Name Taken", description="This name is already in use, please choose another", color=Red)
                embed.set_footer(text="Step 1/13")
                await interaction.response.edit_message(embed=embed, view=NamingView(interaction, self.scrims))

            else:
                scrim_name = self.input.value
                schedule_data = {"scrim_name": scrim_name}

                embed = nextcord.Embed(title=f"Scrim Scheduling: {schedule_data['scrim_name']} // Time Selection", description="Head to https://www.epochconverter.com/ and get the epoch time.\nScheduling with time and date is no longer supported", color=White)
                embed.set_footer(text="Step 2/13")
                await interaction.response.edit_message(embed=embed, view=TimingView(interaction, schedule_data))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

class TimingView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data

        input_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Input Time")
        input_button.callback = self.create_callback("input")
        self.add_item(input_button)

        cancel_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="Cancel")
        cancel_button.callback = self.create_callback("cancel")
        self.add_item(cancel_button)

    def create_callback(self, custom_id):
        async def callback(interaction: nextcord.Interaction):
            try:
                if custom_id == "input":
                    await interaction.response.send_modal(modal=TimingModal(interaction, self.schedule_data))

                elif custom_id == "cancel":
                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Scrim Scheduling Cancelled", description="Scrim Scheduling has been cancelled", color=Red)
                    await interaction.response.edit_message(embed=embed, view=None)

            except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())
        return callback

class TimingModal(nextcord.ui.Modal):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(title="Scrim Time", timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data

        self.input = nextcord.ui.TextInput(
            label="Scrim Time",
            style=nextcord.TextInputStyle.short,
            placeholder="Enter Scrim Time (in epoch)",
            min_length=1,
            max_length=30)

        self.input.callback = self.callback
        self.add_item(self.input)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            scrim_time = self.input.value

            if scrim_time.isnumeric() == True:
                scrim_time = int(scrim_time)
                self.schedule_data["scrim_time"] = scrim_time

                embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Preset Selection", description="Select a preset below to quickly create a scrim", color=White)
                embed.set_footer(text="Step 3/13")
                await interaction.response.edit_message(embed=embed, view=PresetView(interaction, self.schedule_data))

            else:
                embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Scrim Time", description="Please enter a valid epoch time", color=Red)
                embed.set_footer(text="Step 2/13")
                await interaction.response.edit_message(embed=embed, view=TimingView(interaction, self.schedule_data))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

class PresetView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data

        preset_buttons = 0
        for id, preset in getPresets(interaction.guild.id).items():
            preset_name = preset['presetName']
            if preset_name == None: continue

            button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label=preset_name)
            button.callback = self.create_callback(id, preset_name)
            self.add_item(button)
            preset_buttons += 1

        if preset_buttons == 0: # No presets set
            button = nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label="No Presets have been created, create them in /configure", disabled=True)
            self.add_item(button)

        cancel_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="Cancel")
        cancel_button.callback = self.create_callback(None, "cancel")
        self.add_item(cancel_button)

        skip_button = nextcord.ui.Button(style=nextcord.ButtonStyle.gray, label="Skip")
        skip_button.callback = self.create_callback(None, "skip")
        self.add_item(skip_button)

    def create_callback(self, id, button):
        async def callback(interaction: nextcord.Interaction):
            try:
                if button == "cancel":
                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Scrim Scheduling Cancelled", description="Scrim Scheduling has been cancelled", color=Red)
                    await interaction.response.edit_message(embed=embed, view=None)

                elif button == "skip":
                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Pick/Ban Mode", description="Select a pick/ban mode from the dropdown below", color=White)
                    embed.set_footer(text="Step 4/12")
                    await interaction.response.edit_message(embed=embed, view=PickBanModeView(interaction, self.schedule_data))

                else:
                    preset = getPresets(interaction.guild.id)[id]["presetData"]
                    self.schedule_data["match_format"] = preset["matchFormat"]
                    self.schedule_data["pickban_mode"] = preset["pickBanMode"]
                    self.schedule_data["team_type"] = preset["teamType"]
                    self.schedule_data["max_teams"] = preset["maxTeams"]
                    self.schedule_data["total_games"] = preset["totalGames"]
                    self.schedule_data["recurrence"] = preset["recurrence"]
                    self.schedule_data["interval"] = preset["interval"]
                    self.schedule_data["pickban_time"] = preset["pickBanTime"]

                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Registration Channel", description=f"Input the Channel ID for where registrations will be put", color=White)
                    embed.set_footer(text="Step 12/12")
                    await interaction.response.edit_message(embed=embed, view=RegistrationChannelView(interaction, self.schedule_data))

            except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())
        return callback

class PickBanModeView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data
        self.add_item(PickBanModeDropdown(interaction, schedule_data))

class PickBanModeDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        self.interaction = interaction
        self.schedule_data = schedule_data

        options = [
            nextcord.SelectOption(label="Captain Draft", value="Captain Draft", description="Captains submit hero picks and bans", emoji="🎯"),
            nextcord.SelectOption(label="Tournament", value="Tournament", description="Structured tournament draft phase", emoji="⚔"),
            nextcord.SelectOption(label="Random", value="Random", description="Random hero bans assigned to teams", emoji="🎲"),
            nextcord.SelectOption(label="None", value="None", description="Disable pick/bans for this scrim", emoji="❌")
        ]

        super().__init__(placeholder="Select a Pick/Ban Mode", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            self.schedule_data["pickban_mode"] = interaction.data["values"][0]

            embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Pick/Ban Time", description="Select when pick/bans should open\nNumerical values are hours before start!", color=White)
            embed.set_footer(text="Step 5/12")
            await interaction.response.edit_message(embed=embed, view=PickBanTimeView(interaction, self.schedule_data))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

class PickBanTimeView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data
        self.add_item(PickBanTimeDropdown(interaction, schedule_data))

class PickBanTimeDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        self.interaction = interaction
        self.schedule_data = schedule_data

        options = []
        raw_options = ["Start Time", 1, 2, 3, 4, 5, 6, 8, 10, 12, 24, "Registration"]
        for option in raw_options:
            options.append(nextcord.SelectOption(label=str(option), value=str(option)))

        super().__init__(placeholder="Select when pick/bans should open", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            self.schedule_data["pickban_time"] = interaction.data["values"][0]

            embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Match Format", description="Select the match format for the scrim series", color=White)
            embed.set_footer(text="Step 6/12")
            await interaction.response.edit_message(embed=embed, view=MatchFormatView(interaction, self.schedule_data))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())


class MatchFormatView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data
        self.add_item(MatchFormatDropdown(interaction, schedule_data))

class MatchFormatDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        self.interaction = interaction
        self.schedule_data = schedule_data

        options = [
            nextcord.SelectOption(label=fmt, value=fmt, description=f"Best of {fmt[2]}")
            for fmt in MATCH_FORMATS
        ]

        super().__init__(placeholder="Select Match Format", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            self.schedule_data["match_format"] = interaction.data["values"][0]

            embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Team Type", description="Select the team size for the scrim", color=White)
            embed.set_footer(text="Step 7/12")
            await interaction.response.edit_message(embed=embed, view=TeamTypeView(interaction, self.schedule_data))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

class TeamTypeView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data

        sixes_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Sixes")
        sixes_button.callback = self.create_callback("Sixes")
        self.add_item(sixes_button)

        trios_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Trios")
        trios_button.callback = self.create_callback("Trios")
        self.add_item(trios_button)

        duos_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Duos")
        duos_button.callback = self.create_callback("Duos")
        self.add_item(duos_button)

        cancel_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="Cancel")
        cancel_button.callback = self.create_callback("Cancel")
        self.add_item(cancel_button)

    def create_callback(self, team_type):
        async def callback(interaction: nextcord.Interaction):
            try:
                if team_type != "Cancel":
                    self.schedule_data["team_type"] = team_type

                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Max Teams", description="How many teams will be participating in the scrim?\nAny teams that sign up over this limit will become reserve teams", color=White)
                    embed.set_footer(text="Step 8/12")
                    await interaction.response.edit_message(embed=embed, view=MaxTeamView(interaction, self.schedule_data))

                else:
                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Scrim Scheduling Cancelled", description="Scrim Scheduling has been cancelled", color=Red)
                    await interaction.response.edit_message(embed=embed, view=None)

            except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())
        return callback

class MaxTeamView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data
        self.add_item(MaxTeamsDropdown(interaction, schedule_data))

class MaxTeamsDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        self.interaction = interaction
        self.schedule_data = schedule_data

        options = []
        if self.schedule_data["team_type"] == "Sixes":
            for number in range(16, 1, -1):
                options.append(nextcord.SelectOption(label=str(number), value=str(number)))
        elif self.schedule_data["team_type"] == "Trios":
            for number in range(20, 4, -1):
                options.append(nextcord.SelectOption(label=str(number), value=str(number)))
        else:
            for number in range(30, 9, -1):
                options.append(nextcord.SelectOption(label=str(number), value=str(number)))

        super().__init__(placeholder="Select Max Teams", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            max_teams = interaction.data["values"][0]
            self.schedule_data["max_teams"] = int(max_teams)

            embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Total Games", description="How many games will be played in the scrim?", color=White)
            embed.set_footer(text="Step 9/12")
            await interaction.response.edit_message(embed=embed, view=TotalGamesView(interaction, self.schedule_data))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

class TotalGamesView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data
        self.add_item(TotalGamesDropdown(interaction, schedule_data))

class TotalGamesDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        self.interaction = interaction
        self.schedule_data = schedule_data

        options = []
        for number in range(10, 1, -1):
            options.append(nextcord.SelectOption(label=str(number), value=str(number)))

        super().__init__(placeholder="Select Total Games", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            total_games = interaction.data["values"][0]
            self.schedule_data["total_games"] = int(total_games)

            embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Interval Setup", description="Is this scrim recurring?", color=White)
            embed.set_footer(text="Step 10/12")
            await interaction.response.edit_message(embed=embed, view=IntervalView(interaction, self.schedule_data))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

class IntervalView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data

        yes_button = nextcord.ui.Button(style=nextcord.ButtonStyle.success, label="Yes")
        yes_button.callback = self.create_callback("Yes")
        self.add_item(yes_button)

        no_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="No")
        no_button.callback = self.create_callback("No")
        self.add_item(no_button)

        cancel_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="Cancel")
        cancel_button.callback = self.create_callback("Cancel")
        self.add_item(cancel_button)

    def create_callback(self, action):
        async def callback(interaction: nextcord.Interaction):
            try:
                if action == "Yes":
                    self.schedule_data["interval"] = True
                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Interval Setup", description="How long is the interval between each scrim?", color=White)
                    embed.set_footer(text="Step 12/13")
                    await interaction.response.edit_message(embed=embed, view=IntervalTimeView(interaction, self.schedule_data))

                elif action == "No":
                    self.schedule_data["interval"] = False
                    self.schedule_data["recurrence"] = None
                    self.schedule_data["next_interval"] = None

                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Registration Channel", description=f"Input the Channel ID for where registrations will be put", color=White)
                    embed.set_footer(text="Step 12/12")

                    await interaction.response.edit_message(embed=embed, view=RegistrationChannelView(interaction, self.schedule_data))

                elif action == "Cancel":
                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Scrim Scheduling Cancelled", description="Scrim Scheduling has been cancelled", color=Red)
                    await interaction.response.edit_message(embed=embed, view=None)

            except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())
        return callback

class IntervalTimeView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data

        daily_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Daily")
        daily_button.callback = self.create_callback("Daily")
        self.add_item(daily_button)

        weekly_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Weekly")
        weekly_button.callback = self.create_callback("Weekly")
        self.add_item(weekly_button)

        fortnightly_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Fortnightly")
        fortnightly_button.callback = self.create_callback("Fortnightly")
        self.add_item(fortnightly_button)

        monthly_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Monthly")
        monthly_button.callback = self.create_callback("Monthly")
        self.add_item(monthly_button)

        cancel_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="Cancel")
        cancel_button.callback = self.create_callback("cancel")
        self.add_item(cancel_button)

    def create_callback(self, interval):
        async def callback(interaction: nextcord.Interaction):
            try:
                if interval != "cancel":
                    self.schedule_data["recurrence"] = interval

                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Registration Channel", description=f"Input the Channel ID for where registrations will be put", color=White)
                    embed.set_footer(text="Step 12/12")
                    await interaction.response.edit_message(embed=embed, view=RegistrationChannelView(interaction, self.schedule_data))

                else:
                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Scrim Scheduling Cancelled", description="Scrim Scheduling has been cancelled", color=Red)
                    await interaction.response.edit_message(embed=embed, view=None)

            except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())
        return callback

class RegistrationChannelView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data

        input_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Input Channel")
        input_button.callback = self.create_callback("input")
        self.add_item(input_button)

        cancel_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="Cancel")
        cancel_button.callback = self.create_callback("cancel")
        self.add_item(cancel_button)

    def create_callback(self, custom_id):
        async def callback(interaction: nextcord.Interaction):
            try:
                if custom_id == "input":
                    await interaction.response.send_modal(modal=RegistrationChannelModal(interaction, self.schedule_data))

                elif custom_id == "cancel":
                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Scrim Scheduling Cancelled", description="Scrim Scheduling has been cancelled", color=Red)
                    await interaction.response.edit_message(embed=embed, view=None)

            except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())
        return callback

class RegistrationChannelModal(nextcord.ui.Modal):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(title="Registration Channel", timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data

        self.input = nextcord.ui.TextInput(
            label="Registration Channel",
            style=nextcord.TextInputStyle.short,
            placeholder="Enter Registration Channel",
            min_length=1,
            max_length=30)

        self.input.callback = self.callback
        self.add_item(self.input)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            registration_channel = self.input.value

            if registration_channel.isnumeric() == True:
                registration_channel = int(registration_channel)
                channel = interaction.guild.get_channel(registration_channel)

                if channel != None: # Channel Exists
                    scrims = getScrims(interaction.guild.id)
                    channel_used = False

                    for scrim in scrims:
                        if registration_channel == scrim["scrimConfiguration"]["registrationChannel"]:
                            channel_used = True

                    if channel_used != True: # Channel Not Used

                        self.schedule_data["registration_channel"] = registration_channel

                        embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Confirmation", description=f"Confirm Scheduling of: **{self.schedule_data['scrim_name']}**\n\nTime: <t:{self.schedule_data['scrim_time']}:f> (**{self.schedule_data['scrim_time']}**)\nMatch Format: **{self.schedule_data['match_format']}**\nPick/Ban Mode: **{self.schedule_data['pickban_mode']}**\nTeam Type: **{self.schedule_data['team_type']}**\nMax Teams: **{self.schedule_data['max_teams']}**\nTotal Games: **{self.schedule_data['total_games']}**\nInterval: **{self.schedule_data['interval']}**\nRecurrence: **{self.schedule_data['recurrence']}**\nRegistration Channel: <#{self.schedule_data['registration_channel']}>", color=White)
                        await interaction.response.edit_message(embed=embed, view=ConfirmationView(interaction, self.schedule_data))

                    else: # Channel Used
                        embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Registration Channel", description="This channel is already being used for another scrim, please choose another", color=Red)
                        embed.set_footer(text="Step 12/12")
                        await interaction.response.edit_message(embed=embed, view=RegistrationChannelView(interaction, self.schedule_data))

                else: # Channel Doesn't Exist
                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Registration Channel", description="Please enter a valid channel ID", color=Red)
                    embed.set_footer(text="Step 12/12")
                    await interaction.response.edit_message(embed=embed, view=RegistrationChannelView(interaction, self.schedule_data))

            else: # Not an ID
                embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Registration Channel", description="Please enter a valid channel ID", color=Red)
                embed.set_footer(text="Step 13/13")
                await interaction.response.edit_message(embed=embed, view=RegistrationChannelView(interaction, self.schedule_data))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

class ConfirmationView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, schedule_data):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.schedule_data = schedule_data

        confirm_button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label="Confirm")
        confirm_button.callback = self.create_callback("confirm")
        self.add_item(confirm_button)

        cancel_button = nextcord.ui.Button(style=nextcord.ButtonStyle.danger, label="Cancel")
        cancel_button.callback = self.create_callback("cancel")
        self.add_item(cancel_button)

    def create_callback(self, custom_id):
        async def callback(interaction: nextcord.Interaction):
            try:
                if custom_id == "confirm":
                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Confirmation", description="Scrim is being scheduled, this may take a few moments...", color=White)
                    await interaction.response.edit_message(embed=embed, view=None)

                    dateandtime = datetime.datetime.fromtimestamp(int(self.schedule_data["scrim_time"]))
                    discord_time = dateandtime.astimezone(datetime.timezone.utc)
                    formatted_time = nextcord.utils.format_dt(dateandtime, "f")

                    try: # Create Event
                        event = await interaction.guild.create_scheduled_event(
                            name=self.schedule_data['scrim_name'],
                            description="Scrim Scheduled by Deadlock Scrim Bot",
                            entity_type=nextcord.ScheduledEventEntityType.external,
                            metadata=nextcord.EntityMetadata(location=interaction.guild.name),
                            start_time=discord_time,
                            end_time=discord_time + datetime.timedelta(hours=4),
                            privacy_level=nextcord.ScheduledEventPrivacyLevel.guild_only,
                            reason="Scrim Scheduled by Deadlock Scrim Bot"
                            )

                        # Calculate Next Interval
                        if self.schedule_data["interval"] == True:
                            if self.schedule_data["recurrence"] == "Daily": next_interval = 86400
                            elif self.schedule_data["recurrence"] == "Weekly": next_interval = 604800
                            elif self.schedule_data["recurrence"] == "Fortnightly": next_interval = 1209600
                            elif self.schedule_data["recurrence"] == "Monthly": next_interval = 2419200

                            self.schedule_data["next_interval"] = self.schedule_data["scrim_time"] + next_interval

                        # Save Scrim
                        DB[str(command["guildID"])]["ScrimData"].insert_one({
                            "scrimName": self.schedule_data['scrim_name'],
                            "scrimEpoch": self.schedule_data['scrim_time'],

                            "scrimConfiguration": {
                                "maxTeams": self.schedule_data['max_teams'],
                                "teamType": self.schedule_data['team_type'],
                                "pickBanMode": self.schedule_data['pickban_mode'],
                                "pickBanTime": self.schedule_data['pickban_time'],
                                "matchFormat": self.schedule_data['match_format'],
                                "totalGames": self.schedule_data['total_games'],
                                "registrationChannel": self.schedule_data['registration_channel'],
                                "registrationMessages": [],
                                "playerIDs": [],
                                "open": {
                                    "checkin": False,
                                    "pickban": False
                                },
                                "complete" : {
                                    "pickban": False,
                                    "checkin": False,
                                    "setup": False
                                },
                                "interval": {
                                    "repeating": self.schedule_data['interval'],
                                    "interval": self.schedule_data['recurrence'],
                                    "next": self.schedule_data['next_interval']
                                },
                                "IDs": {
                                    "vcCategory": None,
                                    "discordEvent": event.id,
                                    "reserveMessage": None
                                }},
                            "scrimTeams": {}
                            })

                        embed = nextcord.Embed(title=f"Scrim Scheduled: {self.schedule_data['scrim_name']} // Scheduled", description=f"\nTime: <t:{self.schedule_data['scrim_time']}:f> (**{self.schedule_data['scrim_time']}**)\nMatch Format: **{self.schedule_data['match_format']}**\nPick/Ban Mode: **{self.schedule_data['pickban_mode']}**\nTeam Type: **{self.schedule_data['team_type']}**\nMax Teams: **{self.schedule_data['max_teams']}**\nTotal Games: **{self.schedule_data['total_games']}**\nInterval: **{self.schedule_data['interval']}**\nRecurrence: **{self.schedule_data['recurrence']}**\nRegistration Channel: <#{self.schedule_data['registration_channel']}>", color=White)

                        await interaction.edit_original_message(embed=embed)

                        channels = getChannels(interaction.guild.id)
                        messages = getMessages(interaction.guild.id)
                        message = splitMessage(messages["scrimRegistration"], interaction.guild.id, self.schedule_data['scrim_name'])

                        channel = interaction.guild.get_channel(self.schedule_data['registration_channel'])
                        embed = nextcord.Embed(title=message[0], description=message[1], color=White)
                        await channel.send(embed=embed)

                        channel = interaction.guild.get_channel(channels["scrimLogChannel"])
                        embed = nextcord.Embed(title=f"{self.schedule_data['scrim_name']} has been Scheduled", description=f"{self.schedule_data['scrim_name']} was scheduled for {formatted_time}\nMatch Format: **{self.schedule_data['match_format']}**\nPick/Ban Mode: **{self.schedule_data['pickban_mode']}**", color=Green)
                        embed.set_footer(text=f"Scheduled at {datetime.datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC by @{interaction.user.name}")
                        await channel.send(embed=embed)

                        formatOutput(output=f"   {self.schedule_data['scrim_name']} has been scheduled", status="Good", guildID=command["guildID"])

                    except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

                elif custom_id == "cancel":
                    embed = nextcord.Embed(title=f"Scrim Scheduling: {self.schedule_data['scrim_name']} // Scrim Scheduling Cancelled", description="Scrim Scheduling has been cancelled", color=Red)
                    await interaction.response.edit_message(embed=embed, view=None)

            except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())
        return callback

class Command_schedule_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="schedule", description="Schedule Scrims using a series of menus (Max 7 Scrims at a time). **Staff Only**", default_member_permissions=(nextcord.Permissions(administrator=True)))
    async def schedule(self, interaction: nextcord.Interaction):
        global command
        command = {"name": interaction.application_command.name, "userID": interaction.user.id, "guildID": interaction.guild.id}
        formatOutput(output=f"/{command['name']} Used by {command['userID']} | @{interaction.user.name}", status="Normal", guildID=command["guildID"])

        try: await interaction.response.defer(ephemeral=True)
        except: pass # Discord can sometimes error on defer()

        scrims = getScrims(command["guildID"])
        if len(scrims) >= 7: # Schedule Limit
            embed = nextcord.Embed(title="Scrim Scheduling // Error", description="You can only have up to 7 scrims scheduled at a time", color=Red)
            await interaction.edit_original_message(embed=embed)

        else:
            embed = nextcord.Embed(title="Scrim Scheduling // Name your Scrim", description="What would you like to name your Scrim?", color=White)
            embed.set_footer(text="Step 1/13")
            await interaction.edit_original_message(embed=embed, view=NamingView(interaction, scrims))

def setup(bot):
    bot.add_cog(Command_schedule_Cog(bot))