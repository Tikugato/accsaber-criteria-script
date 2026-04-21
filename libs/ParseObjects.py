"""
This file deals with creating a DataFrame of the objects in a map
"""
import pandas as pd
from libs.utils import get_pythagoras
import math
import os
import json
from libs.MapDataFrames import MapDataFrames
EPSILON = 0.059 # Epsilon threshold in ms for detecting when blocks count towards the same swing

def sanitize_notes_df(df, beat_col):
    """
    Sort notes by beat, compute _timeChange, fix negatives, recompute seconds.
    This prevents false slider detection and ensures consistent timing.
    """
    if df.empty or beat_col not in df.columns:
        return df
    # Sort by beat
    df = df.sort_values(beat_col).reset_index(drop=True)

    # Compute time delta
    df["_timeChange"] = df[beat_col].diff().fillna(0)

    # Remove negative deltas (caused by editor export ordering / duplicates)
    df.loc[df["_timeChange"] < 0, "_timeChange"] = 0

    return df

def BuildNewSwingsv2(map_object, left, right, df):
    """
    Sets the df_left, df_right, df_new_left_swing, df_new_right_swing, df_left_sliders, df_right_sliders, df_new_swing, and df_ignore_doubles fields of map_object.dataframe_struct
    """
    firstLeftSwingIndex = left.head(1).index[0]
    firstRightSwingIndex = right.head(1).index[0]

    df_newLeftSwing = left[((((60 * left['_timeChange']) / left['_bpm']) > EPSILON) | (left.index == firstLeftSwingIndex))].copy()
    df_newRightSwing = right[((((60 * right['_timeChange']) / right['_bpm']) > EPSILON) | (right.index == firstRightSwingIndex))].copy()
    df_leftSliders = left[(((60 * left['_timeChange']) / left['_bpm']) < EPSILON) & (left['_timeChange'] != 0)].copy()
    df_rightSliders = right[(((60 * right['_timeChange']) / right['_bpm']) < EPSILON) & (right['_timeChange'] != 0)].copy()

    #Create and update columns
    df_newLeftSwing['_xMovement'] = df_newLeftSwing.loc[:, ['_xCenter']].diff().fillna(0)
    df_newLeftSwing['_yMovement'] = df_newLeftSwing.loc[:, ['_yCenter']].diff().fillna(0)
    df_newLeftSwing['_totMovement'] = df_newLeftSwing.apply(lambda x: get_pythagoras(x['_xMovement'], x['_yMovement']), axis=1).fillna(0) 
    df_newLeftSwing['_angleMagnitudeChange'] = abs(df_newLeftSwing.apply(lambda x: math.atan2(x['_yMovement'],x['_xMovement']), axis=1))
    df_newLeftSwing['_timeChange'] = df_newLeftSwing.loc[:, ['_time']].diff().fillna(0)
    df_newLeftSwing['_timeChangeSeconds'] = (60 * df_newLeftSwing['_timeChange']) / df_newLeftSwing['_bpm']

    df_newRightSwing['_xMovement'] = df_newRightSwing.loc[:, ['_xCenter']].diff().fillna(0)
    df_newRightSwing['_yMovement'] = df_newRightSwing.loc[:, ['_yCenter']].diff().fillna(0)
    df_newRightSwing['_totMovement'] = df_newRightSwing.apply(lambda x: get_pythagoras(x['_xMovement'], x['_yMovement']), axis=1).fillna(0)
    df_newRightSwing['_angleMagnitudeChange'] = abs(df_newRightSwing.apply(lambda x: math.atan2(x['_yMovement'],x['_xMovement']), axis=1))
    df_newRightSwing['_timeChange'] = df_newRightSwing.loc[:, ['_time']].diff().fillna(0)
    df_newRightSwing['_timeChangeSeconds'] = (60 * df_newRightSwing['_timeChange']) / df_newRightSwing['_bpm']

    df_newSwing = pd.concat([df_newLeftSwing, df_newRightSwing])

    df_newSwing = df_newSwing.sort_values('_time')
    df_newSwing['_timeChange'] = df_newSwing.loc[:, ['_time']].diff().fillna(0)
    df_newSwing['_timeChangeSeconds'] = (60 * df_newSwing['_timeChange']) / df_newSwing['_bpm']


    df_newLeftSwing['_seconds'] = df_newLeftSwing['_timeChangeSeconds'].cumsum()
    df_newRightSwing['_seconds'] = df_newRightSwing['_timeChangeSeconds'].cumsum()
    df_newSwing['_seconds'] = df_newSwing['_timeChangeSeconds'].cumsum()
    df_ignoreDoubles = df_newSwing.groupby('_seconds', as_index=False).agg('first')

    # Set the dataframe_struct field of map_object
    df_bombs = pd.DataFrame([])
    dfs = MapDataFrames(df, df_bombs, left, right, df_newLeftSwing, df_newRightSwing, df_leftSliders, df_rightSliders, df_newSwing, df_ignoreDoubles)
    map_object.dataframe_struct = dfs

def BuildObjectsDataFramev2(map_object, bpm_changes, diff_data, initial_bpm):
    """
    Builds the DataFrame of all objects for maps using v2 metadata
    """
    if bpm_changes is None or len(bpm_changes) == 0:
        df = pd.DataFrame(diff_data['_notes'])
        df['_yCenter'] = df['_lineLayer'].apply(lambda x: 1 + x * 0.55)
        df['_xCenter'] = df['_lineIndex'].apply(lambda x: -0.9 + x * 0.6)
        df = sanitize_notes_df(df, "_time")
        df['_bpm'] = initial_bpm
        df['_timeChange'] = df['_time'].diff().fillna(0)
        df['_timeChangeSeconds'] = (60 * df['_timeChange']) / df['_bpm']
        df['_seconds'] = df['_timeChangeSeconds'].cumsum()
        left = sanitize_notes_df(df[df['_type'] == 0].copy(), "_time")
        right = sanitize_notes_df(df[df['_type'] == 1].copy(), "_time")
        BuildNewSwingsv2(map_object, left, right, df)
        return
    
    if "BPM" in bpm_changes.columns and "_BPM" not in bpm_changes.columns:
        bpm_changes["_BPM"] = bpm_changes["BPM"]
    if "startBeat" in bpm_changes.columns and "endBeat" in bpm_changes.columns:
        bpm_changes["_change_in_time"] = (bpm_changes["endBeat"] - bpm_changes["startBeat"]) * (60 / bpm_changes["_BPM"])
    bpm_changes["_time"] = bpm_changes["_change_in_time"].cumsum()

    df = pd.DataFrame(diff_data['_notes'])
    df['_yCenter'] = df['_lineLayer'].apply(lambda x: 1 + x * 0.55)
    df['_xCenter'] = df['_lineIndex'].apply(lambda x: -0.9 + x * 0.6)
    df['_bpm'] = float(initial_bpm)

    for i in range(len(df)):
        currentTime = df.loc[i, '_time']
        for j in range(len(bpm_changes)):
            note_seconds = (currentTime * 60) / df.loc[i, '_bpm']
            if note_seconds < bpm_changes.loc[j, '_time']:
                break
            df.loc[i, '_bpm'] = bpm_changes.loc[j, '_BPM']

    left = sanitize_notes_df(df[df['_type'] == 0].copy(), "_time")
    right = sanitize_notes_df(df[df['_type'] == 1].copy(), "_time")

    left['_timeChangeSeconds'] = (60 * left['_timeChange']) / left['_bpm']
    right['_timeChangeSeconds'] = (60 * right['_timeChange']) / right['_bpm']

    df['_timeChange'] = df['_time'].diff().fillna(0)
    df['_timeChangeSeconds'] = (60 * df['_timeChange']) / df['_bpm']
    df['_seconds'] = df['_timeChangeSeconds'].cumsum()

    BuildNewSwingsv2(map_object, left, right, df)


def BuildNewSwingsv3(map_object, left, right, df, df_bombs):
    firstLeftSwingIndex = left.head(1).index[0]
    firstRightSwingIndex = right.head(1).index[0]

    df_newLeftSwing = left[((((60 * left['_timeChange']) / left['_bpm']) > EPSILON) | (left.index == firstLeftSwingIndex))].copy()
    df_newRightSwing = right[((((60 * right['_timeChange']) / right['_bpm']) > EPSILON) | (right.index == firstRightSwingIndex))].copy()
    df_leftSliders = left[(((60 * left['_timeChange']) / left['_bpm']) < EPSILON) & (left['_timeChange'] != 0)].copy()
    df_rightSliders = right[(((60 * right['_timeChange']) / right['_bpm']) < EPSILON) & (right['_timeChange'] != 0)].copy()

    #Create and update columns
    df_newLeftSwing['_xMovement'] = df_newLeftSwing.loc[:, ['_xCenter']].diff().fillna(0)
    df_newLeftSwing['_yMovement'] = df_newLeftSwing.loc[:, ['_yCenter']].diff().fillna(0)
    df_newLeftSwing['_totMovement'] = df_newLeftSwing.apply(lambda x: get_pythagoras(x['_xMovement'], x['_yMovement']), axis=1).fillna(0) 
    df_newLeftSwing['_angleMagnitudeChange'] = abs(df_newLeftSwing.apply(lambda x: math.atan2(x['_yMovement'],x['_xMovement']), axis=1))
    df_newLeftSwing['_timeChange'] = df_newLeftSwing.loc[:, ['b']].diff().fillna(0)
    df_newLeftSwing['_timeChangeSeconds'] = (60 * df_newLeftSwing['_timeChange']) / df_newLeftSwing['_bpm']

    df_newRightSwing['_xMovement'] = df_newRightSwing.loc[:, ['_xCenter']].diff().fillna(0)
    df_newRightSwing['_yMovement'] = df_newRightSwing.loc[:, ['_yCenter']].diff().fillna(0)
    df_newRightSwing['_totMovement'] = df_newRightSwing.apply(lambda x: get_pythagoras(x['_xMovement'], x['_yMovement']), axis=1).fillna(0)
    df_newRightSwing['_angleMagnitudeChange'] = abs(df_newRightSwing.apply(lambda x: math.atan2(x['_yMovement'],x['_xMovement']), axis=1))
    df_newRightSwing['_timeChange'] = df_newRightSwing.loc[:, ['b']].diff().fillna(0)
    df_newRightSwing['_timeChangeSeconds'] = (60 * df_newRightSwing['_timeChange']) / df_newRightSwing['_bpm']

    df_newSwing = pd.concat([df_newLeftSwing, df_newRightSwing])
    df_newSwing = df_newSwing.sort_values('b')
    df_newSwing['_timeChange'] = df_newSwing.loc[:, ['b']].diff().fillna(0)
    df_newSwing['_timeChangeSeconds'] = (60 * df_newSwing['_timeChange']) / df_newSwing['_bpm']


    df_newLeftSwing['_seconds'] = df_newLeftSwing['_timeChangeSeconds'].cumsum()
    df_newRightSwing['_seconds'] = df_newRightSwing['_timeChangeSeconds'].cumsum()
    df_newSwing['_seconds'] = df_newSwing['_timeChangeSeconds'].cumsum()
    df_ignoreDoubles = df_newSwing.groupby('_seconds', as_index=False).agg('first')
    # Set the dataframe_struct field of map_object
    dfs = MapDataFrames(df, df_bombs, left, right, df_newLeftSwing, df_newRightSwing, df_leftSliders, df_rightSliders, df_newSwing, df_ignoreDoubles)
    map_object.dataframe_struct = dfs

def BuildObjectsDataFramev3(map_object, mapset_path, bpm_changes, diff_data, initial_bpm):
    """
    Builds the DataFrame of all objects for maps using v3 metadata
    """
    if bpm_changes is None or len(bpm_changes) == 0:
        df = pd.DataFrame(diff_data['colorNotes'])
        # safeguard for v3 notes
        for col in ("b", "x", "y", "c", "d", "a"):
            if col not in df.columns:
                df[col] = 0
            else:
                df[col] = df[col].fillna(0)
        df['_yCenter'] = df['y'].apply(lambda x: 1 + x * 0.55)
        df['_xCenter'] = df['x'].apply(lambda x: -0.9 + x * 0.6)
        df = sanitize_notes_df(df, "b")
        df['_bpm'] = initial_bpm
        df['_timeChange'] = df['b'].diff().fillna(0)
        df['_timeChangeSeconds'] = (60 * df['_timeChange']) / df['_bpm']
        df['_seconds'] = df['_timeChangeSeconds'].cumsum()
        df_bombs = pd.DataFrame(diff_data.get('bombNotes', []))
        if not df_bombs.empty:
            for col in ("b", "x", "y"):
                if col not in df_bombs.columns:
                    df_bombs[col] = 0
                else:
                    df_bombs[col] = df_bombs[col].fillna(0)
        df_bombs = sanitize_notes_df(df_bombs, "b")
        left = sanitize_notes_df(df[df['c'] == 0].copy(), "b")
        right = sanitize_notes_df(df[df['c'] == 1].copy(), "b")
        BuildNewSwingsv3(map_object, left, right, df, df_bombs)
        return

    if "BPM" in bpm_changes.columns:
        bpm_changes["_BPM"] = bpm_changes["BPM"]

    last_note_beat = 0
    if "colorNotes" in diff_data and len(diff_data["colorNotes"]) > 0:
        last_note_beat = pd.DataFrame(diff_data["colorNotes"])["b"].max()

    bpmPath = os.path.join(mapset_path, "BPMInfo.dat")
    if os.path.exists(bpmPath):
        with open(bpmPath, encoding="utf-8") as bpm_json_data:
            bpmData = json.load(bpm_json_data)
        song_frequency = bpmData.get('_songFrequency', 44100)

    # Normalize column names so we can handle different BPM change sources uniformly
    if "startBeat" in bpm_changes.columns and "_startBeat" not in bpm_changes.columns:
        bpm_changes["_startBeat"] = bpm_changes["startBeat"]
    if "endBeat" in bpm_changes.columns and "_endBeat" not in bpm_changes.columns:
        bpm_changes["_endBeat"] = bpm_changes["endBeat"]
    if "b" in bpm_changes.columns and "_startBeat" not in bpm_changes.columns:
        bpm_changes["_startBeat"] = bpm_changes["b"]
    if "m" in bpm_changes.columns and "_BPM" not in bpm_changes.columns:
        bpm_changes["_BPM"] = bpm_changes["m"]

    start_col = "_startBeat" if "_startBeat" in bpm_changes.columns else "startBeat"
    end_col = "_endBeat" if "_endBeat" in bpm_changes.columns else "endBeat"

    # Derive end beats if missing (e.g., single-point BPM changes)
    if end_col not in bpm_changes.columns:
        bpm_changes[end_col] = bpm_changes[start_col].shift(-1)
        bpm_changes.loc[bpm_changes[end_col].isna(), end_col] = last_note_beat

    source = bpm_changes["source"].iloc[0]
    MIN_SEGMENT_SECONDS = 0.01
    if source == "BPMInfo":
        bpm_changes['_change_in_time'] = (bpm_changes['_endSampleIndex'] - bpm_changes['_startSampleIndex']) / song_frequency
        bpm_changes['_BPM'] = (bpm_changes['_endBeat'] - bpm_changes['_startBeat']) * (60 / bpm_changes['_change_in_time'])
    else:
        bpm_changes['_change_in_time'] = (bpm_changes[end_col] - bpm_changes[start_col]) * (60 / bpm_changes['_BPM'])

    # Clamp absurd BPM spikes (e.g., m=100000 used as placeholders) to previous/initial BPM
    for idx in range(len(bpm_changes)):
        if bpm_changes.loc[idx, '_BPM'] > 1000:
            fallback_bpm = initial_bpm if idx == 0 else bpm_changes.loc[idx - 1, '_BPM']
            bpm_changes.loc[idx, '_BPM'] = fallback_bpm
            bpm_changes.loc[idx, '_change_in_time'] = (bpm_changes.loc[idx, end_col] - bpm_changes.loc[idx, start_col]) * (60 / bpm_changes.loc[idx, '_BPM'])

    # Clamp tiny segments to previous BPM to avoid absurd values from sub-10ms regions
    for idx in range(1, len(bpm_changes)):
        if bpm_changes.loc[idx, '_change_in_time'] < MIN_SEGMENT_SECONDS:
            bpm_changes.loc[idx, '_BPM'] = bpm_changes.loc[idx - 1, '_BPM']

    bpm_changes['_time'] = bpm_changes['_change_in_time'].cumsum()

    df = pd.DataFrame(diff_data['colorNotes'])
    # safeguard for v3 notes
    for col in ("b", "x", "y", "c", "d", "a"):
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = df[col].fillna(0)
    df['_yCenter'] = df['y'].apply(lambda x: 1 + x * 0.55)
    df['_xCenter'] = df['x'].apply(lambda x: -0.9 + x * 0.6)
    df['_bpm'] = float(initial_bpm)
    df['_bpm'] = df['_bpm'].astype(float)

    bpm_changes = bpm_changes.sort_values(start_col).reset_index(drop=True)

    def beat_to_seconds(beat_value):
        """
        Convert a beat value to seconds using BPM change regions.
        Falls back to initial BPM if regions are missing.
        """
        if start_col not in bpm_changes.columns or end_col not in bpm_changes.columns:
            return (beat_value * 60) / initial_bpm

        for idx, row in bpm_changes.iterrows():
            start_beat = row[start_col]
            end_beat = row[end_col]
            start_time = row["_time"] - row["_change_in_time"]

            if beat_value < end_beat:
                return start_time + (beat_value - start_beat) * (60 / row["_BPM"])

        # After last region, extrapolate with last BPM
        last = bpm_changes.iloc[-1]
        return last["_time"] + (beat_value - last[end_col]) * (60 / last["_BPM"])

    def bpm_for_seconds(note_seconds):
        for j in range(len(bpm_changes)):
            if note_seconds < bpm_changes.loc[j, '_time']:
                return bpm_changes.loc[j, '_BPM']
        return bpm_changes.loc[len(bpm_changes) - 1, '_BPM']

    for i in range(len(df)):
        note_seconds = beat_to_seconds(df.loc[i, 'b'])
        df.loc[i, '_bpm'] = bpm_for_seconds(note_seconds)

    left = sanitize_notes_df(df[df['c'] == 0].copy(), "b")
    right = sanitize_notes_df(df[df['c'] == 1].copy(), "b")

    left['_timeChangeSeconds'] = (60 * left['_timeChange']) / left['_bpm']
    right['_timeChangeSeconds'] = (60 * right['_timeChange']) / right['_bpm']

    df_BPMChanges = bpm_changes
    initialBPM = initial_bpm
    diffData = diff_data
    df_bombs = pd.DataFrame(diffData.get('bombNotes', []))
    # safeguard for v3 bombs
    if not df_bombs.empty:
        for col in ("b", "x", "y"):
            if col not in df_bombs.columns:
                df_bombs[col] = 0
            else:
                df_bombs[col] = df_bombs[col].fillna(0)

    if len(df_bombs) > 0:
        df_bombs['c'] = 3
        df_bombs['d'] = 8
        df_bombs['a'] = 0
        df_bombs['_yCenter'] = df_bombs['y'].apply(lambda x: 1 + x * 0.55)
        df_bombs['_xCenter'] = df_bombs['x'].apply(lambda x: -0.9 + x * 0.6)
        df_bombs['_bpm'] = float(initialBPM)
        df_bombs['_bpm'] = df_bombs['_bpm'].astype(float)
        def bpm_for_bomb_seconds(note_seconds):
            for j in range(len(df_BPMChanges)):
                if note_seconds < df_BPMChanges.loc[j, '_time']:
                    return df_BPMChanges.loc[j, '_BPM']
            return df_BPMChanges.loc[len(df_BPMChanges) - 1, '_BPM']

        for i in range(len(df_bombs)):
            note_seconds = beat_to_seconds(df_bombs.loc[i, 'b'])
            df_bombs.loc[i, '_bpm'] = bpm_for_bomb_seconds(note_seconds)
        df_bombs['_timeChange'] = df_bombs['b'].diff().fillna(0)
        df_bombs['_timeChangeSeconds'] = (60 * df_bombs['_timeChange']) / df_bombs['_bpm']
        df_bombs['_seconds'] = df_bombs['_timeChangeSeconds'].cumsum()

    df['_timeChange'] = df['b'].diff().fillna(0)
    df['_timeChangeSeconds'] = (60 * df['_timeChange']) / df['_bpm']
    df['_seconds'] = df['_timeChangeSeconds'].cumsum()

    BuildNewSwingsv3(map_object, left, right, df, df_bombs)
