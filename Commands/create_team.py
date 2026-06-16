import nextcord
import traceback
import time
from nextcord.ext import commands
from Main import formatOutput, errorResponse, getGuildTeams, getDefaults
from Keys import DB
from BotData.colors import *

placeholder_img = "https://github.com/user-attachments/assets/126753ee-e9a9-43d0-a21e-cbc32e555ff2"

class create_team_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="create_team", description="Create a team for scrims, generates a team role and dashboard. Creating a team makes you the captain")
    async def create_team(self, interaction: nextcord.Interaction,
        team_name: str = nextcord.SlashOption(name="team_name", description="The name of your team", required=True),
        team_player2: nextcord.Member = nextcord.SlashOption(name="team_player2", description="The second player on your team", required=True),
        team_player3: nextcord.Member = nextcord.SlashOption(name="team_player3", description="The third player on your team", required=True),
        team_sub1: nextcord.Member = nextcord.SlashOption(name="team_sub1", description="The first substitute for your team", required=False),
        team_sub2: nextcord.Member = nextcord.SlashOption(name="team_sub2", description="The second substitute for your team", required=False),
        team_coach: nextcord.Member = nextcord.SlashOption(name="team_coach", description="The coach for your team", required=False),
        team_logo: str = nextcord.SlashOption(name="team_logo", description="The logo for your team, use Dyno's /serverinfo in your server to grab the icon", required=False)):

        global command
        command = {'name': interaction.application_command.name, 'guildID': interaction.guild.id, 'userID': interaction.user.id}
        try: await interaction.response.defer(ephemeral=True)
        except: pass # Discord can sometimes error on defer()

        try:
            embed = nextcord.Embed(title="Validating team...", description="This may take a few minutes, please wait", color=White)
            await interaction.edit_original_message(embed=embed)

            player_ids = set()
            player_ids.add(interaction.user.id)
            player_ids.add(team_player2.id)
            player_ids.add(team_player3.id)
            if team_sub1: player_ids.add(team_sub1.id)
            if team_sub2: player_ids.add(team_sub2.id)
            if team_coach: player_ids.add(team_coach.id)

            # Check if a user is listed multiple times
            if len(player_ids) < 3 + (1 if team_sub1 else 0) + (1 if team_sub2 else 0) + (1 if team_coach else 0):
                embed = nextcord.Embed(title="Team Creation Error", description="You cannot have the same player listed multiple times!", color=Red)
                await interaction.edit_original_message(embed=embed)
                return

            # Check if team is valid (name, players, etc.)
            teams = getGuildTeams(interaction.guild.id)

            bot_list = checks = []
            if team_player2.bot == True: bot_list.append(str(team_player2.name))
            if team_player3.bot == True: bot_list.append(str(team_player3.name))
            if team_sub1 and team_sub1.bot == True: bot_list.append(str(team_sub1.name))
            if team_sub2 and team_sub2.bot == True: bot_list.append(str(team_sub2.name))
            if team_coach and team_coach.bot == True: bot_list.append(str(team_coach.name))

            if len(bot_list) > 0:
                embed = nextcord.Embed(title="Team Creation Error", description=f"The following users are bots and cannot be added to teams:\n{'\n'.join(bot_list)}", color=Red)
                await interaction.edit_original_message(embed=embed)
                return

            for team in teams:
                if team["teamName"].lower() == team_name.lower(): # Check if name is taken
                    embed = nextcord.Embed(title="Team Creation Error", description=f"Team name: **{team_name}** is already taken!", color=Red)
                    await interaction.edit_original_message(embed=embed)
                    return

                current_team_players = [team["teamCaptain"], team["teamPlayer2"], team["teamPlayer3"]]
                if team_sub1: current_team_players.append(team["teamSub1"])
                if team_sub2: current_team_players.append(team["teamSub2"])
                if team_coach: current_team_players.append(team["teamCoach"])

                for player_id in player_ids:
                    if player_id in current_team_players:
                        checks.append(player_id)

            if len(checks) > 0: # If any of the players are already in a team
                embed = nextcord.Embed(title="Team Creation Error", description=f"The following users are already in a team:\n{', '.join(f'<@{id}>' for id in checks)}", color=Red)
                await interaction.edit_original_message(embed=embed)
                return

            embed = nextcord.Embed(title="Creating team...", description="This may take a few minutes, please wait", color=White)
            await interaction.edit_original_message(embed=embed)

            created_time = int(time.time())
            embed = nextcord.Embed(title=team_name, description=f"-# Founded at <t:{created_time}:f>", color=White)
            embed.add_field(name="Captain", value=interaction.user.mention, inline=True)
            embed.add_field(name="Player 2", value=team_player2.mention, inline=True)
            embed.add_field(name="Player 3", value=team_player3.mention, inline=True)
            embed.add_field(name="Sub 1", value=team_sub1.mention if team_sub1 else "-# None", inline=True)
            embed.add_field(name="Sub 2", value=team_sub2.mention if team_sub2 else "-# None", inline=True)
            embed.add_field(name="Coach", value=team_coach.mention if team_coach else "-# None", inline=True)
            embed.set_footer(text="This is a preview of your team, please wait while we create it")
            if team_logo: # If no logo is provided, use a default image
                if team_logo.startswith("https://cdn.discordapp.com/icons/"): # Must submit a link to a server icon, for permanent access
                    embed.set_thumbnail(url=team_logo)

                else:
                    team_logo = placeholder_img
                    embed.set_thumbnail(url=team_logo)

            else:
                team_logo = placeholder_img
                embed.set_thumbnail(url=team_logo)

            await interaction.edit_original_message(embed=embed)

            # Create team role
            role = await interaction.guild.create_role(
                name=team_name,
                mentionable=True,
                color=nextcord.Color.from_rgb(0, 0, 0),
                reason=f"Deadlock Scrim Bot: Create team role for {team_name}",
            )

            # Hand out team role
            for id in player_ids:
                member = interaction.guild.get_member(id)
                await member.add_roles(role, reason=f"Deadlock Scrim Bot: Add {member.name} to team {team_name}")

            # Save team data to database
            template = getDefaults("Team")["Team"]

            template["roleID"] = role.id
            template["teamName"] = team_name
            template["teamCaptain"] = interaction.user.id
            template["teamPlayer2"] = team_player2.id
            template["teamPlayer3"] = team_player3.id
            if team_sub1: template["teamSub1"] = team_sub1.id
            if team_sub2: template["teamSub2"] = team_sub2.id
            if team_coach: template["teamCoach"] = team_coach.id
            template["createdAt"] = created_time
            template["teamLogo"] = team_logo
            template = {team_name: template}

            DB[str(interaction.guild.id)]["Teams"].insert_one(template)

            embed.set_footer(text=f"Team created successfully! You can now manage your team via /team")
            await interaction.edit_original_message(embed=embed)

            if team_logo != placeholder_img: # Send notice about custom logos
                embed = nextcord.Embed(title="Team Logo Notice", description="Custom team logo is subject to moderation by server admins. If your logo is removed it will be replaced with a default image.", color=Yellow)
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

def setup(bot):
    bot.add_cog(create_team_Cog(bot))