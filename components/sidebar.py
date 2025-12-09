from datetime import date
from typing import Dict

import streamlit as st

from .data_store import add_task
from .models import STATUSES, WBSItem


def sidebar_forms(data: Dict, wbs_map: Dict[str, WBSItem]):
    st.sidebar.header("タスクの新規作成")

    task_title = st.sidebar.text_input("タスク名", placeholder="例: ユーザーヒアリング")

    selected_wbs = st.sidebar.selectbox(
        "紐づくWBS",
        options=[None] + list(wbs_map.keys()),
        format_func=lambda x: "(未割当)" if x is None else wbs_map[x].name,
    )

    priority = st.sidebar.selectbox("優先度", ["高", "中", "低"], index=1)
    status = st.sidebar.selectbox("初期ステータス", STATUSES, index=0)

    description = st.sidebar.text_area("詳細", height=100)

    use_due = st.sidebar.checkbox("期日を設定する", value=False, key="use_due_date")

    if use_due:
        due_input = st.sidebar.date_input("期日", value=date.today(), key="due_date")
    else:
        due_input = None



    # フォームなし → ボタン押した瞬間に実行
    if st.sidebar.button("タスクを追加") and task_title:
        add_task(data, task_title, selected_wbs, priority, due_input, status, description)
