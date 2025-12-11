from typing import Dict, List, Optional

from .models import STATUSES, WBSItem


def format_wbs_label(wbs_map: Dict[str, WBSItem], wbs_id: Optional[str]) -> str:
    """Return a human-friendly WBS label for task cards.

    - 未割当の場合はプレースホルダーを返す
    - 削除済みの可能性があるIDはダミーのWBSItemを作成して対応する
    """
    if wbs_id is None:
        return "(未割当)"

    # 実在しないIDは「削除済み」として扱う
    deleted_placeholder = WBSItem(
        id="-",
        name="削除済み",
        parent=None,
        start_date=None,
        end_date=None,
        actual_start_date=None,
        actual_end_date=None,
    )
    return wbs_map.get(wbs_id, deleted_placeholder).name


def filter_tasks_by_wbs(tasks: List[Dict], wbs_filter: Optional[str]) -> List[Dict]:
    """Return tasks filtered by a selected WBS ID.

    None を受け取った場合はフィルタリングせずに元のタスクリストを返す。
    """
    if wbs_filter is None:
        return tasks

    return [task for task in tasks if task.get("wbs_id") == wbs_filter]


def summarize_tasks_by_status(tasks: List[Dict]) -> Dict[str, int]:
    """Count tasks for each known status.

    STATUSES に含まれないステータスは集計対象外とし、欠損を防ぐために
    全てのステータスキーを初期化した上で集計する。
    """
    summary = {status: 0 for status in STATUSES}
    for task in tasks:
        status = task.get("status")
        if status in summary:
            summary[status] += 1
    return summary


def group_tasks_by_status(tasks: List[Dict]) -> Dict[str, List[Dict]]:
    """Group tasks into a dictionary keyed by status.

    描画処理で扱いやすいように、存在しないステータスでも空リストを用意する。
    """
    grouped = {status: [] for status in STATUSES}
    for task in tasks:
        status = task.get("status")
        if status in grouped:
            grouped[status].append(task)
    return grouped
