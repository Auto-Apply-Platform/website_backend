from __future__ import annotations

from dataclasses import dataclass

from app.schemas.request_status import RequestStatus

PIPELINE = (
    RequestStatus.NEW,
    RequestStatus.CV_SEARCH,
    RequestStatus.CV_SENT,
    RequestStatus.DETAILS_CLARIFICATION,
    RequestStatus.CLIENT_REVIEW,
    RequestStatus.PRECHECK,
    RequestStatus.INTERVIEW_1,
    RequestStatus.INTERVIEW_2,
    RequestStatus.INTERVIEW_3,
    RequestStatus.WAIT_DECISION,
    RequestStatus.ON_PROJECT,
)

STAGE_BY_STATUS = {
    RequestStatus.NEW: 0,
    RequestStatus.CV_SEARCH: 1,
    RequestStatus.CV_SENT: 2,
    RequestStatus.DETAILS_CLARIFICATION: 3,
    RequestStatus.CLIENT_REVIEW: 4,
    RequestStatus.PRECHECK: 5,
    RequestStatus.INTERVIEW_1: 6,
    RequestStatus.INTERVIEW_2: 7,
    RequestStatus.INTERVIEW_3: 8,
    RequestStatus.WAIT_DECISION: 9,
    RequestStatus.ON_PROJECT: 10,
}

TRANSITIONS = {
    RequestStatus.NEW: {RequestStatus.CV_SEARCH},
    RequestStatus.CV_SEARCH: {RequestStatus.CV_SENT},
    RequestStatus.CV_SENT: {RequestStatus.DETAILS_CLARIFICATION},
    RequestStatus.DETAILS_CLARIFICATION: {RequestStatus.CLIENT_REVIEW},
    RequestStatus.CLIENT_REVIEW: {RequestStatus.PRECHECK, RequestStatus.INTERVIEW_1},
    RequestStatus.PRECHECK: {RequestStatus.INTERVIEW_1},
    RequestStatus.INTERVIEW_1: {
        RequestStatus.INTERVIEW_2,
        RequestStatus.WAIT_DECISION
    },
    RequestStatus.INTERVIEW_2: {
        RequestStatus.INTERVIEW_3,
        RequestStatus.WAIT_DECISION
    },
    RequestStatus.INTERVIEW_3: {RequestStatus.WAIT_DECISION},
    RequestStatus.WAIT_DECISION: {RequestStatus.ON_PROJECT},
}


def stage(status: RequestStatus) -> int:
    return STAGE_BY_STATUS.get(status, -1)


def is_terminal(status: RequestStatus) -> bool:
    return status == RequestStatus.ON_PROJECT


def is_cancel_status(status: RequestStatus) -> bool:
    return status in (RequestStatus.CANCELLED_BY_US, RequestStatus.REJECTED)


@dataclass(frozen=True)
class TransitionCheck:
    allowed: bool
    reason: str | None = None


def can_transition(
    current: RequestStatus,
    target: RequestStatus,
    *,
    max_stage: int,
) -> TransitionCheck:
    if current == target:
        return TransitionCheck(True)

    if is_terminal(current):
        return TransitionCheck(False, "ON_PROJECT is terminal")

    if is_cancel_status(target):
        return TransitionCheck(True)

    if is_cancel_status(current):
        target_stage = stage(target)
        if target == RequestStatus.ON_PROJECT:
            return TransitionCheck(False, "cannot restore directly to ON_PROJECT")
        if target_stage == -1:
            return TransitionCheck(False, "invalid restore target")
        if target_stage <= max_stage:
            return TransitionCheck(True)
        return TransitionCheck(False, "restore target exceeds max_stage")

    allowed = TRANSITIONS.get(current, set())
    if target in allowed:
        return TransitionCheck(True)
    return TransitionCheck(False, "transition not allowed")


def next_available_statuses(
    current: RequestStatus,
    *,
    max_stage: int,
) -> list[RequestStatus]:
    if is_terminal(current):
        return []

    next_statuses: set[RequestStatus] = set()

    if is_cancel_status(current):
        for status in PIPELINE:
            if status == RequestStatus.ON_PROJECT:
                continue
            if stage(status) <= max_stage:
                next_statuses.add(status)
        return sorted(next_statuses, key=lambda item: stage(item))

    allowed = TRANSITIONS.get(current, set())
    next_statuses.update(allowed)
    next_statuses.add(RequestStatus.CANCELLED_BY_US)
    next_statuses.add(RequestStatus.REJECTED)

    return sorted(next_statuses, key=lambda item: stage(item) if stage(item) >= 0 else 999)
