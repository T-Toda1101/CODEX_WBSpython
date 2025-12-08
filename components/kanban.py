from typing import Dict, List, Optional

import streamlit as st

from .data_store import delete_task, update_task_status
from .models import STATUSES, WBSItem


def wbs_label(wbs_map: Dict[str, WBSItem], wbs_id: Optional[str]) -> str:
    if wbs_id is None:
        return "(未割当)"
    return wbs_map.get(
        wbs_id,
        WBSItem(
            id="-", name="削除済み", parent=None, start_date=None, end_date=None, actual_start_date=None, actual_end_date=None
        ),
    ).name


def kanban_view(data: Dict[str, List[Dict]], wbs_filter: Optional[str], wbs_map: Dict[str, WBSItem]):
    filtered_tasks = [
        task for task in data["tasks"] if (wbs_filter is None or task["wbs_id"] == wbs_filter)
    ]

    st.subheader("かんばんボード")

    for status in STATUSES:
        st.markdown(f"### {status}")
        column_tasks = [t for t in filtered_tasks if t["status"] == status]
        if not column_tasks:
            st.caption("タスクなし")
        for task in column_tasks:
            with st.container(border=True):
                st.markdown(f"**{task['title']}**")
                st.caption(f"WBS: {wbs_label(wbs_map, task['wbs_id'])}")
                meta = []
                if task.get("priority"):
                    meta.append(f"優先度: {task['priority']}")
                if task.get("due"):
                    meta.append(f"期日: {task['due']}")
                if meta:
                    st.caption(" / ".join(meta))
                if task.get("description"):
                    st.write(task["description"])

                with st.form(f"update_{task['id']}"):
                    new_status = st.selectbox(
                        "ステータス変更",
                        STATUSES,
                        index=STATUSES.index(task["status"]),
                        key=f"select_{task['id']}",
                    )
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        submitted = st.form_submit_button("更新")
                    with col2:
                        removed = st.form_submit_button("削除", type="secondary")
                    if submitted and new_status != task["status"]:
                        update_task_status(data, task["id"], new_status)
                    if removed:
                        delete_task(data, task["id"])


def status_summary(tasks: List[Dict]):
    return {status: len([t for t in tasks if t["status"] == status]) for status in STATUSES}
