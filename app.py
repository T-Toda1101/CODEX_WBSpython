from pathlib import Path
from typing import Optional

import streamlit as st

from components.data_store import DATA_FILE, build_wbs_map, load_data
from components.kanban import kanban_view, status_summary
from components.models import STATUSES
from components.sidebar import sidebar_forms
from components.wbs_creation import wbs_creation_form
from components.wbs_structure import wbs_structure_view

st.set_page_config(page_title="WBS & Kanban", layout="wide")


def ensure_data_file_exists():
    data_path: Path = DATA_FILE
    data_path.parent.mkdir(parents=True, exist_ok=True)
    if not data_path.exists():
        data_path.write_text("{\n  \"wbs\": [],\n  \"tasks\": []\n}\n", encoding="utf-8")


def main():
    st.title("WBSとタスク管理 (かんばん式)")
    st.caption("単独ユーザ向けの簡易WBS管理＆かんばんツール")

    ensure_data_file_exists()
    data = load_data()
    wbs_map = build_wbs_map(data.get("wbs", []))

    sidebar_forms(data, wbs_map)

    wbs_tab, task_tab = st.tabs(["WBS管理", "タスク管理"])

    with wbs_tab:
        wbs_creation_form(data, wbs_map)
        wbs_structure_view(data)

    with task_tab:
        wbs_filter: Optional[str] = st.selectbox(
            "かんばんの表示対象",
            options=[None] + list(wbs_map.keys()),
            format_func=lambda x: "全タスク" if x is None else wbs_map[x].name,
            key="wbs_filter",
        )

        counts = status_summary(data["tasks"])
        st.write(
            " | ".join([f"{status}: {counts.get(status, 0)}件" for status in STATUSES])
        )

        kanban_view(data, wbs_filter, wbs_map)


if __name__ == "__main__":
    main()
