from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from components.data_store import save_data
from components.wbs_structure_table import build_wbs_dataframe, normalize_date_value
from .wbs_period_chart_view import render_period_chart


def render_structure_and_period_table(
    data: Dict[str, List[Dict]]
) -> Optional[pd.DataFrame]:
    """Display the WBS structure table and persist date updates."""

    wbs_items = data.get("wbs", [])
    if not wbs_items:
        st.info("まだWBSがありません。下のフォームから追加してください。")
        return None

    wbs_df = build_wbs_dataframe(wbs_items)

    st.markdown("### WBS構造と期間")

    with st.expander("構造順テーブル", expanded=True):
        edited_df = st.data_editor(
            wbs_df,
            hide_index=True,
            disabled=["id", "display_name"],
            column_config={
                "display_name": st.column_config.Column("WBS名 "),
                "start_date": st.column_config.DateColumn("開始予定日"),
                "end_date": st.column_config.DateColumn("終了予定日"),
                "actual_start_date": st.column_config.DateColumn("実績開始日"),
                "actual_end_date": st.column_config.DateColumn("実績終了日"),
            },
            key="wbs_structure_editor",
        )

        if st.button("予定・実績日を保存", key="save_wbs_dates"):
            updates = 0
            for _, row in edited_df.iterrows():
                target = next((i for i in data["wbs"] if i["id"] == row["id"]), None)
                if not target:
                    continue
                new_start = normalize_date_value(row.get("start_date"))
                new_end = normalize_date_value(row.get("end_date"))
                new_actual_start = normalize_date_value(row.get("actual_start_date"))
                new_actual_end = normalize_date_value(row.get("actual_end_date"))
                if (
                    target.get("start_date") != new_start
                    or target.get("end_date") != new_end
                    or target.get("actual_start_date") != new_actual_start
                    or target.get("actual_end_date") != new_actual_end
                ):
                    target["start_date"] = new_start
                    target["end_date"] = new_end
                    target["actual_start_date"] = new_actual_start
                    target["actual_end_date"] = new_actual_end
                    updates += 1
            if updates:
                save_data(data)
                st.success(f"{updates}件のWBSの日付を更新しました")
            else:
                st.info("変更はありませんでした")

    return edited_df


def wbs_structure_view(data: Dict[str, List[Dict]]):
    edited_df = render_structure_and_period_table(data)
    if edited_df is None:
        return

    render_period_chart(edited_df)
