# Deadlock Scrim Bot

A Discord bot for running and managing **Deadlock** scrims.

Automates check-ins, hero pick/bans, team voice channel creation, scheduling, and scoring so organisers can focus on running matches instead of spreadsheets.

Forked and adapted from [apex-automation-scrim-bot](https://github.com/g8tsz/apex-automation-scrim-bot).

## Features

- **Registrations** — Solo, duo, trio, and six-stack scrim registration with team logos and substitutes
- **Scheduling** — schedule up to 7 scrims at a time through a guided menu
- **Check-ins & pick/bans** — automated check-in windows; Captain Draft and Random ban modes
- **Team tools** — create, edit, and manage persistent teams, roles, and rosters
- **Admin tooling** — player/team/pick-ban lists with filters, role assignments, channel saves, scoring
- **Configurable** — channels, roles, messages, presets, and timings are all editable per server

## Commands

Use `/help` in Discord for the full interactive list.

### For players

| Command | Description |
|---|---|
| `/help` | Open a help menu with details on every command |
| `/register_solo` | Register for a solo scrim |
| `/register_duo` | Register for a duo scrim |
| `/register_trio` | Register for a trio scrim |
| `/register_six` | Register for a six-stack scrim |
| `/registrations` | Show the full list of teams, players, and subs |
| `/create_team` | Create a team role and dashboard (you become captain) |
| `/team` | View your team or look up a team by name |
| `/feedback` | Submit feedback, suggestions, or bug reports |

### Admin or staff

| Command | Description |
|---|---|
| `/configure` | Configure every aspect of the bot for your server |
| `/schedule` | Schedule scrims via guided menus |
| `/pickban_draft` | Record hero picks and bans for scrim games |
| `/scrims` | View and edit all currently scheduled scrims |
| `/team_list` | Full list of teams, players, and subs with filters |
| `/pickban_list` | List pick/ban selections with filters |
| `/player_list` | Full list of players with filters |
| `/give_role` | Give roles to filtered users |
| `/save` | Save players, check-in status, and pick/bans to a channel |
| `/score` | View and record scrim match scores |

## Pick/Ban modes

| Mode | Description |
|---|---|
| **Captain Draft** | Captains record picks/bans via `/pickban_draft` |
| **Tournament** | Same recording flow as Captain Draft (structured rules coming soon) |
| **Random** | Server assigns random bans automatically when pick/bans open |
| **None** | Pick/bans disabled for this scrim |

Match formats: **Bo1**, **Bo3**, or **Bo5**.

## Setup

### Prerequisites

- **Python 3.12+**
- **MongoDB** (local or hosted)
- A Discord bot application — see the [Discord Developer Portal](https://discord.com/developers/applications)

### Data layout

The bot uses the shared database name **`DeadlockAutomation`** for defaults, saved messages, and other global collections. Each guild also uses a separate MongoDB database whose name is that guild's numeric Discord ID (`str(guild_id)`).

### Install

```bash
pip install -r requirements.txt
python setup_db.py
```

### Configuration

Copy the example keys file and fill in values:

```bash
cp Keys.example.py Keys.py
```

Required fields in `Keys.py`:

| Name | Purpose |
|---|---|
| `BOT_TOKEN` | Your Discord bot token |
| `DB` | A `pymongo.MongoClient` connected to your Mongo instance |
| `BOT_VERSION` | Version string shown in embeds |

### Run

```bash
python Main.py
```

## Hero roster

The bot includes all 38 playable Deadlock heroes in `BotData/herodata.py`.

## Credits

Built with [Nextcord](https://github.com/nextcord/nextcord).  
Based on [apex-automation-scrim-bot](https://github.com/g8tsz/apex-automation-scrim-bot) by g8tsz.
