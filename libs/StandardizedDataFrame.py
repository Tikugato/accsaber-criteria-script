"""
Builds a standardized DataFrame for feature extraction across v2/v3 maps.
"""
import pandas as pd


def _normalize_bpm_changes(bpm_changes, initial_bpm, last_beat):
    if bpm_changes is None or len(bpm_changes) == 0:
        return pd.DataFrame([
            {
                "_startBeat": 0.0,
                "_endBeat": float("inf"),
                "_BPM": float(initial_bpm),
                "_time": 0.0,
            }
        ])

    df = bpm_changes.copy()

    if "startBeat" in df.columns and "_startBeat" not in df.columns:
        df["_startBeat"] = df["startBeat"]
    if "endBeat" in df.columns and "_endBeat" not in df.columns:
        df["_endBeat"] = df["endBeat"]
    if "b" in df.columns and "_startBeat" not in df.columns:
        df["_startBeat"] = df["b"]
    if "BPM" in df.columns and "_BPM" not in df.columns:
        df["_BPM"] = df["BPM"]
    if "m" in df.columns and "_BPM" not in df.columns:
        df["_BPM"] = df["m"]

    if "_startBeat" not in df.columns:
        df["_startBeat"] = 0.0
    df = df.sort_values("_startBeat").reset_index(drop=True)

    if "_endBeat" not in df.columns:
        df["_endBeat"] = df["_startBeat"].shift(-1)
        fallback_end = last_beat if last_beat is not None else df["_startBeat"].max()
        df.loc[df["_endBeat"].isna(), "_endBeat"] = fallback_end

    if "_time" not in df.columns:
        if "_change_in_time" in df.columns:
            df["_time"] = df["_change_in_time"].cumsum()
        else:
            df["_change_in_time"] = (df["_endBeat"] - df["_startBeat"]) * (60 / df["_BPM"])
            df["_time"] = df["_change_in_time"].cumsum()

    return df


def BuildStandardizedDataFrame(map_object):
    """
    Returns a standardized DataFrame across v2/v3 maps with consistent columns.
    """
    metadata_version = map_object.metadata_version
    df_notes = map_object.dataframe_struct.df
    df_bombs = map_object.dataframe_struct.df_bombs

    last_beat = None
    beats = []
    if df_notes is not None and not df_notes.empty:
        beats.append(df_notes["_time"] if metadata_version == "v2" else df_notes["b"])
    if df_bombs is not None and not df_bombs.empty and "b" in df_bombs.columns:
        beats.append(df_bombs["b"])
    if beats:
        last_beat = float(pd.concat(beats).max())

    bpm_changes = _normalize_bpm_changes(map_object.bpm_changes, map_object.initial_bpm, last_beat)

    def seconds_for_beat(beat_value):
        for _, row in bpm_changes.iterrows():
            start_beat = row["_startBeat"]
            end_beat = row["_endBeat"]
            start_time = row["_time"] - ((row["_endBeat"] - row["_startBeat"]) * (60 / row["_BPM"]))
            if beat_value < end_beat:
                return start_time + (beat_value - start_beat) * (60 / row["_BPM"])
        last = bpm_changes.iloc[-1]
        return last["_time"] + (beat_value - last["_endBeat"]) * (60 / last["_BPM"])

    def bpm_for_beat(beat_value):
        for _, row in bpm_changes.iterrows():
            if beat_value < row["_endBeat"]:
                return float(row["_BPM"])
        return float(bpm_changes.iloc[-1]["_BPM"])

    def xy_center(x, y):
        return (-0.9 + x * 0.6, 1 + y * 0.55)

    rows = []

    if metadata_version == "v2":
        for _, row in df_notes.iterrows():
            beat = float(row["_time"])
            event_type = "bomb" if row["_type"] == 3 else "note"
            hand = "left" if row["_type"] == 0 else "right" if row["_type"] == 1 else None
            rows.append({
                "metadata_version": "v2",
                "event_type": event_type,
                "is_note": event_type == "note",
                "is_bomb": event_type == "bomb",
                "hand": hand,
                "color": int(row["_type"]) if not pd.isna(row["_type"]) else None,
                "cut_direction": int(row["_cutDirection"]) if "_cutDirection" in row else None,
                "angle_offset": None,
                "beat": beat,
                "seconds": float(row["_seconds"]) if "_seconds" in row else seconds_for_beat(beat),
                "bpm": float(row["_bpm"]) if "_bpm" in row else bpm_for_beat(beat),
                "x": int(row["_lineIndex"]) if "_lineIndex" in row else None,
                "y": int(row["_lineLayer"]) if "_lineLayer" in row else None,
                "x_center": float(row["_xCenter"]) if "_xCenter" in row else None,
                "y_center": float(row["_yCenter"]) if "_yCenter" in row else None,
            })
    else:
        for _, row in df_notes.iterrows():
            beat = float(row["b"])
            x = int(row["x"]) if "x" in row else None
            y = int(row["y"]) if "y" in row else None
            x_center, y_center = xy_center(x, y) if x is not None and y is not None else (None, None)
            rows.append({
                "metadata_version": "v3",
                "event_type": "note",
                "is_note": True,
                "is_bomb": False,
                "hand": "left" if row["c"] == 0 else "right" if row["c"] == 1 else None,
                "color": int(row["c"]) if "c" in row else None,
                "cut_direction": int(row["d"]) if "d" in row else None,
                "angle_offset": float(row["a"]) if "a" in row else None,
                "beat": beat,
                "seconds": float(row["_seconds"]) if "_seconds" in row else seconds_for_beat(beat),
                "bpm": float(row["_bpm"]) if "_bpm" in row else bpm_for_beat(beat),
                "x": x,
                "y": y,
                "x_center": float(row["_xCenter"]) if "_xCenter" in row else x_center,
                "y_center": float(row["_yCenter"]) if "_yCenter" in row else y_center,
            })

        if df_bombs is not None and not df_bombs.empty:
            for _, row in df_bombs.iterrows():
                beat = float(row["b"])
                x = int(row["x"]) if "x" in row else None
                y = int(row["y"]) if "y" in row else None
                x_center, y_center = xy_center(x, y) if x is not None and y is not None else (None, None)
                rows.append({
                    "metadata_version": "v3",
                    "event_type": "bomb",
                    "is_note": False,
                    "is_bomb": True,
                    "hand": None,
                    "color": 3,
                    "cut_direction": 8,
                    "angle_offset": 0.0,
                    "beat": beat,
                    "seconds": float(row["_seconds"]) if "_seconds" in row else seconds_for_beat(beat),
                    "bpm": float(row["_bpm"]) if "_bpm" in row else bpm_for_beat(beat),
                    "x": x,
                    "y": y,
                    "x_center": float(row["_xCenter"]) if "_xCenter" in row else x_center,
                    "y_center": float(row["_yCenter"]) if "_yCenter" in row else y_center,
                })

    df_standard = pd.DataFrame(rows)
    if df_standard.empty:
        return df_standard

    df_standard = df_standard.sort_values(["seconds", "beat", "event_type"]).reset_index(drop=True)
    df_standard["beat_delta"] = df_standard["beat"].diff().fillna(0)
    df_standard["seconds_delta"] = df_standard["seconds"].diff().fillna(0)

    return df_standard
