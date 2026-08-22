from contextlib import redirect_stdout
import io
import json
from pathlib import Path

from libs.CriteriaChecker import RunCriteriaChecks
from libs.Map import Map


CATEGORY_OPTIONS = ("Standard", "Tech", "True")


def list_standard_difficulties(mapset_path):
    mapset_path = Path(mapset_path)
    info_path = mapset_path / "Info.dat"
    if not info_path.exists():
        info_path = mapset_path / "info.dat"
    if not info_path.exists():
        raise FileNotFoundError(f"Could not find Info.dat in {mapset_path}")

    with open(info_path, "r", encoding="utf-8") as handle:
        info_data = json.load(handle)

    difficulties = []
    for beatmap_set in info_data.get("_difficultyBeatmapSets", []):
        if beatmap_set.get("_beatmapCharacteristicName") != "Standard":
            continue
        for difficulty in beatmap_set.get("_difficultyBeatmaps", []):
            name = difficulty.get("_difficulty")
            if name and name not in difficulties:
                difficulties.append(name)
    return difficulties


def run_check(mapset_path, diff_str, category):
    map_object = Map(mapset_path, diff_str, category)
    stdout_buffer = io.StringIO()
    with redirect_stdout(stdout_buffer):
        results = RunCriteriaChecks(map_object)
    passed = len(map_object.logs_list) == 0
    category_name = str(map_object.category)
    if passed:
        summary = (
            f"This map passed the criteria for the {category_name} acc category. "
            "Make sure the map still passes QAT tests."
        )
    else:
        summary = f"This map failed the criteria for the {category_name} acc category."

    return {
        "results": results,
        "passed": passed,
        "summary": summary,
        "logs": map_object.logs_list,
        "stdout": stdout_buffer.getvalue(),
        "standard_df": map_object.standard_df,
        "map_object": map_object,
    }
