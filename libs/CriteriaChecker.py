"""
This file handles criteria checks
"""
from libs.ObstacleDetector import (
    RunAllPostBombChecks,
    RunAllPreBombChecks,
)
from libs.CalculateStats import GetSectionsViolatingPeakSps

def UniversalCriteriaChecks(map_object):
    """
    This checks the criteria for all categories
    """
    logs_list = map_object.logs_list

    # 6 minute maximum time between first and last note
    time = map_object.statistics.total_time
    if (time > 360):
        logs_list.append("Fail: The time between the first and last note is " + str(round(time, 2)) + " seconds which is more than 6 minutes\n")

    # Each hand must start on a downswing (down or down-diagonal)
    if (map_object.metadata_version == "v2"):
        df_newLeftSwing = map_object.dataframe_struct.df_new_left_swing
        df_newRightSwing = map_object.dataframe_struct.df_new_right_swing
        if (((df_newLeftSwing.iloc[0].loc['_cutDirection'] != 1) and (df_newLeftSwing.iloc[0].loc['_cutDirection'] != 8) and (df_newLeftSwing.iloc[0].loc['_cutDirection'] != 6) and (df_newLeftSwing.iloc[0].loc['_cutDirection'] != 7)) or ((df_newRightSwing.iloc[0].loc['_cutDirection'] != 1) and (df_newRightSwing.iloc[0].loc['_cutDirection'] != 8) and (df_newRightSwing.iloc[0].loc['_cutDirection'] != 6) and (df_newRightSwing.iloc[0].loc['_cutDirection'] != 7))):
            logs_list.append("Fail: At least one of the hands does not start on a downswing\n")
    if (map_object.metadata_version == "v3"):
        df_newLeftSwing = map_object.dataframe_struct.df_new_left_swing
        df_newRightSwing = map_object.dataframe_struct.df_new_right_swing
        if (((df_newLeftSwing.iloc[0].loc['d'] != 1) and (df_newLeftSwing.iloc[0].loc['d'] != 8) and (df_newLeftSwing.iloc[0].loc['d'] != 6) and (df_newLeftSwing.iloc[0].loc['d'] != 7)) or ((df_newRightSwing.iloc[0].loc['d'] != 1) and (df_newRightSwing.iloc[0].loc['d'] != 8) and (df_newRightSwing.iloc[0].loc['d'] != 6) and (df_newRightSwing.iloc[0].loc['d'] != 7))):
            logs_list.append("Fail: At least one of the hands does not start on a downswing\n")

    # Note count minimum: 115
    notes = map_object.statistics.number_notes
    if (notes < 115):
        logs_list.append("Fail: There are " + str(notes) + " notes, which is less than 115\n")

    # Min space before notes after bombs: 150ms
    violations = RunAllPostBombChecks(map_object)
    if (len(violations) > 0):
        for entry in violations:
            logs_list.append("Fail: This breaks the post-bomb criteria at beat " + str(entry) + " \n")

def TrueAccCriteriaChecks(map_object):
    """
    This checks true acc exclusive criteria
    """
    logs_list = map_object.logs_list

    # 2 minute minimum time between first and last note
    time = map_object.statistics.total_time
    if (time < 120):
        logs_list.append("Fail: The time between the first and last note is " + str(time) + " seconds which is less than 2 minutes\n")

    # NJS limit: 12 NJS
    njs = map_object.njs
    if (njs > 12):
        logs_list.append("Fail: njs is " + str(njs) + " which is greater than 12\n")

    # Max peak SPS counting doubles as one swing: 1.75
    true_acc_peak_sps = map_object.statistics.true_acc_peak_sps
    if (true_acc_peak_sps > 1.75):
        logs_list.append("Fail: the max peak sps counting doubles as one swing is " + str(true_acc_peak_sps) + " swings per second, which is more than 1.75\n")
        violations = GetSectionsViolatingPeakSps(map_object)
        for entry in violations:
            logs_list.append("Fail: This breaks the true acc peak sps criteria at beat " + str(entry) + " \n")

    # Max average SPS counting doubles as one swing: 1.5
    true_acc_avg_sps = map_object.statistics.true_acc_avg_sps
    if (true_acc_avg_sps > 1.5):
        logs_list.append("Fail: the average sps counting doubles as one swing is " + str(true_acc_avg_sps) + " swings per second, which is more than 1.5\n")

    # No stacks, sliders, or windows
    if (map_object.statistics.number_notes != len(map_object.dataframe_struct.df_new_swing)):
        logs_list.append("Fail: There are sliders, stacks, towers, or windows in this map\n")

    # Min time after notes before bombs: 500ms
    violations = RunAllPreBombChecks(map_object)
    if (len(violations) > 0):
        for entry in violations:
            logs_list.append("Fail: This breaks the pre-bomb criteria at beat " + str(entry) + " \n")


def StandardAccCriteriaChecks(map_object):
    """
    This checks standard acc exclusive criteria
    """
    logs_list = map_object.logs_list

    # 1:45 minute minimum time between first and last note
    time = map_object.statistics.total_time
    if (time < 105):
        logs_list.append("Fail: The time between the first and last note is " + str(time) + " seconds which is less than 1 minute 45 seconds\n")


    # NJS limit: 16 NJS
    njs = map_object.njs
    if (njs > 16):
        logs_list.append("Fail: njs is " + str(njs) + " which is greater than 16\n")

    # Max peak SPS: 6.25
    peak_sps = map_object.statistics.peak_sps
    if (peak_sps > 6.25):
        logs_list.append("Fail: the peak sps is " + str(peak_sps) + " swings per second, which is more than 6.25\n")
        violations = GetSectionsViolatingPeakSps(map_object)
        for entry in violations:
            logs_list.append("Fail: This breaks the standard acc peak sps criteria at beat " + str(entry) + " \n")

    # Max average SPS: 4
    avg_sps = map_object.statistics.avg_sps
    if (avg_sps > 4):
        logs_list.append("Fail: the average sps is " + str(avg_sps) + " swings per second, which is more than 4\n")

    # No sliders
    if (map_object.statistics.has_sliders):
        logs_list.append("Fail: the map has sliders\n")

    # Bombs that don't affect swing path and are placed against the 
    # direction of the previous swing will only require y =1500/x 
    # of distance from the previous note, where x is the NJS
    # For other cases, min time after notes before bombs: 350ms
    violations = RunAllPreBombChecks(map_object)
    if (len(violations) > 0):
        for entry in violations:
            logs_list.append("Fail: This breaks the pre-bomb criteria at beat " + str(entry) + " \n")

def TechAccCriteriaChecks(map_object):
    """
    This checks tech acc exclusive criteria
    """
    logs_list = map_object.logs_list

    # 1:45 minute minimum time between first and last note
    time = map_object.statistics.total_time
    if (time < 105):
        logs_list.append("Fail: The time between the first and last note is " + str(time) + " seconds which is less than 1 minute 45 seconds\n")

    # NJS limit: 16 NJS
    njs = map_object.njs
    if (njs > 16):
        logs_list.append("Fail: njs is " + str(njs) + " which is greater than 16\n")

    # Max peak SPS: 6.25
    peak_sps = map_object.statistics.peak_sps
    if (peak_sps > 6.25):
        logs_list.append("Fail: the peak sps is " + str(peak_sps) + " swings per second, which is more than 6.25\n")
        violations = GetSectionsViolatingPeakSps(map_object)
        for entry in violations:
            logs_list.append("Fail: This breaks the tech acc peak sps criteria at beat " + str(entry) + " \n")

    # Max average SPS: 4
    avg_sps = map_object.statistics.avg_sps
    if (avg_sps > 4):
        logs_list.append("Fail: the average sps is " + str(avg_sps) + " swings per second, which is more than 4\n")

    # Bombs that don't affect swing path and are placed against the 
    # direction of the previous swing will only require y =1500/x 
    # of distance from the previous note, where x is the NJS
    # For other cases, min time after notes before bombs: 300ms
    violations = RunAllPreBombChecks(map_object)
    if (len(violations) > 0):
        for entry in violations:
            logs_list.append("Fail: This breaks the pre-bomb criteria at beat " + str(entry) + " \n")


def RunCriteriaChecks(map_object):
    """
    This is the point of entry for running the criteria checks
    """
    logs_list = map_object.logs_list

    UniversalCriteriaChecks(map_object)

    if (map_object.category == "true"):
        TrueAccCriteriaChecks(map_object)
    if (map_object.category == "standard"):
        StandardAccCriteriaChecks(map_object)
    if (map_object.category == "tech"):
        TechAccCriteriaChecks(map_object)
    
    if (len(logs_list) > 0):
        print("This map failed the criteria for the " + str(map_object.category) + " acc category\n")
        print("Logs:\n")
        for entry in logs_list:
            print(entry)
    else:
        print("This map passed the criteria for the " + str(map_object.category) + " acc category! Make sure the map still passes QAT tests")

    return logs_list