"""
Anomaly Detection: flags a performance record when a student's exam score
is significantly worse than their own historical attendance/assignment
baseline - e.g. a normally strong, consistent student who had one bad exam
(illness, personal emergency, etc.).

This is intentionally rule-based and transparent, not machine learning:
the threshold is a fixed, explainable percentage, and flagging never changes
a score automatically - it only surfaces the case for a teacher to review.
"""

ANOMALY_THRESHOLD_PERCENT = 30  # exam score must fall this % below baseline to flag


def detect_anomaly(exam_score: float, past_records: list[dict]) -> tuple[bool, str | None]:
    """
    past_records: this student's PREVIOUS performance records (not including
    the one just submitted), each a dict with 'attendance_percent' and
    'assignment_score'.

    Returns (is_flagged, flag_reason).
    """
    if not past_records:
        return False, None  # no history yet - nothing to compare against

    baseline_values = [
        (r["attendance_percent"] + r["assignment_score"]) / 2
        for r in past_records
    ]
    baseline = sum(baseline_values) / len(baseline_values)

    threshold_score = baseline * (1 - ANOMALY_THRESHOLD_PERCENT / 100)

    if exam_score < threshold_score:
        reason = (
            f"Exam score ({exam_score}) is more than {ANOMALY_THRESHOLD_PERCENT}% "
            f"below this student's attendance/assignment baseline ({baseline:.1f}). "
            f"This may indicate an anomaly (e.g. illness) rather than a genuine decline."
        )
        return True, reason

    return False, None