"""
This file creates a Map class to store information about a map
"""
from libs.utils import normalize_string
from libs.ParseObjects import BuildObjectsDataFramev2, BuildObjectsDataFramev3
import json
import os
import pandas as pd
from libs.MapStatistics import MapStatistics

def DetectMetadataVersion(diff_data):
    """
    Detects the metadata version the beatmap uses
    """
    notes = diff_data.get('_notes')
    if notes is not None:
        return "v2"
    else:
        notes = diff_data.get('colorNotes')
        if notes is not None:
            return "v3"
    return "Error: not a v2 or v3 map"

def GetBpmChanges(mapset_path, diff_info):
    """
    Returns a DataFrame of BPM Changes or an empty DataFrame if there are no BPM changes
    """
    bpmPath = os.path.join(mapset_path, "BPMInfo.dat")

    rename_map = {
        "startBeat": "_startBeat",
        "endBeat": "_endBeat",
        "_startBeat": "_startBeat",
        "_endBeat": "_endBeat"
    }
    if os.path.exists(bpmPath):
        with open(bpmPath, encoding="utf-8") as f:
            bpmData = json.load(f)

        song_frequency = bpmData.get("_songFrequency", 44100)
        df = pd.DataFrame(bpmData.get("_regions", []))

        df = df.rename(columns=rename_map, errors="ignore")

        if not df.empty and "_endSampleIndex" in df and "_startSampleIndex" in df:
            df["_change_in_time"] = (df["_endSampleIndex"] - df["_startSampleIndex"]) / song_frequency
            df["_BPM"] = (df["_endBeat"] - df["_startBeat"]) * (60 / df["_change_in_time"])
            df["_time"] = df["_change_in_time"].cumsum()

        df["source"] = "BPMInfo"
        return df

    customData = diff_info.get("_customData", {})

    if "_BPMChanges" in customData:
        df = pd.DataFrame(customData["_BPMChanges"])
        df = df.rename(columns=rename_map, errors="ignore")

        if not df.empty:
            if "BPM" in df:
                df["_BPM"] = df["BPM"]

            if "_startBeat" in df and "_endBeat" in df and "_BPM" in df:
                df["_change_in_time"] = (df["_endBeat"] - df["_startBeat"]) * (60 / df["_BPM"])
                df["_time"] = df["_change_in_time"].cumsum()

        df["source"] = "V2_custom"
        return df

    if "bpmEvents" in diff_info:
        df = pd.DataFrame(diff_info["bpmEvents"])
        df = df.rename(columns=rename_map, errors="ignore")

        if not df.empty:
            if "BPM" in df:
                df["_BPM"] = df["BPM"]

            if "_startBeat" in df and "_endBeat" in df and "_BPM" in df:
                df["_change_in_time"] = (df["_endBeat"] - df["_startBeat"]) * (60 / df["_BPM"])
                df["_time"] = df["_change_in_time"].cumsum()

        df["source"] = "V3_official"
        return df

    fallback_bpm = (
        diff_info.get("_beatsPerMinute")
        or diff_info.get("beatsPerMinute")
    )
    if fallback_bpm is None:
        info_path = os.path.join(mapset_path, "Info.dat")
        if not os.path.exists(info_path):
            info_path = os.path.join(mapset_path, "info.dat")
        if os.path.exists(info_path):
            with open(info_path, encoding="utf-8") as f:
                info_data = json.load(f)
            fallback_bpm = info_data.get("_beatsPerMinute")

    if fallback_bpm is None:
        return pd.DataFrame([])

    return pd.DataFrame([{
        "_startBeat": 0.0,
        "_endBeat": 99999.0,
        "_BPM": fallback_bpm,
        "_change_in_time": 0.0,
        "_time": 0.0,
        "source": "fallback"
    }])

       
def get_diff_info_dict(info_data, diff):
    """
    Returns a dictionary of the information contained in the info.dat file that is relevant for this difficulty
    """
    # we first want to iterate through dicts
    for beatmap_set in info_data["_difficultyBeatmapSets"]:
        if (beatmap_set["_beatmapCharacteristicName"] != "Standard"):
            continue
        else:
            for difficulty in beatmap_set["_difficultyBeatmaps"]:
                if (difficulty["_difficultyRank"] == diff):
                    return difficulty
    print("Error finding difficulty metadata in the info.dat file for this difficulty")
    return

def diff_str_to_int(diff_str):
    """
    This takes in a string representing the map's difficulty and outputs the corresponding integer
    easy -> 1, normal -> 3, hard -> 5, expert -> 7, expertplus -> 9
    returns -1 on error (invalid input string)
    """
    normalized_str = normalize_string(diff_str)
    if (normalized_str == "easy"):
        return 1
    elif (normalized_str == "normal"):
        return 3
    elif (normalized_str == "hard"):
        return 5
    elif (normalized_str == "expert"):
        return 7
    elif (normalized_str == "expertplus"):
        return 9
    return -1

class Map:
    """
    Map class declaration
    Fields:
        - mapset_path (string): file path of the mapset directory
        - diff (int): integer encoding difficulty label
        - info_data (dict): dictionary storing the contents from the info .dat file
        - diff_info (dict): dictionary storing the contents from the info .dat file for the respective diff
        - diff_data (dict): dictionary storing the contents from the respective diff's .dat file
        - category (string): the category of accuracy map
        - njs (int): njs of the map
        - initial_bpm (double) : initial bpm of the map
        - bpm_changes (DataFrame): DataFrame of bpm changes in the map
        - metadata_version (string): "v2" if the map stores v2 data, "v3" if the map stores v3 data
        - logs_list (string[]): this stores a list of failed criteria
        - dataframe_struct (MapDataFrames class): Class that contains a lot of different DataFrames related to the map
        - statistics (MapStatistics class): Class that contains statistics related to this map
    """
    def __init__(self, mapset_path, diff_str, category):
        """
        Constructor
        """
        self.mapset_path = mapset_path
        self.diff = diff_str_to_int(diff_str)
        if (self.diff == -1):
            raise ValueError("Please provide a valid difficulty label")
        info_path = os.path.join(mapset_path, "Info.dat")
        if not os.path.exists(info_path):
            info_path = os.path.join(mapset_path, "info.dat")
        with open(info_path, "r", encoding="utf-8") as f:
            self.info_data = json.load(f)
        self.diff_info = get_diff_info_dict(self.info_data, self.diff)
        if self.diff_info is None:
            raise ValueError("Difficulty metadata not found")
        diff_filename = self.diff_info["_beatmapFilename"]
        diff_path = os.path.join(mapset_path, diff_filename)
        with open(diff_path, "r", encoding="utf-8") as f:
            self.diff_data = json.load(f)
        self.category = normalize_string(category)
        
        self.njs = self.diff_info["_noteJumpMovementSpeed"]
        self.initial_bpm = self.info_data.get('_beatsPerMinute')
        self.bpm_changes = GetBpmChanges(mapset_path, self.diff_data)
        self.metadata_version = DetectMetadataVersion(self.diff_data)
        self.logs_list = []
        self.dataframe_struct = None
        if (self.metadata_version != "v2" and self.metadata_version != "v3"):
            return
        if (self.metadata_version == "v2"):
            BuildObjectsDataFramev2(self, self.bpm_changes, self.diff_data, self.initial_bpm)
        else:
            BuildObjectsDataFramev3(self, self.mapset_path, self.bpm_changes, self.diff_data, self.initial_bpm)
        self.statistics = MapStatistics(self)
