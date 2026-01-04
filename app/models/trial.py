from dataclasses import dataclass
from typing import List, Optional

VALID_STATUSES = [
    ("RECRUITING", "Recruiting"),
    ("NOT_YET_RECRUITING", "Not Yet Recruiting"),
    ("ACTIVE_NOT_RECRUITING", "Active, Not Recruiting"),
    ("COMPLETED", "Completed"),
    ("ENROLLING_BY_INVITATION", "Enrolling by Invitation"),
    ("SUSPENDED", "Suspended"),
    ("TERMINATED", "Terminated"),
    ("WITHDRAWN", "Withdrawn"),
]

VALID_PHASES = [
    ("EARLY_PHASE1", "Early Phase 1"),
    ("PHASE1", "Phase 1"),
    ("PHASE2", "Phase 2"),
    ("PHASE3", "Phase 3"),
    ("PHASE4", "Phase 4"),
]

@dataclass
class Trial:
    nct_id: str
    title: str
    phase: str
    status: str
    sponsor: str
    conditions: List[str]
    interventions: List[str]

@dataclass
class SearchParams:
    compound: Optional[str] = None
    condition: Optional[str] = None
    phases: Optional[List[str]] = None
    statuses: Optional[List[str]] = None

@dataclass
class SearchResult:
    trials: List[Trial]
    total_count: int
    truncated: bool  # True if results exceeded MAX_RESULTS limit
