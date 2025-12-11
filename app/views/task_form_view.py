from datetime import date
from typing import Dict

import streamlit as st

from components.data_store import add_task
from components.models import STATUSES, WBSItem


def render_task_form(data: Dict, wbs_map: Dict[str, WBSItem]):
    st.header("タスクの追加 / 編集")

    task_title = st.text_input("タスク名", placeholder="例: ユーザーヒアリング")

    selected_wbs = st.selectbox(
        "紐づくWBS",
        options=[None] + list(wbs_map.keys()),
        format_func=lambda x: "(未割当)" if x is None else wbs_map[x].name,
    )

    priority = st.selectbox("優先度", ["高", "中", "低"], index=1)
    status = st.selectbox("ステータス", STATUSES, index=0)

    description = st.text_area("詳細", height=100)

    use_due = st.checkbox("期日を設定する", value=False, key="use_due_date")

    if use_due:
        due_input = st.date_input("期日", value=date.today(), key="due_date")
    else:
        due_input = None

    if st.button("タスクを追加") and task_title:
        add_task(data, task_title, selected_wbs, priority, due_input, status, description)
