from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from components.kanban import summarize_tasks_by_status
from components.data_store import delete_tasks, delete_wbs_items, save_data
from components.wbs_structure_table import (
    build_wbs_dataframe,
    collect_descendants,
    normalize_date_value,
    parse_iso_date,
)

SAVE_FEEDBACK_KEY = "wbs_save_feedback"
SAVE_ERROR_KEY = "wbs_save_errors"
TASK_SAVE_FEEDBACK_KEY = "task_save_feedback"
TASK_SAVE_ERROR_KEY = "task_save_errors"


def build_task_dataframe(tasks: List[Dict], wbs_display_map: Dict[Optional[str], str]) -> pd.DataFrame:
    rows = []
    for task in tasks:
        rows.append(
            {
                "id": task.get("id"),
                "title": task.get("title"),
                "wbs_selection": wbs_display_map.get(task.get("wbs_id"), wbs_display_map[None]),
                "status": task.get("status"),
                "priority": task.get("priority"),
                "due": parse_iso_date(task.get("due")),
                "description": task.get("description"),
                "delete": False,
            }
        )
    return pd.DataFrame(rows).set_index("id")


def render_structure_and_period_table(
    data: Dict[str, List[Dict]],
    wbs_items: List[Dict],
) -> Optional[pd.DataFrame]:
    """Display the WBS structure table and persist date updates."""

    if not wbs_items:
        st.info("まだWBSがありません。下のフォームから追加してください。")
        return None

    wbs_df = build_wbs_dataframe(wbs_items).set_index("id")

    st.markdown("### WBS構造と期間")

    with st.expander("構造順テーブル", expanded=True):
        parent_display_map = {None: "(トップレベル)"}
        for item in data.get("wbs", []):
            wbs_id = item.get("id")
            if not wbs_id:
                continue
            parent_display_map[wbs_id] = item.get('name')

        wbs_df["parent_selection"] = wbs_df["parent"].apply(
            lambda value: parent_display_map.get(value, parent_display_map[None])
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
                    required=True,
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
            rerun_needed = False
            success_message = ""
            errors = []
            id_to_item = {item.get("id"): item for item in data.get("wbs", [])}
            descendants_map = {
                item.get("id"): collect_descendants(data.get("wbs", []), item.get("id"))
                for item in data.get("wbs", [])
            }

            delete_targets = set(
                index for index, row in edited_df.iterrows() if bool(row.get("delete"))
            )

            for target_id in list(delete_targets):
                delete_targets.update(descendants_map.get(target_id, set()))

            for index, row in edited_df.iterrows():
                target = id_to_item.get(index)
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

            if updates or parent_updates or removed:
                if not removed:
                    save_data(data)
                success_message = "、".join(
                    part
                    for part in [
                        f"{updates}件の日付更新" if updates else "",
                        f"{parent_updates}件の階層更新" if parent_updates else "",
                        f"{removed}件のWBS削除" if removed else "",
                    ]
                    if part
                )
                rerun_needed = True

            if errors:
                if rerun_needed:
                    st.session_state[SAVE_ERROR_KEY] = errors
                else:
                    st.error("\n".join(errors))

            if rerun_needed:
                if success_message:
                    st.session_state[SAVE_FEEDBACK_KEY] = success_message
                st.rerun()
            elif not errors:
                st.info("変更はありませんでした")

    return edited_df


def render_task_table(data: Dict[str, List[Dict]], filtered_tasks: List[Dict]):
    st.markdown("### タスク一覧")
    if not filtered_tasks:
        st.info("タスクがまだありません。右のフォームから追加してください。")
        return

    counts = summarize_tasks_by_status(filtered_tasks)
    st.write(" | ".join([f"{status}: {counts.get(status, 0)}件" for status in counts]))

    wbs_display_map: Dict[Optional[str], str] = {None: "(未割当)"}
    for item in data.get("wbs", []):
        wbs_id = item.get("id")
        if not wbs_id:
            continue
        wbs_display_map[wbs_id] = item.get("name")

    task_df = build_task_dataframe(filtered_tasks, wbs_display_map)
    wbs_options = list(wbs_display_map.values())
    wbs_option_to_id = {name: wbs_id for wbs_id, name in wbs_display_map.items()}

    edited_tasks = st.data_editor(
        task_df,
        hide_index=True,
        column_config={
            "title": st.column_config.Column("タイトル", required=True),
            "wbs_selection": st.column_config.SelectboxColumn(
                "WBS",
                options=wbs_options,
                required=True,
            ),
            "status": st.column_config.Column("ステータス", disabled=True),
            "priority": st.column_config.Column("優先度", disabled=True),
            "due": st.column_config.DateColumn("期日"),
            "description": st.column_config.Column("詳細", disabled=True),
            "delete": st.column_config.CheckboxColumn("削除", default=False),
        },
        key="task_list_editor",
    )

    if st.button("変更を保存", key="save_task_updates"):
        id_to_task = {task.get("id"): task for task in data.get("tasks", [])}
        delete_targets = set(
            index for index, row in edited_tasks.iterrows() if bool(row.get("delete"))
        )
        updates = 0
        removed = 0
        errors = []

        for index, row in edited_tasks.iterrows():
            task = id_to_task.get(index)
            if not task or index in delete_targets:
                continue

            new_title = (row.get("title") or "").strip()
            if not new_title:
                errors.append("タイトルは空欄にできません")
                continue

            selection = row.get("wbs_selection")
            new_wbs = (
                wbs_option_to_id.get(selection) if not pd.isna(selection) else None
            )
            new_due = normalize_date_value(row.get("due"))

            if (
                task.get("title") != new_title
                or task.get("wbs_id") != new_wbs
                or task.get("due") != new_due
            ):
                task["title"] = new_title
                task["wbs_id"] = new_wbs
                task["due"] = new_due
                updates += 1

        if delete_targets:
            removed = delete_tasks(data, delete_targets)

        if updates and not removed:
            save_data(data)

        if updates or removed:
            success_message = "、".join(
                part
                for part in [
                    f"{updates}件のタスク更新" if updates else "",
                    f"{removed}件のタスク削除" if removed else "",
                ]
                if part
            )
            if errors:
                st.session_state[TASK_SAVE_ERROR_KEY] = errors
            if success_message:
                st.session_state[TASK_SAVE_FEEDBACK_KEY] = success_message
            st.rerun()

        if errors and not (updates or removed):
            st.error("\n".join(errors))
        elif not errors and not (updates or removed):
            st.info("変更はありませんでした")


def render(data, filtered_data, filtered_wbs_map):

    if errors := st.session_state.pop(SAVE_ERROR_KEY, None):
        st.error("\n".join(errors))
    if errors := st.session_state.pop(TASK_SAVE_ERROR_KEY, None):
        st.error("\n".join(errors))

    if feedback := st.session_state.pop(SAVE_FEEDBACK_KEY, None):
        st.success(feedback)
    if feedback := st.session_state.pop(TASK_SAVE_FEEDBACK_KEY, None):
        st.success(feedback)

    render_structure_and_period_table(data, filtered_data.get("wbs", []))

    render_task_table(data, filtered_data.get("tasks", []))
