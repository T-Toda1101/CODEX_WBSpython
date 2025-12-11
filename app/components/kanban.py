from typing import Dict, List, Optional

import streamlit as st

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


def render_kanban_columns(tasks: List[Dict], wbs_map: Dict[str, WBSItem]):
    cols = st.columns(len(STATUSES))
    for col, status in zip(cols, STATUSES):
        col.write(f"### {status}")
        status_tasks = [t for t in tasks if t.get("status") == status]
        if not status_tasks:
            col.write("(カードを後で実装)")
            continue
        for task in status_tasks:
            with col.container(border=True):
                col.markdown(f"**{task.get('title', 'No Title')}**")
                col.caption(f"WBS: {wbs_label(wbs_map, task.get('wbs_id'))}")
                meta = []
                if task.get("priority"):
                    meta.append(f"優先度: {task['priority']}")
                if task.get("due"):
                    meta.append(f"期日: {task['due']}")
                if meta:
                    col.caption(" / ".join(meta))
                if task.get("description"):
                    col.write(task["description"])
