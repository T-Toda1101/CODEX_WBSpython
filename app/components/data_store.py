import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set

import streamlit as st

from .models import STATUSES, WBSItem

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_FILE = DATA_DIR / "wbs_data.json"


def ensure_data_file_exists() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("{\n  \"wbs\": [],\n  \"tasks\": []\n}\n", encoding="utf-8")


def load_data() -> Dict[str, List[Dict]]:
    if not DATA_FILE.exists():
        return {"wbs": [], "tasks": []}
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: Dict[str, List[Dict]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    st.session_state["data"] = data


def build_wbs_map(items: List[Dict]) -> Dict[str, WBSItem]:
    return {
        item["id"]: WBSItem(
            id=item["id"],
            name=item["name"],
            parent=item.get("parent"),
            start_date=item.get("start_date"),
            end_date=item.get("end_date"),
            actual_start_date=item.get("actual_start_date"),
            actual_end_date=item.get("actual_end_date"),
        )
        for item in items
    }


def add_wbs_item(
    data: Dict[str, List[Dict]],
    name: str,
    parent: Optional[str],
    start_date,
    end_date,
):
    data["wbs"].append(
        {
            "id": str(uuid.uuid4()),
            "name": name,
            "parent": parent,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "actual_start_date": None,
            "actual_end_date": None,
        }
    )
    save_data(data)
    st.success(f"WBS項目を追加しました: {name}")


def add_task(
    data: Dict[str, List[Dict]],
    title: str,
    wbs_id: Optional[str],
    due_date,
    status: str,
    description: str,
):
    due_value = due_date.isoformat() if due_date else None
    data["tasks"].append(
        {
            "id": str(uuid.uuid4()),
            "title": title,
            "status": status,
            "wbs_id": wbs_id,
            "due": due_value,
            "description": description,
        }
    )
    save_data(data)
    st.success(f"タスクを追加しました: {title}")


def update_task_status(data: Dict[str, List[Dict]], task_id: str, status: str):
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["status"] = status
            save_data(data)
            st.toast("ステータスを更新しました")
            break


def delete_task(data: Dict[str, List[Dict]], task_id: str):
    before = len(data["tasks"])
    data["tasks"] = [task for task in data["tasks"] if task["id"] != task_id]
    if len(data["tasks"]) < before:
        save_data(data)
        st.toast("タスクを削除しました", icon="⚠️")


def delete_tasks(data: Dict[str, List[Dict]], task_ids: Set[str]) -> int:
    before = len(data.get("tasks", []))
    data["tasks"] = [task for task in data.get("tasks", []) if task.get("id") not in task_ids]
    removed = before - len(data["tasks"])
    if removed:
        save_data(data)
        st.toast(f"{removed}件のタスクを削除しました", icon="⚠️")
    return removed


def delete_wbs_items(data: Dict[str, List[Dict]], wbs_ids: Set[str]) -> int:
    """削除対象のWBSと紐づくタスクのWBS紐付けを外す."""

    before = len(data["wbs"])
    data["wbs"] = [item for item in data["wbs"] if item.get("id") not in wbs_ids]

    for task in data.get("tasks", []):
        if task.get("wbs_id") in wbs_ids:
            task["wbs_id"] = None

    removed = before - len(data["wbs"])
    if removed:
        save_data(data)
        st.toast(f"{removed}件のWBSを削除しました", icon="⚠️")

    return removed


def status_summary(tasks: List[Dict]):
    return {status: len([t for t in tasks if t.get("status") == status]) for status in STATUSES}
