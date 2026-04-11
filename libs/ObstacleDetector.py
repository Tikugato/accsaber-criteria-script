"""
This file has helper functions related to detecting obstacles
"""
import pandas as pd
import math

def AddNextPrevNoteColumns(df, metadata_version):
    """
    Adds '_nextX', '_nextY', '_prevX', and '_prevY' columns to the DataFrame
    """
    df_modified = df.copy()
    prev_idx = None
    df_modified['_prevX'] = float('nan')
    df_modified['_prevY'] = float('nan')
    df_modified['_nextX'] = float('nan')
    df_modified['_nextY'] = float('nan')
    if (metadata_version == "v2"):
        # v2 metadata
        for idx, row in df_modified.iterrows():
            if (row['_type'] == 0 or row['_type'] == 1):
                if prev_idx is None:
                    prev_idx = idx
                else:
                    df_modified.loc[idx, '_prevX'] = df_modified.loc[prev_idx, '_xCenter']
                    df_modified.loc[idx, '_prevY'] = df_modified.loc[prev_idx, '_yCenter']

                    df_modified.loc[prev_idx, '_nextX'] = df_modified.loc[idx, '_xCenter']
                    df_modified.loc[prev_idx, '_nextY'] = df_modified.loc[idx, '_yCenter']
                    prev_idx = idx
    else:
        # v3 metadata
        for idx, row in df_modified.iterrows():
            if (row['c'] == 0 or row['c'] == 1):
                if prev_idx is None:
                    prev_idx = idx
                else:
                    df_modified.loc[idx, '_prevX'] = df_modified.loc[prev_idx, '_xCenter']
                    df_modified.loc[idx, '_prevY'] = df_modified.loc[prev_idx, '_yCenter']

                    df_modified.loc[prev_idx, '_nextX'] = df_modified.loc[idx, '_xCenter']
                    df_modified.loc[prev_idx, '_nextY'] = df_modified.loc[idx, '_yCenter']
                    prev_idx = idx

    return df_modified


def CombineNotesAndBombs(initial_bpm, bpm_changes, df, df_bombs):
    """
    Combines the entries of df and df_bombs into a single DataFrame
    Sorts these results by ascending beat number and then returns this DataFrame
    """
    df_combined = pd.concat([df, df_bombs]).sort_values('b').reset_index(drop=True)
    df_combined['_seconds'] = 0.0
    for i in range(len(df_combined)):
        b = df_combined.loc[i, 'b']
        if bpm_changes.empty or "_startBeat" not in bpm_changes.columns:
            region_df = bpm_changes  # will be empty, but safe
        else:
            region_df = bpm_changes[bpm_changes["_startBeat"] <= b]

        if len(region_df) == 0:
            # use the first BPM region
            if bpm_changes.empty:
                region = {
                    "_startBeat": 0,
                    "_endBeat": float('inf'),
                    "_BPM": initial_bpm,    # map will use initial BPM
                    "_time": 0,
                    "source": "no_bpm_changes"
                }
            else:
                region = bpm_changes.head(1).iloc[0]
        else:
            # use the most recent region
            region = region_df.tail(1).iloc[0]
        startBeat  = region['_startBeat']
        startTime  = region['_time']       
        bpm        = region['_BPM']
        offset = (b - startBeat) * (60 / bpm)

        df_combined.loc[i, '_seconds'] = startTime + offset

    return df_combined.sort_values('_seconds').reset_index(drop=True)

def point_to_segment_distance(px, py, x1, y1, x2, y2):
    """
    Calculate the distance from a point to a line segment
    """
    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return math.sqrt((px - x1)**2 + (py - y1)**2)

    t = ((px - x1)*dx + (py - y1)*dy) / (dx*dx + dy*dy)
    t = max(0, min(1, t))  # clamp to segment

    proj_x = x1 + t * dx
    proj_y = y1 + t * dy

    return math.sqrt((px - proj_x)**2 + (py - proj_y)**2)

def AffectsSwingPath(prev_note, bomb):
    """
    Checks if a bomb affects the swing path of the prev_note
    Returns 1 if it affects the swing path, 0 otherwise
    """
    prevX = prev_note['_prevX']
    prevY = prev_note['_prevY']
    nextX = prev_note['_nextX']
    nextY = prev_note['_nextY']
    curX = prev_note['_xCenter']
    curY = prev_note['_yCenter']
    bombX = bomb['_xCenter']
    bombY = bomb['_yCenter']
    if not math.isnan(prevX):
        distance = point_to_segment_distance(
            bombX, bombY,
            prevX, prevY,
            curX, curY
        )
        if distance < 0.5:
            return 1
    if not math.isnan(nextX):
        distance = point_to_segment_distance(
                bombX, bombY,
                curX, curY,
                nextX, nextY
            )
        if (distance < .5):
            # This swing affects swing path
            return 1
    return 0


def WithDirPrevSwing(prev_note, bomb):
    """
    Checks if a bomb is with the direction of the previous swing
    Returns 1 if it is with the direction of the previous swing, 0 if against
    """
    nextNoteX = prev_note['_nextX']
    nextNoteY = prev_note['_nextY']
    if math.isnan(nextNoteX) or math.isnan(nextNoteY):
        return 0
    prevNoteX = prev_note['_xCenter']
    prevNoteY = prev_note['_yCenter']
    bombX = bomb['_xCenter']
    bombY = bomb['_yCenter']
    note_diffX = nextNoteX - prevNoteX
    note_diffY = nextNoteY - prevNoteY
    bomb_diffX = bombX - prevNoteX
    bomb_diffY = bombY - prevNoteY
    dot_product = note_diffX * bomb_diffX + note_diffY * bomb_diffY
    mag_note = math.sqrt(note_diffX * note_diffX + note_diffY * note_diffY)
    mag_bomb = math.sqrt(bomb_diffX * bomb_diffX + bomb_diffY * bomb_diffY)
    if (mag_note == 0 or mag_bomb == 0):
        return 0
    else:
        cos_theta = dot_product / (mag_note * mag_bomb)
        cos_theta = max(-1.0, min(1.0, cos_theta))
        angle = math.degrees(math.acos(cos_theta))
    if (angle < 90):
        return 1
    return 0

    

    



def ValidTimeBeforeBombAfterNote(prev_note, bomb, njs, category):
    """
    Checks if a single (prev_note, bomb) triple satisfies requirements for min time before the bomb after the note
    Returns 1 if it is valid, 0 if not
    """
    time_diff_ms = (bomb['_seconds'] - prev_note['_seconds']) * 1000
    if ((AffectsSwingPath(prev_note, bomb) == 0) and (WithDirPrevSwing(prev_note, bomb) == 0) and (category != "true")):
        # the bomb does not affect swing path and is against against the direction of the previous swing and category is not true acc
        if (time_diff_ms < (1500/njs)):
            return 0
        else: 
            return 1
    elif (category == "true"):
        if (time_diff_ms < 500):
            return 0
        else:
            return 1
    elif (category == "standard"):
        if (time_diff_ms < 350):
            return 0
        else:
            return 1
    else:
        if (time_diff_ms < 300):
            return 0
        else:
            return 1


def ValidTimeBeforeNoteAfterBomb(prev_bomb, note):
    """
    Checks if a single (bomb, note) pairs satisfies requirements for min time before the note after the bomb
    Returns 1 if it is valid, 0 if not
    """
    time_diff_ms = (note['_seconds'] - prev_bomb['_seconds']) * 1000
    if (time_diff_ms < 150):
        return 0
    else:
        return 1


def RunAllPreBombChecks(map_object):
    """
    Runs ValidTimeBeforeBombAfterNote for all (prev_note, bomb) pairs in map_object
    Returns an array of times where the bomb criteria failed
    Thus, this portion of the criteria passes if and only if this function returns an empty array
    """
    invalid_times = []
    prev_note = None
    df = map_object.dataframe_struct.df
    metadata_version = map_object.metadata_version
    if (metadata_version == "v2"):
        df_modified = AddNextPrevNoteColumns(df, metadata_version)
        for _, row in df_modified.iterrows():
            if (row['_type'] == 0 or row['_type'] == 1): 
                prev_note = row
            elif (row['_type'] == 3):
                if prev_note is not None:
                    is_valid = ValidTimeBeforeBombAfterNote(prev_note, row, map_object.njs, map_object.category)
                    if is_valid == 0:
                        invalid_times.append(row['_time'])
    else:
        df_combined = CombineNotesAndBombs(map_object.initial_bpm, map_object.bpm_changes, df, map_object.dataframe_struct.df_bombs)
        df_modified = AddNextPrevNoteColumns(df_combined, metadata_version)
        for _, row in df_modified.iterrows():
            if (row['c'] == 0 or row['c'] == 1): 
                prev_note = row
            elif (row['c'] == 3):
                if prev_note is not None:
                    is_valid = ValidTimeBeforeBombAfterNote(prev_note, row, map_object.njs, map_object.category)
                    if is_valid == 0:
                        invalid_times.append(row['b'])
    return invalid_times

def RunAllPostBombChecks(map_object):
    """
    Runs ValidTimeBeforeNoteAfterBomb for all (prev_bomb, note) pairs in map_object
    Returns an array of times where the bomb criteria failed
    Thus, this portion of the criteria passes if and only if this function returns an empty array
    """
    invalid_times = []
    prev_bomb = None
    df = map_object.dataframe_struct.df
    metadata_version = map_object.metadata_version
    if (metadata_version == "v2"):
        for _, row in df.iterrows():
            if (row['_type'] == 3): 
                prev_bomb = row
            elif (row['_type'] == 0 or row['_type'] == 1):
                if prev_bomb is not None:
                    is_valid = ValidTimeBeforeNoteAfterBomb(prev_bomb, row)
                    if is_valid == 0:
                        invalid_times.append(row['_time'])
    else:
        df_combined = CombineNotesAndBombs(map_object.initial_bpm, map_object.bpm_changes, df, map_object.dataframe_struct.df_bombs)
        for _, row in df_combined.iterrows():
            if (row['c'] == 3): 
                prev_bomb = row
            elif (row['c'] == 0 or row['c'] == 1):
                if prev_bomb is not None:
                    is_valid = ValidTimeBeforeNoteAfterBomb(prev_bomb, row)
                    if is_valid == 0:
                        invalid_times.append(row['b'])
    return invalid_times
            
