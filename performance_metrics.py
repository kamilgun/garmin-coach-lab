import json
import os
from datetime import timedelta
from garminconnect import Garmin

TOKENSTORE = r"C:\Users\TCKGUN\.garminconnect"


def seconds_to_hms(seconds):
    if seconds is None:
        return None
    return str(timedelta(seconds=int(seconds)))


def main():
    api = Garmin()
    api.login(TOKENSTORE)

    race = api.get_race_predictions()

    output = {
        "race_predictor": {
            "calendar_date": race.get("calendarDate"),
            "5k": seconds_to_hms(race.get("time5K")),
            "10k": seconds_to_hms(race.get("time10K")),
            "half_marathon": seconds_to_hms(race.get("timeHalfMarathon")),
            "marathon": seconds_to_hms(race.get("timeMarathon")),
        }
    }

    os.makedirs("data", exist_ok=True)

    with open("data/performance_summary.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()