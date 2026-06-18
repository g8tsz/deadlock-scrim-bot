import nextcord
import traceback
import datetime
import signal
import sys
from nextcord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from Tasks import *
from BotData.colors import *
from Keys import BOT_TOKEN, DB, BOT_VERSION, ERROR_REPORT_GUILD_ID, ERROR_REPORT_CHANNEL_ID
from BotCore.bot_holder import set_bot
from BotCore.scrim_utils import delete_scrim_roles

command_list = admin_command_list = [
    "registrations", "register", "schedule", "help", "configure", "score", "feedback",
    "scrims", "team_list", "pickban_list", "player_list", "give_role", "save",
    "pickban_draft", "create_team", "team", "staff_tools",
]
public_command_list = [
    "registrations", "register_solo", "register_duo", "register_trio", "register_six",
    "register_my_team", "unregister", "help", "feedback", "create_team", "team", "health",
]
admin_command_list = [
    "registrations", "register_solo", "register_duo", "register_trio", "register_six",
    "register_my_team", "unregister", "schedule", "help", "configure", "score", "feedback",
    "scrims", "team_list", "pickban_list", "player_list", "give_role", "save",
    "pickban_draft", "create_team", "team", "staff_tools", "health",
]

intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
bot = commands.Bot(intents=intents)
set_bot(bot)

def formatOutput(output, status, guildID):
    current_time = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S.%f')[:-3]
    if status == "Normal":
        print(f"| {current_time} || {CBOLD} {guildID} {CLEAR} {output}")
    elif status == "Good":
        print(f"{CGREEN}| {current_time} || {CBOLD} {guildID} {CLEAR} {output} {CLEAR}")
    elif status == "Error":
        print(f"{CRED}| {current_time} || {CBOLD} {guildID} {CLEAR} {output} {CLEAR}")
    elif status == "Warning":
        print(f"{CYELLOW}| {current_time} || {CBOLD} {guildID} {CLEAR} {output} {CLEAR}")


async def errorResponse(error, command, interaction: nextcord.Interaction, error_traceback):
    embed = nextcord.Embed(
        title="**Error**",
        description=f"Something went wrong while running `/{command['name']}`.\nError: {error}",
        color=Red,
    )
    embed.set_footer(text="Error was automatically logged for review")
    try:
        await interaction.response.edit_message(embed=embed, view=None)
    except Exception:
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception:
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception:
                try:
                    await interaction.send(embed=embed, ephemeral=True)
                except Exception:
                    pass

    formatOutput(
        output=f"   Something went wrong while running /{command['name']}. Error: {error}",
        status="Error",
        guildID=command['guildID'],
    )
    report = nextcord.Embed(
        title="**Error Report**",
        description=f"Error while running /{command['name']}.\nError: {error}",
        color=Red,
    )
    report.set_footer(text=f"Guild: {command['guildID']} | User: {interaction.user.name}/{command['userID']}")
    if ERROR_REPORT_GUILD_ID and ERROR_REPORT_CHANNEL_ID:
        try:
            channel = await bot.get_guild(ERROR_REPORT_GUILD_ID).fetch_channel(ERROR_REPORT_CHANNEL_ID)
            await channel.send(embed=report)
        except Exception:
            pass


def getAllGuilds():
    guilds = []
    for db in DB.list_database_names():
        if db in ("DeadlockAutomation", "local", "admin"):
            continue
        guilds.append(int(db))
    return guilds


def getDefaults(type):
    default_data = DB["DeadlockAutomation"]["Defaults"].find_one({type: {'$exists': True}})[type]
    return {type: default_data}


def getGuildConfig(guildID):
    doc = DB[str(guildID)]['Config'].find_one({'Config': {'$exists': True}})
    if doc:
        return doc['Config']
    return {
        "config": getConfigData(guildID),
        "channels": getChannels(guildID),
        "messages": getMessages(guildID),
        "presets": getPresets(guildID),
    }


def getGuildData(guildID):
    return DB[str(guildID)]['GuildData'].find_one({'guildID': guildID})


def getGuildTeams(guildID, teamName=None):
    if teamName:
        team = DB[str(guildID)]["Teams"].find_one({teamName: {'$exists': True}})
        return team[teamName] if team else None

    teams = list(DB[str(guildID)]["Teams"].find({}))
    formatted_list = []
    for team in teams:
        for team_name, data in team.items():
            if team_name != '_id':
                formatted_list.append(data)
    return formatted_list


def getScrims(guildID):
    return list(DB[str(guildID)]["ScrimData"].find({}))


def getScrim(guildID, scrim_name):
    return DB[str(guildID)]["ScrimData"].find_one({"scrimName": scrim_name})


def getScrimInfo(guildID, scrim_name):
    scrim_data = DB[str(guildID)]["ScrimData"].find_one({"scrimName": scrim_name})
    return {"scrimName": scrim_data["scrimName"], "scrimEpoch": scrim_data["scrimEpoch"]}


def _team_member_ids(team):
    ids = []
    for key in ("teamPlayer1", "teamPlayer2", "teamPlayer3", "teamPlayer4", "teamPlayer5", "teamPlayer6"):
        val = team.get(key)
        if val is not None:
            ids.append(int(val))
    for key in ("teamSub1", "teamSub2"):
        val = team.get(key)
        if val is not None:
            ids.append(int(val))
    return ids


start_time = datetime.datetime.now()
formatOutput(f"{CBOLD} DEADLOCK SCRIM BOT TERMINAL {CLEAR}", status="Good", guildID="STARTUP")
formatOutput("Loading Commands...", status="Normal", guildID="STARTUP")

for command in command_list:
    try:
        bot.load_extension(f"Commands.{command}")
        formatOutput(f"    /{command} Successfully Loaded", status="Good", guildID="STARTUP")
    except Exception as e:
        formatOutput(f"    /{command} Failed to Load // Error: {e}", status="Warning", guildID="STARTUP")

formatOutput("Commands Loaded", status="Normal", guildID="STARTUP")
formatOutput("Connecting To Database...", status="Normal", guildID="STARTUP")

db_connected = False
try:
    DB.admin.command('ping')
    db_connected = True
    formatOutput("Connected to Database", status="Good", guildID="STARTUP")
except Exception:
    formatOutput("Failed to Connect to Database", status="Error", guildID="STARTUP")

if not db_connected:
    formatOutput("Cannot start bot without a database connection.", status="Error", guildID="STARTUP")
    raise SystemExit(1)

formatOutput("Connecting to Discord...", status="Normal", guildID="STARTUP")


@bot.event
async def on_ready():
    startup_time = round((datetime.datetime.now() - start_time).total_seconds() * 1000)
    formatOutput(f"{bot.user.name} has connected to Discord (Took {startup_time}ms)", status="Good", guildID="STARTUP")
    formatOutput("Resuming Views...", status="Normal", guildID="STARTUP")

    from Commands.register_trio import AutomatedRegisterView
    view_count = 1
    success_count = deleted_messages = 0
    messageData = list(DB.DeadlockAutomation.SavedMessages.find({}))
    for entry in messageData:
        try:
            guild = bot.get_guild(entry["guildID"])
            channel = guild.get_channel(entry["channelID"])
            message = await channel.fetch_message(entry["messageID"])
            view = AutomatedRegisterView(
                entry["interactionID"],
                entry.get("viewType", "registration"),
                entry["guildID"],
                entry["channelID"],
                entry.get("scrimName"),
                entry.get("teamKey"),
            )
            await message.edit(view=view)
            formatOutput(f"   Resuming Views: {view_count}/{len(messageData)}", status="Good", guildID="RESUMER")
            view_count += 1
            success_count += 1
        except Exception as e:
            if "Unknown Message" in str(e):
                DB.DeadlockAutomation.SavedMessages.delete_one({"messageID": entry["messageID"]})
                formatOutput(
                    f"   Resuming Views: {view_count}/{len(messageData)} | Message Deleted",
                    status="Warning",
                    guildID="RESUMER",
                )
                deleted_messages += 1
                view_count += 1
            else:
                formatOutput(
                    output=f"   Something went wrong while resuming views. Error: {e} | {traceback.format_exc()}",
                    status="Error",
                    guildID="RESUMER",
                )

    formatOutput(f"Resumed {success_count}/{len(messageData)} Views", status="Good", guildID="RESUMER")
    formatOutput(f"Deleted {deleted_messages} Messages", status="Warning", guildID="RESUMER")

    await startScheduler()
    formatOutput(f"BOT VERSION {BOT_VERSION}", status="Normal", guildID="STARTUP")
    await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name=f"/help | Version {BOT_VERSION}"))
    formatOutput("---------------------------------", status="Normal", guildID="STARTUP")


async def registration_updater(config_data, guildID, scrim_name, phase):
    toggle_key = "togglePickBan" if phase == "pickban" else f"toggle{phase.capitalize()}"
    time_key = f"{toggle_key}Time"
    formatOutput(
        f"   Opening {phase}, Less than {config_data[time_key]} hour(s) until start",
        status="Normal",
        guildID=guildID,
    )
    channels = getChannels(guildID)
    guild = bot.get_guild(guildID)
    try:
        scrim = getScrim(guildID, scrim_name)
        teams = getTeams(guildID, scrim_name)

        from Commands.register_trio import AutomatedRegisterView
        reg_channel = bot.get_channel(scrim["scrimConfiguration"]["registrationChannel"])
        for team_key, team_data in teams.items():
            messageID = team_data["messageID"]
            DB.DeadlockAutomation.SavedMessages.find_one_and_update(
                {"messageID": messageID},
                {"$set": {"viewType": phase}},
            )
            message = await reg_channel.fetch_message(messageID)
            await message.edit(view=AutomatedRegisterView(
                team_data["teamPlayer1"],
                phase,
                guildID,
                scrim["scrimConfiguration"]["registrationChannel"],
                scrim_name,
                team_key,
            ))

        msg_key = automation_message_key(phase)
        message_parts = splitMessage(getMessages(guildID)[msg_key], guildID, scrim_name)
        channel = bot.get_channel(scrim["scrimConfiguration"]["registrationChannel"])
        embed = nextcord.Embed(title=message_parts[0], description=message_parts[1], color=White)
        await channel.send(embed=embed)

        if phase == "pickban" and scrim["scrimConfiguration"].get("pickBanMode") == "Random":
            await apply_random_bans(guildID, scrim_name, scrim)

        if phase == "checkin" and guild:
            for _, team_data in teams.items():
                captain_id = team_data.get("teamPlayer1")
                if not captain_id:
                    continue
                member = guild.get_member(int(captain_id))
                if member:
                    try:
                        await member.send(
                            embed=nextcord.Embed(
                                title=f"Check-in open — {scrim_name}",
                                description="Your scrim check-in window is now open. Use the button on your registration message.",
                                color=Green,
                            )
                        )
                    except Exception:
                        pass

        log_embed = nextcord.Embed(title=f"{phase.capitalize()} is Open!", color=Green)
        log_embed.set_footer(text=f"Automatically opened {config_data[time_key]} hour(s) before start")
        log_channel = bot.get_channel(channels["scrimLogChannel"])
        if log_channel:
            await log_channel.send(embed=log_embed)

        DB[str(guildID)]["ScrimData"].find_one_and_update(
            {"scrimName": scrim_name},
            {"$set": {
                f"scrimConfiguration.open.{phase}": True,
                f"scrimConfiguration.complete.{phase}": True,
            }},
        )
        formatOutput(f"      Automation | {phase} opened", status="Good", guildID=guildID)
    except Exception as e:
        formatOutput(
            output=f"   Automation | Something went wrong while opening {phase}. Error: {e} {traceback.format_exc()}",
            status="Error",
            guildID=guildID,
        )
        log_channel = bot.get_channel(channels.get("scrimLogChannel"))
        if log_channel:
            embed = nextcord.Embed(title="Error Encountered", description=f"Error while opening {phase}.\nError: {e}", color=Red)
            await log_channel.send(embed=embed)


async def apply_random_bans(guildID, scrim_name, scrim):
    import random
    from BotData.herodata import HERO_NAMES
    teams = getTeams(guildID, scrim_name)
    team_keys = list(teams.keys())[:2]
    if len(team_keys) < 2:
        return
    pool = HERO_NAMES.copy()
    random.shuffle(pool)
    for idx, team_key in enumerate(team_keys):
        ban = pool[idx]
        DB[str(guildID)]["ScrimData"].update_one(
            {"scrimName": scrim_name},
            {"$addToSet": {f"scrimTeams.{team_key}.teamPickBans.game1.bans": ban}},
        )


async def setup_handler(config_data, guildID, scrim_name):
    error = False
    message = embed = None
    started_at = datetime.datetime.utcnow()
    channels = getChannels(guildID)
    scrim = getScrim(guildID, scrim_name)
    scrim_info = getScrimInfo(guildID, scrim_name)
    team_data = getTeams(guildID, scrim_name)
    team_items = list(team_data.items())
    guild = bot.get_guild(guildID)

    formatOutput(
        f"   Starting Setup, less than {config_data['toggleSetupTime']} hour(s) until start",
        status="Normal",
        guildID=guildID,
    )

    try:
        embed = nextcord.Embed(title=f"{scrim_info['scrimName']} is starting!", color=Green)
        embed.add_field(name="Preparing", value="0%", inline=True)
        embed.add_field(name="Teams", value=f"0/{len(team_items)}", inline=True)
        embed.set_footer(text=f"Automatically started {config_data['toggleSetupTime']} hour(s) before start")
        log_channel = bot.get_channel(channels["scrimLogChannel"])
        message = await log_channel.send(embed=embed)
    except Exception as e:
        formatOutput(output=f"   Setup failed to start: {e}", status="Error", guildID=guildID)
        return

    try:
        category = await guild.create_category_channel(name=f"{scrim_name} Team VCs")
        DB[str(guildID)]["ScrimData"].update_one(
            {"scrimName": scrim_name},
            {"$set": {"scrimConfiguration.IDs.vcCategory": category.id}},
        )
        scrim = getScrim(guildID, scrim_name)
    except Exception as e:
        error = True
        formatOutput(output=f"   Setup category failed: {e}", status="Error", guildID=guildID)

    caster_role = None
    if config_data.get("caster") and config_data.get("casterRole"):
        caster_role = guild.get_role(config_data["casterRole"])

    processed = 0
    if not error:
        for team_key, team in team_items:
            try:
                role = await guild.create_role(name=team["teamName"], mentionable=True)
                DB[str(guildID)]["ScrimData"].update_one(
                    {"scrimName": scrim_name},
                    {"$set": {f"scrimTeams.{team_key}.teamSetup.roleID": role.id}},
                )
                team = getTeams(guildID, scrim_name)[team_key]
                team_role = guild.get_role(team["teamSetup"]["roleID"])
                for member_id in _team_member_ids(team):
                    member = guild.get_member(member_id)
                    if member and team_role:
                        await member.add_roles(team_role)

                vc = await guild.create_voice_channel(name=team["teamName"], category=category)
                DB[str(guildID)]["ScrimData"].update_one(
                    {"scrimName": scrim_name},
                    {"$set": {f"scrimTeams.{team_key}.teamSetup.channelID": vc.id}},
                )
                team_role = guild.get_role(team["teamSetup"]["roleID"])
                if team_role:
                    overwrite = nextcord.PermissionOverwrite(connect=True, view_channel=True)
                    await vc.set_permissions(team_role, overwrite=overwrite)
                if caster_role:
                    overwrite = nextcord.PermissionOverwrite(connect=True, view_channel=True)
                    await vc.set_permissions(caster_role, overwrite=overwrite)
                await vc.set_permissions(guild.default_role, overwrite=nextcord.PermissionOverwrite(connect=False))

                processed += 1
                embed.set_field_at(1, name="Teams", value=f"{processed}/{len(team_items)}", inline=True)
                await message.edit(embed=embed)
            except Exception as e:
                error = True
                formatOutput(output=f"   Setup team failed for {team_key}: {e}", status="Error", guildID=guildID)
                break

    if not error:
        time_taken = datetime.datetime.strftime(
            datetime.datetime(1, 1, 1) + (datetime.datetime.utcnow() - started_at), "%M:%S"
        )
        embed.title = f"{scrim_info['scrimName']} has started!"
        embed.color = Green
        embed.set_footer(text=f"Setup completed in {time_taken}")
        await message.edit(embed=embed)
        DB[str(guildID)]["ScrimData"].update_one(
            {"scrimName": scrim_name},
            {"$set": {"scrimConfiguration.complete.setup": True}},
        )
        formatOutput("      Automation | Setup completed", status="Good", guildID=guildID)
    else:
        embed.title = "SETUP FAILED"
        embed.color = Red
        await message.edit(embed=embed)
        formatOutput("      Automation | Setup failed", status="Error", guildID=guildID)


async def event_checker():
    for id in DB.list_database_names():
        if id in ("DeadlockAutomation", "admin", "local"):
            continue
        guildID = int(id)
        guild = bot.get_guild(guildID)
        guild_label = guild.name if guild else str(guildID)
        scrims = getScrims(guildID)

        if not scrims:
            formatOutput(f"   No scheduled scrims found for {guild_label}", status="Warning", guildID=guildID)
            continue

        formatOutput(f"Running Event Checker Scheduler for {guild_label}...", status="Normal", guildID=guildID)
        for scrim in scrims:
            scrim_name = scrim["scrimName"]
            scrim_epoch = int(scrim["scrimEpoch"])
            current_epoch = int(datetime.datetime.now().timestamp())
            hours_until_start = (scrim_epoch - current_epoch) / 3600
            config_data = getConfigData(guildID)

            if hours_until_start <= -4:
                formatOutput(f"   Ending {scrim_name} | started more than 4 hours ago", status="Normal", guildID=guildID)
                team_data = getTeams(guildID, scrim_name)

                if config_data.get("toggleSetup") and guild:
                    try:
                        vc_category = scrim["scrimConfiguration"]["IDs"].get("vcCategory")
                        for _, data in team_data.items():
                            channel_id = data.get("teamSetup", {}).get("channelID")
                            if channel_id:
                                vc = bot.get_channel(channel_id)
                                if vc:
                                    await vc.delete()
                        if vc_category:
                            cat = guild.get_channel(vc_category)
                            if cat:
                                await cat.delete()
                        await delete_scrim_roles(guild, team_data)
                        formatOutput(f"   Deleted VCs and roles for {scrim_name}", status="Good", guildID=guildID)
                    except Exception as e:
                        formatOutput(f"   Failed to delete VCs for {scrim_name}: {e}", status="Error", guildID=guildID)
                        await logAction(guildID, "AUTOMATED ACTION", f"Failed to delete VCs. Error: {e}", "Error")

                try:
                    reg_channel = bot.get_channel(scrim["scrimConfiguration"]["registrationChannel"])
                    for _, data in team_data.items():
                        messageID = data.get("messageID")
                        if messageID and reg_channel:
                            msg = await reg_channel.fetch_message(messageID)
                            await msg.delete()
                            DB.DeadlockAutomation.SavedMessages.delete_one({"messageID": messageID})
                    formatOutput(f"   Deleted registrations for {scrim_name}", status="Good", guildID=guildID)
                except Exception as e:
                    formatOutput(f"   Failed to delete registrations for {scrim_name}: {e}", status="Error", guildID=guildID)

                DB[str(guildID)]["ScrimData"].update_one({"scrimName": scrim_name}, {"$set": {"scrimTeams": {}}})

                if scrim['scrimConfiguration']['interval']['repeating']:
                    interval_name = scrim['scrimConfiguration']['interval']['interval']
                    intervals = {"Daily": 86400, "Weekly": 604800, "Fortnightly": 1209600, "Monthly": 2419200}
                    next_interval = intervals.get(interval_name, 604800)
                    new_epoch = scrim_epoch + next_interval
                    dateandtime = datetime.datetime.fromtimestamp(new_epoch, tz=datetime.timezone.utc)

                    DB[str(guildID)]["ScrimData"].update_one(
                        {"scrimName": scrim_name},
                        {"$set": {
                            "scrimEpoch": new_epoch,
                            "scrimConfiguration.interval.next": new_epoch + next_interval,
                            "scrimConfiguration.open.checkin": False,
                            "scrimConfiguration.open.pickban": False,
                            "scrimConfiguration.complete.pickban": False,
                            "scrimConfiguration.complete.checkin": False,
                            "scrimConfiguration.complete.setup": False,
                            "scrimTeams": {},
                        }},
                    )

                    if guild:
                        try:
                            await guild.get_scheduled_event(scrim['scrimConfiguration']['IDs']['discordEvent']).delete()
                        except Exception:
                            pass
                        event = await guild.create_scheduled_event(
                            name=scrim_name,
                            description="Scrim Scheduled by Deadlock Scrim Bot",
                            entity_type=nextcord.ScheduledEventEntityType.external,
                            metadata=nextcord.EntityMetadata(location=guild.name),
                            start_time=dateandtime,
                            end_time=dateandtime + datetime.timedelta(hours=4),
                            privacy_level=nextcord.ScheduledEventPrivacyLevel.guild_only,
                        )
                        DB[str(guildID)]["ScrimData"].update_one(
                            {"scrimName": scrim_name},
                            {"$set": {"scrimConfiguration.IDs.discordEvent": event.id}},
                        )

                        message_parts = splitMessage(getMessages(guildID)["scrimRegistration"], guildID, scrim_name)
                        channel = guild.get_channel(scrim["scrimConfiguration"]["registrationChannel"])
                        if channel:
                            embed = nextcord.Embed(title=message_parts[0], description=message_parts[1], color=White)
                            await channel.send(embed=embed)

                    formatOutput(f"   {scrim_name} has been rescheduled", status="Good", guildID=guildID)
                    await logAction(guildID, "AUTOMATED ACTION", f"Rescheduled {scrim_name}", "Good")
                else:
                    if guild:
                        try:
                            await guild.get_scheduled_event(scrim['scrimConfiguration']['IDs']['discordEvent']).delete()
                        except Exception:
                            pass
                    DB[str(guildID)]["ScrimData"].delete_one({"scrimName": scrim_name})
                    await logAction(guildID, "AUTOMATED ACTION", f"Ended {scrim_name}", "Good")

                formatOutput(f"   {scrim_name} has ended", status="Good", guildID=guildID)
            else:
                for action, phase in (("toggleCheckin", "checkin"), ("toggleSetup", "setup"), ("togglePickBan", "pickban")):
                    if not config_data.get(action):
                        continue
                    if scrim["scrimConfiguration"]["complete"].get(phase):
                        continue
                    time_key = f"{action}Time"
                    if hours_until_start < config_data.get(time_key, 999):
                        if phase in ("checkin", "pickban"):
                            await registration_updater(config_data, guildID, scrim_name, phase)
                        elif phase == "setup" and config_data.get("toggleSetup"):
                            await setup_handler(config_data, guildID, scrim_name)


async def global_messager():
    formatOutput("Running Global Messager Scheduler...", status="Normal", guildID="BACKGROUND TASK")
    messages = DB["DeadlockAutomation"]["ScheduledMessages"].find_one({"title": {"$exists": True}})
    if messages is None:
        formatOutput("   No Global Messages Found", status="Normal", guildID="BACKGROUND TASK")
        return

    description_parts = messages["message"].split('{}')
    description = '\n'.join(description_parts)
    embed = nextcord.Embed(title=messages["title"], description=description, color=messages["type"])
    embed.set_footer(text=messages["footer"])

    for guild_id in getAllGuilds():
        try:
            channel_id = getLogChannelId(guild_id)
            if channel_id:
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)
                    name = bot.get_guild(guild_id).name if bot.get_guild(guild_id) else guild_id
                    formatOutput(f"   Sent global message to {name}", status="Good", guildID=guild_id)
        except Exception as e:
            formatOutput(f"   Global message failed for {guild_id}: {e}", status="Error", guildID=guild_id)

    DB["DeadlockAutomation"]["ScheduledMessages"].delete_one({"title": {"$exists": True}})
    formatOutput("   All Global Messages Sent", status="Good", guildID="BACKGROUND TASK")


async def startScheduler():
    try:
        formatOutput("Starting Scheduler...", status="Normal", guildID="STARTUP")
        scheduler = AsyncIOScheduler()
        scheduler.add_job(event_checker, 'cron', minute='*/15', misfire_grace_time=600)
        scheduler.add_job(global_messager, 'cron', minute='*/1', misfire_grace_time=30)
        scheduler.start()
        formatOutput("Scheduler Started", status="Good", guildID="STARTUP")
    except Exception as e:
        formatOutput(f"Scheduler failed to start: {e} | {traceback.format_exc()}", status="Error", guildID="STARTUP")


@bot.event
async def on_guild_join(guild: nextcord.guild.Guild):
    try:
        formatOutput(f"Joined {guild.name} ({guild.id})", status="Good", guildID="JOINED GUILD")
        embed = nextcord.Embed(
            title="Deadlock Scrim Bot has Arrived",
            description="Run `/configure` to set up channels and automation for your Deadlock scrims.",
            color=White,
        )
        embed.set_footer(text=f"{BOT_VERSION}")
        if guild.system_channel:
            await guild.system_channel.send(embed=embed)

        if str(guild.id) not in DB.list_database_names():
            seedGuildConfig(guild.id)
        ensure_guild_indexes(guild.id)
    except Exception as e:
        formatOutput(output=f"   Guild join error for {guild.name}: {e}", status="Error", guildID="ON GUILD JOIN")


@bot.event
async def on_close():
    formatOutput("Bot shutting down gracefully.", status="Normal", guildID="SHUTDOWN")


def _graceful_exit(signum, frame):
    formatOutput(f"Received signal {signum}, closing bot.", status="Warning", guildID="SHUTDOWN")
    asyncio = __import__("asyncio")
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(bot.close())
    except Exception:
        sys.exit(0)


signal.signal(signal.SIGINT, _graceful_exit)
signal.signal(signal.SIGTERM, _graceful_exit)

bot.run(BOT_TOKEN)
