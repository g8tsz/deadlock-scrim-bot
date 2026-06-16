### Deadlock heroes (playable roster)

HeroData = {
    "Abrams": {"Role": "Brawler"},
    "Apollo": {"Role": "Marksman"},
    "Bebop": {"Role": "Brawler"},
    "Billy": {"Role": "Assassin"},
    "Calico": {"Role": "Assassin"},
    "Celeste": {"Role": "Mystic"},
    "Drifter": {"Role": "Assassin"},
    "Dynamo": {"Role": "Mystic"},
    "Graves": {"Role": "Marksman"},
    "Grey Talon": {"Role": "Marksman"},
    "Haze": {"Role": "Assassin"},
    "Holliday": {"Role": "Marksman"},
    "Infernus": {"Role": "Brawler"},
    "Ivy": {"Role": "Mystic"},
    "Kelvin": {"Role": "Mystic"},
    "Lady Geist": {"Role": "Mystic"},
    "Lash": {"Role": "Brawler"},
    "McGinnis": {"Role": "Mystic"},
    "Mina": {"Role": "Assassin"},
    "Mirage": {"Role": "Assassin"},
    "Mo & Krill": {"Role": "Brawler"},
    "Paige": {"Role": "Mystic"},
    "Paradox": {"Role": "Mystic"},
    "Pocket": {"Role": "Mystic"},
    "Rem": {"Role": "Marksman"},
    "Seven": {"Role": "Mystic"},
    "Shiv": {"Role": "Assassin"},
    "Silver": {"Role": "Marksman"},
    "Sinclair": {"Role": "Marksman"},
    "The Doorman": {"Role": "Brawler"},
    "Venator": {"Role": "Assassin"},
    "Victor": {"Role": "Brawler"},
    "Vindicta": {"Role": "Marksman"},
    "Viscous": {"Role": "Brawler"},
    "Vyper": {"Role": "Assassin"},
    "Warden": {"Role": "Brawler"},
    "Wraith": {"Role": "Assassin"},
    "Yamato": {"Role": "Assassin"},
}

HERO_NAMES = sorted(HeroData.keys())

MATCH_FORMATS = ["Bo1", "Bo3", "Bo5"]

PICKBAN_MODES = {
    "Captain Draft": "Captains submit hero picks and bans for each game",
    "Tournament": "Structured tournament draft (3 bans, alternating picks)",
    "Random": "Random hero bans are assigned to each team",
    "None": "Disable pick/ban phase for this scrim",
}
