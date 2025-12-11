from datetime import date
from typing import Dict, List, Optional

from .wbs_structure_table import parse_iso_date


def _is_within_range(target: Optional[date], start: Optional[date], end: Optional[date]) -> bool:
    if start and target and target < start:
        return False
    if end and target and target > end:
        return False
    return True


def _wbs_matches(item: Dict, start: Optional[date], end: Optional[date], level_query: Optional[str]) -> bool:
    start_date = parse_iso_date(item.get("start_date"))
    end_date = parse_iso_date(item.get("end_date"))

    if not _is_within_range(start_date or end_date, start, end):
        return False

    if level_query and level_query not in item.get("name", ""):
        return False

    return True


def _task_matches(
    task: Dict,
    start: Optional[date],
    end: Optional[date],
    status: Optional[str],
    allowed_wbs: Optional[List[str]],
) -> bool:
    due_date = parse_iso_date(task.get("due"))

    if status and task.get("status") != status:
        return False

    if not _is_within_range(due_date, start, end):
        return False

    if allowed_wbs is not None:
        task_wbs = task.get("wbs_id")
        if task_wbs and task_wbs not in allowed_wbs:
            return False

    return True


def apply_filters(data: Dict[str, List[Dict]], filters: Dict) -> Dict[str, List[Dict]]:
    """Return WBSとタスクのフィルター済みデータセット."""

    if not filters.get("enabled"):
        return data

    start: Optional[date] = filters.get("start")
    end: Optional[date] = filters.get("end")
    status: Optional[str] = filters.get("status")
    level_query: Optional[str] = filters.get("level")

    filtered_wbs = [
        item
        for item in data.get("wbs", [])
        if _wbs_matches(item, start, end, level_query)
    ]

    allowed_wbs = [item.get("id") for item in filtered_wbs] if level_query else None

    filtered_tasks = [
        task
        for task in data.get("tasks", [])
        if _task_matches(task, start, end, status, allowed_wbs)
    ]

    return {"wbs": filtered_wbs, "tasks": filtered_tasks}
