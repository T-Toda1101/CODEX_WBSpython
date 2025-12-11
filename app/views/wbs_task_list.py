import pandas as pd
import streamlit as st

from components.kanban import summarize_by_status
from components.models import WBSItem
from views.task_form_view import render_task_form
from views.wbs_creation_view import wbs_creation_form
from views.wbs_structure_view import wbs_structure_view


def render(data, wbs_map):
    st.subheader("WBS & Task List")

    with st.sidebar:
        render_task_form(data, wbs_map)

    wbs_creation_form(data, wbs_map)
    wbs_structure_view(data)

    st.markdown("### タスク一覧")
    if not data.get("tasks"):
        st.info("タスクがまだありません。右のフォームから追加してください。")
        return

    counts = summarize_by_status(data["tasks"])
    st.write(" | ".join([f"{status}: {counts.get(status, 0)}件" for status in counts]))

    task_rows = []
    for task in data.get("tasks", []):
        task_rows.append(
            {
                "タイトル": task.get("title"),
                "ステータス": task.get("status"),
                "WBS": wbs_map.get(task.get("wbs_id"), WBSItem("-", "(未割当)", None, None, None, None, None)).name
                if task.get("wbs_id")
                else "(未割当)",
                "優先度": task.get("priority"),
                "期日": task.get("due"),
                "詳細": task.get("description"),
            }
        )

    st.dataframe(pd.DataFrame(task_rows))
