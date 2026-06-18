import csv
import io
import traceback
import nextcord
from nextcord.ext import commands
from Keys import DB, BOT_OWNER_ID
from Main import formatOutput, errorResponse, getScrims, getScrim, getAllGuilds
from Tasks import getPresets, logAction, getTeams
from BotCore.permissions import is_staff
from BotCore.context import set_command_context, get_command_context
from BotCore.db import write_audit
from BotData.colors import *


class StaffToolsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="health", description="Check bot and database connectivity")
    async def health(self, interaction: nextcord.Interaction):
        set_command_context("health", interaction.guild.id if interaction.guild else 0, interaction.user.id)
        db_ok = False
        try:
            DB.admin.command("ping")
            db_ok = True
        except Exception:
            pass
        discord_ok = self.bot.is_ready()
        embed = nextcord.Embed(title="Bot Health", color=Green if db_ok and discord_ok else Red)
        embed.add_field(name="Discord", value="OK" if discord_ok else "Not ready", inline=True)
        embed.add_field(name="MongoDB", value="OK" if db_ok else "Failed", inline=True)
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="audit", description="View recent bot audit log entries **Staff Only**")
    async def audit(self, interaction: nextcord.Interaction, limit: int = 10):
        if not is_staff(interaction):
            await interaction.response.send_message("Staff only.", ephemeral=True)
            return
        set_command_context("audit", interaction.guild.id, interaction.user.id)
        entries = list(DB[str(interaction.guild.id)]["AuditLog"].find({}).sort("_id", -1).limit(min(limit, 25)))
        if not entries:
            await interaction.response.send_message("No audit entries yet.", ephemeral=True)
            return
        lines = [f"**{e.get('category', 'Audit')}** | {e.get('user')} — {e.get('action')}" for e in entries]
        embed = nextcord.Embed(title="Audit Log", description="\n".join(lines), color=White)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="export", description="Export scrim data as CSV **Staff Only**")
    async def export(self, interaction: nextcord.Interaction, scrim_name: str):
        if not is_staff(interaction):
            await interaction.response.send_message("Staff only.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        teams = getTeams(interaction.guild.id, scrim_name)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["team", "type", "captain", "checkin", "pickban_complete"])
        for _, data in teams.items():
            writer.writerow([
                data.get("teamName"),
                data.get("teamType"),
                data.get("teamPlayer1"),
                data.get("teamStatus", {}).get("checkin"),
                data.get("teamStatus", {}).get("pickBanComplete"),
            ])
        await interaction.followup.send(file=nextcord.File(io.BytesIO(output.getvalue().encode()), filename=f"{scrim_name}.csv"))

    @nextcord.slash_command(name="bracket", description="Generate round 1 pairings for a scrim **Staff Only**")
    async def bracket(self, interaction: nextcord.Interaction, scrim_name: str):
        if not is_staff(interaction):
            await interaction.response.send_message("Staff only.", ephemeral=True)
            return
        scrim = getScrim(interaction.guild.id, scrim_name)
        teams = list(getTeams(interaction.guild.id, scrim_name).items())[: scrim["scrimConfiguration"]["maxTeams"]]
        if len(teams) < 2:
            await interaction.response.send_message("Need at least 2 teams.", ephemeral=True)
            return
        lines = []
        for i in range(0, len(teams) - 1, 2):
            t1 = teams[i][1]["teamName"]
            t2 = teams[i + 1][1]["teamName"] if i + 1 < len(teams) else "BYE"
            lines.append(f"Match {i//2 + 1}: **{t1}** vs **{t2}**")
        embed = nextcord.Embed(title=f"Bracket — {scrim_name}", description="\n".join(lines), color=White)
        await interaction.response.send_message(embed=embed)
        write_audit(interaction.guild.id, interaction.user.name, f"Generated bracket for {scrim_name}")

    @nextcord.slash_command(name="global_message", description="Queue a global message to all guild log channels **Staff Only**")
    async def global_message(
        self,
        interaction: nextcord.Interaction,
        title: str,
        message: str,
        footer: str = "Deadlock Scrim Bot",
    ):
        if not is_staff(interaction):
            await interaction.response.send_message("Staff only.", ephemeral=True)
            return
        DB["DeadlockAutomation"]["ScheduledMessages"].delete_many({})
        DB["DeadlockAutomation"]["ScheduledMessages"].insert_one({
            "title": title,
            "message": message,
            "footer": footer,
            "type": White,
        })
        await interaction.response.send_message("Global message queued for next scheduler run.", ephemeral=True)

    @nextcord.slash_command(name="caster", description="Show caster info and VC access for a scrim **Staff Only**")
    async def caster(self, interaction: nextcord.Interaction, scrim_name: str):
        if not is_staff(interaction):
            await interaction.response.send_message("Staff only.", ephemeral=True)
            return
        scrim = getScrim(interaction.guild.id, scrim_name)
        vc_cat = scrim["scrimConfiguration"]["IDs"].get("vcCategory")
        embed = nextcord.Embed(title=f"Caster Info — {scrim_name}", color=White)
        embed.add_field(name="VC Category", value=f"<#{vc_cat}>" if vc_cat else "Not created yet", inline=False)
        embed.add_field(name="Tip", value="Casters with the configured caster role can join team VCs after setup.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="scrim_template", description="List saved scrim presets **Staff Only**")
    async def scrim_template(self, interaction: nextcord.Interaction):
        if not is_staff(interaction):
            await interaction.response.send_message("Staff only.", ephemeral=True)
            return
        presets = getPresets(interaction.guild.id)
        lines = []
        for key, preset in presets.items():
            name = preset.get("presetName") or "(empty)"
            data = preset.get("presetData", {})
            lines.append(f"**{name}** — {data.get('teamType')} {data.get('matchFormat')} max {data.get('maxTeams')} teams")
        embed = nextcord.Embed(title="Scrim Templates (Presets)", description="\n".join(lines) or "No presets configured.", color=White)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="guild_stats", description="Multi-guild overview (bot owner)")
    async def guild_stats(self, interaction: nextcord.Interaction):
        if BOT_OWNER_ID and interaction.user.id != BOT_OWNER_ID:
            await interaction.response.send_message("Bot owner only.", ephemeral=True)
            return
        lines = []
        for gid in getAllGuilds():
            scrim_count = DB[str(gid)]["ScrimData"].count_documents({})
            guild = self.bot.get_guild(gid)
            name = guild.name if guild else str(gid)
            lines.append(f"**{name}** — {scrim_count} scrim(s)")
        embed = nextcord.Embed(title="Multi-Guild Stats", description="\n".join(lines) or "No guild databases.", color=White)
        await interaction.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(StaffToolsCog(bot))
