"""
The Weighted Scoring Algorithm.

Formula:
    weighted_score = (attendance_percent * attendance_weight)
                    + (assignment_score  * assignment_weight)
                    + (exam_score        * exam_weight)

Classification thresholds:
    >= 75  -> Top Performer
    50-74  -> Average Performer
    < 50   -> At-Risk
"""
from app.models.performance_score import PerformanceCategory

TOP_PERFORMER_THRESHOLD = 75
AVERAGE_PERFORMER_THRESHOLD = 50


def calculate_weighted_score(
    attendance_percent: float,
    assignment_score: float,
    exam_score: float,
    attendance_weight: float,
    assignment_weight: float,
    exam_weight: float,
) -> float:
    score = (
        attendance_percent * attendance_weight
        + assignment_score * assignment_weight
        + exam_score * exam_weight
    )
    return round(score, 2)


def classify_score(weighted_score: float) -> PerformanceCategory:
    if weighted_score >= TOP_PERFORMER_THRESHOLD:
        return PerformanceCategory.TOP_PERFORMER
    elif weighted_score >= AVERAGE_PERFORMER_THRESHOLD:
        return PerformanceCategory.AVERAGE_PERFORMER
    else:
        return PerformanceCategory.AT_RISK