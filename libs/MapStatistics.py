"""
This file defines a class MapStatistics that stores statistics about a map
This class will be a field stored within the Map class
The nested structure is for readability, separating map statistics from metadata-related variables
"""
from libs.CalculateStats import (
    GetLeftSwings,
    GetRightSwings,
    GetTotalSwings,
    GetLeftTime, 
    GetRightTime,
    GetLeftAvgSps,
    GetRightAvgSps,
    GetLeftAvgAngleChange,
    GetRightAvgAngleChange,
    GetAvgAngleChange,
    GetTotalTime,
    GetAvgSps,
    GetNumDoubles,
    GetTrueAccAvgSps,
    HasSliders,
    GetNumSliders,
    GetNumOverlapStacks,
    GetNumTowers,
    GetNumWindows,
    GetNumNotes,
    GetLeftPeakSps,
    GetRightPeakSps,
    GetPeakSps,
    GetTrueAccPeakSps,
)

class MapStatistics:
    """
    MapStatistics class delcaration
    Fields:
        - num_left_swings (int): number of left swings
        - num_right_swings (int): number of right swings
        - num_total_swings (int): number of total swings
        - left_time (double): time passed from first left swing to last left swing
        - right_time (double): time passed from first right swing to last right swing
        - left_avg_sps (double): avg sps of left hand
        - right_avg_sps (double): avg sps of right hand
        - left_avg_angle_change (double): avg angle change of left hand
        - right_avg_angle_change (double): avg angle change of right hand
        - avg_angle_change (double): avg angle change considering both hands
        - total_time (double): total time passed from first to last swing for either hand
        - avg_sps (double): avg sps considering both hands
        - number_doubles (int): number of doubles 
        - true_acc_avg_sps (double): avg sps calculation for true acc
        - has_sliders (int): 1 if the map has sliders, 0 otherwise
        - num_sliders (int): number of slider occurrences
        - num_overlap_stacks (int): number of same-time same-hand overlap/stack groups
        - num_towers (int): number of same-time same-hand tower groups
        - num_windows (int): number of same-time same-hand window groups
        - number_notes (int): number of notes
        - left_peak_sps (double): peak sps of left hand
        - right_peak_sps (double): peak sps of right hand
        - peak_sps (double): peak sps considering both hands
        - true_acc_peak_sps (double): peak sps calculation for true acc
    """
    def __init__(self, map_object):
        """
        Constructor
        """
        self.num_left_swings = GetLeftSwings(map_object)
        self.num_right_swings = GetRightSwings(map_object)
        self.num_total_swings = GetTotalSwings(map_object)
        self.left_time = GetLeftTime(map_object)
        self.right_time = GetRightTime(map_object)
        self.left_avg_sps = GetLeftAvgSps(map_object)
        self.right_avg_sps = GetRightAvgSps(map_object)
        self.left_avg_angle_change = GetLeftAvgAngleChange(map_object)
        self.right_avg_angle_change = GetRightAvgAngleChange(map_object)
        self.avg_angle_change = GetAvgAngleChange(map_object)
        self.total_time = GetTotalTime(map_object)
        self.avg_sps = GetAvgSps(map_object)
        self.number_doubles = GetNumDoubles(map_object)
        self.true_acc_avg_sps = GetTrueAccAvgSps(map_object)
        self.has_sliders = HasSliders(
            map_object,
            map_object.dataframe_struct.df_left,
            map_object.dataframe_struct.df_right,
        )
        self.num_sliders = GetNumSliders(map_object)
        self.num_overlap_stacks = GetNumOverlapStacks(map_object)
        self.num_towers = GetNumTowers(map_object)
        self.num_windows = GetNumWindows(map_object)
        self.number_notes = GetNumNotes(map_object)
        self.left_peak_sps = GetLeftPeakSps(map_object)
        self.right_peak_sps = GetRightPeakSps(map_object)
        self.peak_sps = GetPeakSps(map_object)
        self.true_acc_peak_sps = GetTrueAccPeakSps(map_object)
