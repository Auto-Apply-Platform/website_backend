from __future__ import annotations

from app.schemas.response_stage import ResponseStage


STAGE_ORDER = [
    ResponseStage.CV_SELECTED,
    ResponseStage.CV_SENT,
    ResponseStage.DETAILS_CLARIFICATION,
    ResponseStage.CLIENT_REVIEW,
    ResponseStage.PRECHECK,
    ResponseStage.INTERVIEW_1,
    ResponseStage.INTERVIEW_2,
    ResponseStage.INTERVIEW_3,
    ResponseStage.WAIT_DECISION,
    ResponseStage.ON_PROJECT,
    ResponseStage.CANCELLED_BY_US,
    ResponseStage.REJECTED,
]

STAGE_INDEX = {stage: idx + 1 for idx, stage in enumerate(STAGE_ORDER)}

ALLOWED_TRANSITIONS = {
    ResponseStage.CV_SELECTED: {
        ResponseStage.CV_SENT,
        ResponseStage.CANCELLED_BY_US,
        ResponseStage.REJECTED,
    },
    ResponseStage.CV_SENT: {
        ResponseStage.DETAILS_CLARIFICATION,
        ResponseStage.CANCELLED_BY_US,
        ResponseStage.REJECTED,
    },
    ResponseStage.DETAILS_CLARIFICATION: {
        ResponseStage.CLIENT_REVIEW,
        ResponseStage.CANCELLED_BY_US,
        ResponseStage.REJECTED,
    },
    ResponseStage.CLIENT_REVIEW: {
        ResponseStage.PRECHECK,
        ResponseStage.INTERVIEW_1,
        ResponseStage.CANCELLED_BY_US,
        ResponseStage.REJECTED,
    },
    ResponseStage.PRECHECK: {
        ResponseStage.INTERVIEW_1,
        ResponseStage.CANCELLED_BY_US,
        ResponseStage.REJECTED,
    },
    ResponseStage.INTERVIEW_1: {
        ResponseStage.INTERVIEW_2,
        ResponseStage.WAIT_DECISION,
        ResponseStage.CANCELLED_BY_US,
        ResponseStage.REJECTED,
    },
    ResponseStage.INTERVIEW_2: {
        ResponseStage.INTERVIEW_3,
        ResponseStage.WAIT_DECISION,
        ResponseStage.CANCELLED_BY_US,
        ResponseStage.REJECTED,
    },
    ResponseStage.INTERVIEW_3: {
        ResponseStage.WAIT_DECISION,
        ResponseStage.CANCELLED_BY_US,
        ResponseStage.REJECTED,
    },
    ResponseStage.WAIT_DECISION: {
        ResponseStage.ON_PROJECT,
        ResponseStage.CANCELLED_BY_US,
        ResponseStage.REJECTED,
    },
    ResponseStage.ON_PROJECT: {},
    ResponseStage.CANCELLED_BY_US: set(),
    ResponseStage.REJECTED: set(),
}


def can_transition(
    from_stage: ResponseStage | None,
    to_stage: ResponseStage,
    max_stage: int,
) -> tuple[bool, int]:
    no_max_stage_change = {
        ResponseStage.ON_PROJECT,
        ResponseStage.CANCELLED_BY_US,
        ResponseStage.REJECTED,
    }
    if from_stage is None:
        return True, max_stage
    if from_stage == to_stage:
        return True, max_stage
    if from_stage in {ResponseStage.CANCELLED_BY_US, ResponseStage.REJECTED}:
        if to_stage in {ResponseStage.CANCELLED_BY_US, ResponseStage.REJECTED}:
            return True, max_stage
        to_index = STAGE_INDEX.get(to_stage, 0)
        if to_index <= max_stage:
            if to_stage in no_max_stage_change:
                return True, max_stage
            return True, to_index
        return False, max_stage
    allowed = ALLOWED_TRANSITIONS.get(from_stage, set())
    if to_stage not in allowed:
        return False, max_stage
    to_index = STAGE_INDEX.get(to_stage, max_stage)
    if to_index > max_stage:
        if to_stage in no_max_stage_change:
            return True, max_stage
        return True, to_index
    if to_stage in no_max_stage_change:
        return True, max_stage
    return True, max_stage


def allowed_stages(
    from_stage: ResponseStage | None,
    max_stage: int,
) -> list[ResponseStage]:
    if from_stage is None:
        return []
    if from_stage in {ResponseStage.CANCELLED_BY_US, ResponseStage.REJECTED}:
        allowed = {ResponseStage.CANCELLED_BY_US, ResponseStage.REJECTED}
        for stage_item in STAGE_ORDER:
            if STAGE_INDEX[stage_item] <= max_stage:
                allowed.add(stage_item)
        allowed.discard(from_stage)
        return sorted(allowed, key=lambda stage: STAGE_INDEX[stage])
    allowed = set(ALLOWED_TRANSITIONS.get(from_stage, set()))
    allowed.discard(from_stage)
    return sorted(allowed, key=lambda stage: STAGE_INDEX[stage])
