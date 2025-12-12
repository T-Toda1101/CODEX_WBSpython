from datetime import date
from typing import Dict, List, Optional, Set

import pandas as pd


def parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def flatten_wbs_with_levels(wbs_items: List[Dict]) -> List[Dict]:
    ordered: List[Dict] = []

    def walk(parent: Optional[str], level: int):
        children = [item for item in wbs_items if item.get("parent") == parent]
        for child in children:
            ordered.append({"item": child, "level": level})
            walk(child["id"], level + 1)

    walk(None, 0)
    return ordered


def collect_descendants(wbs_items: List[Dict], root_id: str) -> Set[str]:
    descendants: Set[str] = set()

    def dfs(parent_id: str):
        for item in wbs_items:
            if item.get("parent") == parent_id:
                child_id = item.get("id")
                if child_id:
                    descendants.add(child_id)
                    dfs(child_id)

    dfs(root_id)
    return descendants


def normalize_date_value(value: Optional[object]) -> Optional[str]:
    """Convert mixed date inputs from data_editor rows to ISO strings."""

    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, str):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            return None

    return None


def build_wbs_dataframe(wbs_items: List[Dict]) -> pd.DataFrame:
    ordered_items = flatten_wbs_with_levels(wbs_items)
    rows = []
    for entry in ordered_items:
        item = entry["item"]
        level = entry["level"]
        rows.append(
            {
                "id": item["id"],
                "display_name": "　" * level + item["name"],
                "parent": item.get("parent"),
                "start_date": parse_iso_date(item.get("start_date")),
                "end_date": parse_iso_date(item.get("end_date")),
                "actual_start_date": parse_iso_date(item.get("actual_start_date")),
                "actual_end_date": parse_iso_date(item.get("actual_end_date")),
                "delete": False,
            }
        )

    return pd.DataFrame(rows)
