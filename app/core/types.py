import enum


class TargetType(str, enum.Enum):
    DEPARTMENT = "DEPARTMENT"
    ROLE = "ROLE"
    USER = "USER"


class SourceType(str, enum.Enum):
    ANNOUNCEMENT = "ANNOUNCEMENT"
    EVENT = "EVENT"


class RSVPStatus(str, enum.Enum):
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    TENTATIVE = "TENTATIVE"


class LocationType(str, enum.Enum):
    ONLINE = "ONLINE"
    PHYSICAL = "PHYSICAL"
    HYBRID = "HYBRID"


class CalendarLayer(str, enum.Enum):
    COMPANY = "COMPANY"
    TEAM = "TEAM"
    MINE = "MINE"
