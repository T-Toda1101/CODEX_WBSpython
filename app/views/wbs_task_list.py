from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from components.kanban import summarize_tasks_by_status
from components.models import WBSItem
from components.data_store import delete_wbs_items, save_data
from components.wbs_structure_table import (
    build_wbs_dataframe,
    collect_descendants,
    normalize_date_value,
)

def render_structure_and_period_table(
    data: Dict[str, List[Dict]],
    wbs_items: List[Dict],
) -> Optional[pd.DataFrame]:
    """Display the WBS structure table and persist date updates."""

    if not wbs_items:
        st.info("まだWBSがありません。下のフォームから追加してください。")
        return None

    wbs_df = build_wbs_dataframe(wbs_items)

    st.markdown("### WBS構造と期間")

    with st.expander("構造順テーブル", expanded=True):
        parent_label_map = {item.get("id"): item.get("name") for item in data.get("wbs", [])}
        parent_display_map = {None: "(トップレベル)"}
        for item in data.get("wbs", []):
            wbs_id = item.get("id")
            if not wbs_id:
                continue
            parent_display_map[wbs_id] = item.get('name')

        wbs_df["parent_selection"] = wbs_df["parent"].apply(
            lambda value: parent_display_map.get(value, "-")
        )
        parent_options = [v for v in parent_display_map.values() if v]
        parent_option_to_id = {v: k for k, v in parent_display_map.items()}
        wbs_df = wbs_df.drop(columns=["parent"])

        edited_df = st.data_editor(
            wbs_df,
            hide_index=True,
            column_config={
                "display_name": st.column_config.Column("WBS名 "),
                "parent_selection": st.column_config.SelectboxColumn(
                    "親WBS",
                    options=parent_options,
                ),
                "start_date": st.column_config.DateColumn("開始予定日"),
                "end_date": st.column_config.DateColumn("終了予定日"),
                "actual_start_date": st.column_config.DateColumn("実績開始日"),
                "actual_end_date": st.column_config.DateColumn("実績終了日"),
                "delete": st.column_config.CheckboxColumn("削除", default=False),
            },
            key="wbs_structure_editor",
        )

        if st.button("変更を保存", key="save_wbs_dates"):
            updates = 0
            parent_updates = 0
            errors = []
            id_to_item = {item.get("id"): item for item in data.get("wbs", [])}
            descendants_map = {
                item.get("id"): collect_descendants(data.get("wbs", []), item.get("id"))
                for item in data.get("wbs", [])
            }

            delete_targets = set(
                row.get("id")
                for _, row in edited_df.iterrows()
                if bool(row.get("delete"))
            )

            for target_id in list(delete_targets):
                delete_targets.update(descendants_map.get(target_id, set()))

            for _, row in edited_df.iterrows():
                target = id_to_item.get(row.get("id"))
                if not target or target.get("id") in delete_targets:
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

                parent_selection = row.get("parent_selection")
                new_parent = (
                    parent_option_to_id.get(parent_selection)
                    if not pd.isna(parent_selection)
                    else None
                )
                if new_parent in delete_targets:
                    errors.append(f"{target.get('name')} の親が削除対象になっています")
                    continue
                if new_parent == target.get("id") or new_parent in descendants_map.get(target.get("id"), set()):
                    errors.append(f"{target.get('name')} は自身または子孫を親にできません")
                    continue
                if target.get("parent") != new_parent:
                    target["parent"] = new_parent
                    parent_updates += 1

            removed = delete_wbs_items(data, delete_targets) if delete_targets else 0

            if errors:
                st.error("\n".join(errors))

            if updates or parent_updates or removed:
                if not removed:
                    save_data(data)
                st.success(
                    "、".join(
                        part
                        for part in [
                            f"{updates}件の日付更新" if updates else "",
                            f"{parent_updates}件の階層更新" if parent_updates else "",
                            f"{removed}件のWBS削除" if removed else "",
                        ]
                        if part
                    )
                )
            else:
                st.info("変更はありませんでした")

    return edited_df


def render(data, filtered_data, filtered_wbs_map):

    render_structure_and_period_table(data, filtered_data.get("wbs", []))

    st.markdown("### タスク一覧")
    if not filtered_data.get("tasks"):
        st.info("タスクがまだありません。右のフォームから追加してください。")
        return

    counts = summarize_tasks_by_status(filtered_data["tasks"])
    st.write(" | ".join([f"{status}: {counts.get(status, 0)}件" for status in counts]))

    task_rows = []
    for task in filtered_data.get("tasks", []):
        task_rows.append(
            {
                "WBS": filtered_wbs_map.get(task.get("wbs_id"), WBSItem("-", "(未割当)", None, None, None, None, None)).name
                if task.get("wbs_id")
                else "(未割当)",
                "タイトル": task.get("title"),
                "ステータス": task.get("status"),
                "優先度": task.get("priority"),
                "期日": task.get("due"),
                "詳細": task.get("description"),
            }
        )

    st.dataframe(pd.DataFrame(task_rows))
