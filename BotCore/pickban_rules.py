"""Pick/ban validation and mode rules."""

from BotData.herodata import HERO_NAMES

TOURNAMENT_BANS_PER_TEAM = 3
CAPTAIN_DRAFT_BANS_PER_TEAM = 1
CAPTAIN_DRAFT_PICKS_PER_TEAM = 1


def games_for_format(match_format: str) -> int:
    return {"Bo1": 1, "Bo3": 3, "Bo5": 5}.get(match_format, 1)


def required_bans(mode: str) -> int:
    if mode == "Tournament":
        return TOURNAMENT_BANS_PER_TEAM
    if mode == "Captain Draft":
        return CAPTAIN_DRAFT_BANS_PER_TEAM
    return 0


def required_picks(mode: str) -> int:
    if mode in ("Tournament", "Captain Draft"):
        return CAPTAIN_DRAFT_PICKS_PER_TEAM
    return 0


def collect_used_heroes(scrim_teams: dict, game_key: str, exclude_team_key: str | None = None) -> set[str]:
    used = set()
    for key, team in scrim_teams.items():
        if exclude_team_key and key == exclude_team_key:
            continue
        pb = team.get("teamPickBans", {}).get(game_key, {})
        used.update(pb.get("bans", []))
        used.update(pb.get("picks", []))
    return used


def hero_is_available(scrim_teams: dict, game_key: str, hero: str, exclude_team_key: str | None = None) -> bool:
    return hero in HERO_NAMES and hero not in collect_used_heroes(scrim_teams, game_key, exclude_team_key)


def game_draft_complete(team_data: dict, game_key: str, mode: str) -> bool:
    if mode == "None":
        return True
    pb = team_data.get("teamPickBans", {}).get(game_key, {})
    bans = len(pb.get("bans", []))
    picks = len(pb.get("picks", []))
    return bans >= required_bans(mode) and picks >= required_picks(mode)


def team_pickban_complete(team_data: dict, total_games: int, mode: str) -> bool:
    if mode == "None":
        return True
    for i in range(1, total_games + 1):
        if not game_draft_complete(team_data, f"game{i}", mode):
            return False
    return True


def tournament_turn_label(action_index: int) -> str:
    order = ["Team A ban", "Team B ban", "Team A ban", "Team B ban", "Team A ban", "Team B ban"]
    if action_index < len(order):
        return order[action_index]
    return "Pick phase"
