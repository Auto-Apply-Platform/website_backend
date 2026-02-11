from enum import Enum


class RequestStatus(str, Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    ON_PROJECT = "on_project"
    CANCELED_BY_US = "canceled_by_us"
    REJECTED = "rejected"
