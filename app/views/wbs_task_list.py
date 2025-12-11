import pandas as pd
import streamlit as st

from components.kanban import summarize_by_status
from components.models import WBSItem

from typing import Dict, List, Optional


from components.data_store import save_data
from components.wbs_structure_table import build_wbs_dataframe, normalize_date_value

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


def render(data, wbs_map):

    render_structure_and_period_table(data)

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
