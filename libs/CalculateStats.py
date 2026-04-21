"""
This file contains helper functions to calculate map statistics that will be called in the MapStatistics class
"""
import math
EPSILON = 0.059 # Epsilon threshold in ms for detecting when blocks count towards the same swing

def GetLeftSwings(map_object):
    return len(map_object.dataframe_struct.df_new_left_swing)

def GetRightSwings(map_object):
    return len(map_object.dataframe_struct.df_new_right_swing)

def GetTotalSwings(map_object):
    return len(map_object.dataframe_struct.df_new_swing)

def GetLeftTime(map_object):
    return round(map_object.dataframe_struct.df_new_left_swing['_timeChangeSeconds'].sum(), 2)

def GetRightTime(map_object):
    return round(map_object.dataframe_struct.df_new_right_swing['_timeChangeSeconds'].sum(), 2)

def GetLeftAvgSps(map_object):
    return round(GetLeftSwings(map_object) / GetLeftTime(map_object), 2)

def GetRightAvgSps(map_object):
    return round(GetRightSwings(map_object) / GetRightTime(map_object), 2)

def GetLeftAvgAngleChange(map_object):
    return round(map_object.dataframe_struct.df_new_left_swing['_angleMagnitudeChange'].mean(), 2)

def GetRightAvgAngleChange(map_object):
    return round(map_object.dataframe_struct.df_new_right_swing['_angleMagnitudeChange'].mean(), 2)

def GetAvgAngleChange(map_object):
    return round(map_object.dataframe_struct.df_new_swing['_angleMagnitudeChange'].mean(), 2)

def GetTotalTime(map_object):
    return round(map_object.dataframe_struct.df_new_swing['_timeChangeSeconds'].sum(), 2)

def GetAvgSps(map_object):
    return round(GetTotalSwings(map_object) / GetTotalTime(map_object), 2)

def GetNumDoubles(map_object):
    return len(map_object.dataframe_struct.df_new_swing) - len(map_object.dataframe_struct.df_ignore_doubles)

def GetTrueAccAvgSps(map_object):
    return round(len(map_object.dataframe_struct.df_ignore_doubles) / map_object.dataframe_struct.df_ignore_doubles['_timeChangeSeconds'].sum(), 2)

def HasSliders(map_object, left=None, right=None):
    """
    Checks whether the map contains sliders. Optionally accepts the raw left/right
    note DataFrames so callers can pass them directly.
    """
    left_df = left if left is not None else map_object.dataframe_struct.df_left
    right_df = right if right is not None else map_object.dataframe_struct.df_right

    num_sliders = len(map_object.dataframe_struct.df_left_sliders) + len(map_object.dataframe_struct.df_right_sliders)
    if (num_sliders > 0):
        return 1
    return 0

def GetNumNotes(map_object):
    return len(map_object.dataframe_struct.df_left) + len(map_object.dataframe_struct.df_right)

# The code for calculating peak_sps adapted from Uninstaller's sps calculator

def calculate_swings_list(df_current):
    swing_list = df_current['_seconds'].tolist()
    last = math.floor(df_current['_seconds'].max())
    array = [0 for x in range(math.floor(last) + 1)]
    for swing in swing_list:
        array[math.floor(swing)] += 1
    return array

def calculate_peak_sps(swings_list, interval = 10):

    current_sps_sum = sum(swings_list[:interval])
    max_sps_sum = current_sps_sum
    for x in range(0, len(swings_list) - interval):
        current_sps_sum = current_sps_sum - swings_list[x] + swings_list[x + interval]
        max_sps_sum = max(max_sps_sum, current_sps_sum)
    return round(max_sps_sum / interval, 2)

def GetLeftPeakSps(map_object):
    return round(calculate_peak_sps(calculate_swings_list(map_object.dataframe_struct.df_new_left_swing)), 2)

def GetRightPeakSps(map_object):
    return round(calculate_peak_sps(calculate_swings_list(map_object.dataframe_struct.df_new_right_swing)), 2)

def GetPeakSps(map_object):
    return round(calculate_peak_sps(calculate_swings_list(map_object.dataframe_struct.df_new_swing)), 2)

def GetTrueAccPeakSps(map_object):
    return round(calculate_peak_sps(calculate_swings_list(map_object.dataframe_struct.df_ignore_doubles)), 2)

def get_swings_with_beats(df):
    """
    Returns a list of (sps_value, beat_or_seconds_value)
    where each entry corresponds to one swing.
    """
    swings = calculate_swings_list(df)

    # df_ignore_doubles and swings_list align by index!
    beats = df['_seconds'].tolist()     # consistent across v2/v3

    return list(zip(swings, beats))

def GetSectionsViolatingPeakSps(map_object, interval=10):
    violations = []
    category = map_object.category

    # Only true acc uses peak SPS limit 1.75
    if category == "true":
        df_swing = map_object.dataframe_struct.df_ignore_doubles
        swings_with_beats = get_swings_with_beats(df_swing)

        # Unzip into two lists
        sps_list = [x[0] for x in swings_with_beats]
        beat_list = [x[1] for x in swings_with_beats]

        # Sliding window sum
        current_sum = sum(sps_list[:interval])

        for i in range(len(sps_list) - interval):
            current_sum = current_sum - sps_list[i] + sps_list[i + interval]
            current_sps = current_sum / interval

            if current_sps > 1.75:
                # record the beats involved in this violating window
                violations.append((i + 1, i + 1 + interval))
    else:
        df_swing = map_object.dataframe_struct.df_new_swing
        swings_with_beats = get_swings_with_beats(df_swing)

        # Unzip into two lists
        sps_list = [x[0] for x in swings_with_beats]
        beat_list = [x[1] for x in swings_with_beats]

        # Sliding window sum
        current_sum = sum(sps_list[:interval])

        for i in range(len(sps_list) - interval):
            current_sum = current_sum - sps_list[i] + sps_list[i + interval]
            current_sps = current_sum / interval

            if current_sps > 6.25:
                # record the beats involved in this violating window
                violations.append((i + 1, i + 1 + interval))

    return violations
