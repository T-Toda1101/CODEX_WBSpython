import streamlit as st

from components.wbs_structure_table import build_wbs_dataframe
from components.wbs_period_chart import render_period_chart
from components.models import WBSItem

def render(data, wbs_map):
    st.subheader("Gantt View")

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.write("#### タスクリスト / WBS")
        wbs_df = build_wbs_dataframe(data.get("wbs", []))
        st.dataframe(wbs_df[["display_name", "start_date", "end_date"]], use_container_width=True)

    with col_right:
        st.write("#### ガントチャート")
        if data.get("wbs"):
            render_period_chart(build_wbs_dataframe(data.get("wbs", [])))
        else:
            st.info("ガントチャートは後で実装予定です。")
