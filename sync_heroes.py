"""Fetch hero list from Liquipedia API placeholder / manual sync stub."""
import json
from pathlib import Path

HERODATA_PATH = Path(__file__).parent / "BotData" / "herodata.py"

# Run manually after new heroes release; extend HeroData dict in herodata.py.
if __name__ == "__main__":
    print("Hero sync: update BotData/herodata.py manually or extend this script with a data source.")
    print(f"Current file: {HERODATA_PATH}")
