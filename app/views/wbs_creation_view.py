from datetime import date
from typing import Dict

import streamlit as st

from components.data_store import add_wbs_item
from components.models import WBSItem


def wbs_creation_form(data: Dict, wbs_map: Dict[str, WBSItem]):
    st.markdown("### WBSを追加")
    with st.form("create_wbs_main"):
        wbs_name = st.text_input("WBS名", placeholder="例: フェーズA / 要件定義")
        parent_choice = st.selectbox(
            "親WBS",
            options=[None] + list(wbs_map.keys()),
            format_func=lambda x: "(トップレベル)" if x is None else wbs_map[x].name,
        )
        col1, col2 = st.columns(2)
        with col1:
            start_input = st.date_input("開始予定日", value=date.today())
        with col2:
            end_input = st.date_input("終了予定日", value=date.today())

        submitted = st.form_submit_button("WBSを追加")
        if submitted:
            if not wbs_name:
                st.error("WBS名を入力してください")
            elif start_input and end_input and start_input > end_input:
                st.error("終了予定日は開始予定日以降の日付を選択してください")
            else:
                add_wbs_item(data, wbs_name, parent_choice, start_input, end_input)
