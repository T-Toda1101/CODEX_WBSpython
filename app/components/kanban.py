from typing import Dict, List, Optional

from .models import STATUSES, WBSItem


def wbs_label(wbs_map: Dict[str, WBSItem], wbs_id: Optional[str]) -> str:
    if wbs_id is None:
        return "(未割当)"
    return wbs_map.get(
        wbs_id,
        WBSItem(
            id="-",
            name="削除済み",
            parent=None,
            start_date=None,
            end_date=None,
            actual_start_date=None,
            actual_end_date=None,
        ),
    ).name


def summarize_by_status(tasks: List[Dict]):
    return {status: len([t for t in tasks if t.get("status") == status]) for status in STATUSES}
