import unittest

from BotCore.pickban_rules import (
    games_for_format,
    hero_is_available,
    required_bans,
    team_pickban_complete,
)


class PickBanRulesTests(unittest.TestCase):
    def test_games_for_format(self):
        self.assertEqual(games_for_format("Bo3"), 3)

    def test_required_bans_tournament(self):
        self.assertEqual(required_bans("Tournament"), 3)

    def test_hero_availability(self):
        teams = {"a": {"teamPickBans": {"game1": {"bans": ["Haze"], "picks": []}}}}
        self.assertFalse(hero_is_available(teams, "game1", "Haze"))
        self.assertTrue(hero_is_available(teams, "game1", "Vindicta"))

    def test_team_pickban_incomplete(self):
        team = {"teamPickBans": {"game1": {"bans": [], "picks": []}}}
        self.assertFalse(team_pickban_complete(team, 1, "Captain Draft"))


if __name__ == "__main__":
    unittest.main()
