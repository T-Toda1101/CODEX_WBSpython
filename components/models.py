from dataclasses import dataclass
from typing import Optional

STATUSES = ["Backlog", "In Progress", "Blocked", "Done"]


@dataclass
class WBSItem:
    id: str
    name: str
    parent: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    actual_start_date: Optional[str]
    actual_end_date: Optional[str]


@dataclass
class Task:
    id: str
    title: str
    status: str
    wbs_id: Optional[str]
    priority: str
    due: Optional[str]
    description: str
