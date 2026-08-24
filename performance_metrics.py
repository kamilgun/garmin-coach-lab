import json
from datetime import timedelta

from garminconnect import Garmin

from coach_engine.workspace import get_runtime_workspace



def seconds_to_hms(seconds):
    if seconds is None:
        return None
    return str(timedelta(seconds=int(seconds)))


def main():
    runtime = get_runtime_workspace()

    api = Garmin()
    api.login(str(runtime.garmin_tokenstore))

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

    runtime.data_dir.mkdir(parents=True, exist_ok=True)

    with runtime.performance_summary_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(
        f"\nJSON yazıldı: {runtime.performance_summary_path}"
    )
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()