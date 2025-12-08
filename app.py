import json
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(page_title="WBS & Kanban", layout="wide")

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "wbs_tasks.json"
STATUSES = ["Backlog", "In Progress", "Blocked", "Done"]


@dataclass
class WBSItem:
    id: str
    name: str
    parent: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]


@dataclass
class Task:
    id: str
    title: str
    status: str
    wbs_id: Optional[str]
    priority: str
    due: Optional[str]
    description: str


def load_data() -> Dict[str, List[Dict]]:
    if not DATA_FILE.exists():
        return {"wbs": [], "tasks": []}
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: Dict[str, List[Dict]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_wbs_map(items: List[Dict]) -> Dict[str, WBSItem]:
    return {
        item["id"]: WBSItem(
            id=item["id"],
            name=item["name"],
            parent=item.get("parent"),
            start_date=item.get("start_date"),
            end_date=item.get("end_date"),
        )
        for item in items
    }


def render_wbs_tree(wbs_items: List[Dict], parent: Optional[str] = None, level: int = 0):
    children = [item for item in wbs_items if item.get("parent") == parent]
    for child in children:
        indent = "  " * level
        st.markdown(f"{indent}• **{child['name']}**")
        render_wbs_tree(wbs_items, child["id"], level + 1)


def add_wbs_item(
    data: Dict[str, List[Dict]],
    name: str,
    parent: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
):
    data["wbs"].append(
        {
            "id": str(uuid.uuid4()),
            "name": name,
            "parent": parent,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }
    )
    save_data(data)
    st.success(f"WBS項目を追加しました: {name}")


def add_task(
    data: Dict[str, List[Dict]],
    title: str,
    wbs_id: Optional[str],
    priority: str,
    due_date: Optional[date],
    status: str,
    description: str,
):
    due_value = due_date.isoformat() if due_date else None
    data["tasks"].append(
        {
            "id": str(uuid.uuid4()),
            "title": title,
            "status": status,
            "wbs_id": wbs_id,
            "priority": priority,
            "due": due_value,
            "description": description,
        }
    )
    save_data(data)
    st.success(f"タスクを追加しました: {title}")


def update_task_status(data: Dict[str, List[Dict]], task_id: str, status: str):
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["status"] = status
            save_data(data)
            st.toast("ステータスを更新しました")
            break


def delete_task(data: Dict[str, List[Dict]], task_id: str):
    before = len(data["tasks"])
    data["tasks"] = [task for task in data["tasks"] if task["id"] != task_id]
    if len(data["tasks"]) < before:
        save_data(data)
        st.toast("タスクを削除しました", icon="⚠️")


def wbs_label(wbs_map: Dict[str, WBSItem], wbs_id: Optional[str]) -> str:
    if wbs_id is None:
        return "(未割当)"
    return wbs_map.get(
        wbs_id,
        WBSItem(
            id="-", name="削除済み", parent=None, start_date=None, end_date=None
        ),
    ).name


def sidebar_forms(data: Dict[str, List[Dict]], wbs_map: Dict[str, WBSItem]):
    st.sidebar.header("タスクの新規作成")
    with st.sidebar.form("create_task"):
        task_title = st.text_input("タスク名", placeholder="例: ユーザーヒアリング")
        selected_wbs = st.selectbox(
            "紐づくWBS",
            options=[None] + list(wbs_map.keys()),
            format_func=lambda x: "(未割当)" if x is None else wbs_map[x].name,
        )
        priority = st.selectbox("優先度", ["高", "中", "低"], index=1)
        use_due = st.checkbox("期日を設定する", value=False, key="use_due_date")
        due_input = (
            st.date_input("期日", value=date.today()) if use_due else None
        )
        status = st.selectbox("初期ステータス", STATUSES, index=0)
        description = st.text_area("詳細", height=100)
        if st.form_submit_button("タスクを追加") and task_title:
            add_task(data, task_title, selected_wbs, priority, due_input, status, description)



def kanban_view(data: Dict[str, List[Dict]], wbs_filter: Optional[str], wbs_map: Dict[str, WBSItem]):
    filtered_tasks = [
        task for task in data["tasks"] if (wbs_filter is None or task["wbs_id"] == wbs_filter)
    ]

    st.subheader("かんばんボード")
    columns = st.columns(len(STATUSES))

    for status, column in zip(STATUSES, columns):
        with column:
            st.markdown(f"### {status}")
            column_tasks = [t for t in filtered_tasks if t["status"] == status]
            if not column_tasks:
                st.caption("タスクなし")
            for task in column_tasks:
                with st.container(border=True):
                    st.markdown(f"**{task['title']}**")
                    st.caption(f"WBS: {wbs_label(wbs_map, task['wbs_id'])}")
                    meta = []
                    if task.get("priority"):
                        meta.append(f"優先度: {task['priority']}")
                    if task.get("due"):
                        meta.append(f"期日: {task['due']}")
                    if meta:
                        st.caption(" / ".join(meta))
                    if task.get("description"):
                        st.write(task["description"])

                    with st.form(f"update_{task['id']}"):
                        new_status = st.selectbox(
                            "ステータス変更",
                            STATUSES,
                            index=STATUSES.index(task["status"]),
                            key=f"select_{task['id']}",
                        )
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            submitted = st.form_submit_button("更新")
                        with col2:
                            removed = st.form_submit_button("削除", type="secondary")
                        if submitted and new_status != task["status"]:
                            update_task_status(data, task["id"], new_status)
                        if removed:
                            delete_task(data, task["id"])


def status_summary(tasks: List[Dict]):
    return {status: len([t for t in tasks if t["status"] == status]) for status in STATUSES}


def parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def flatten_wbs_with_levels(wbs_items: List[Dict]) -> List[Dict]:
    ordered: List[Dict] = []

    def walk(parent: Optional[str], level: int):
        children = [item for item in wbs_items if item.get("parent") == parent]
        for child in children:
            ordered.append({"item": child, "level": level})
            walk(child["id"], level + 1)

    walk(None, 0)
    return ordered


def normalize_date_value(value: Optional[object]) -> Optional[str]:
    """Convert mixed date inputs from data_editor rows to ISO strings."""

    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, str):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            return None

    return None


def wbs_structure_view(data: Dict[str, List[Dict]]):
    wbs_items = data.get("wbs", [])
    if not wbs_items:
        st.info("まだWBSがありません。下のフォームから追加してください。")
        return

    ordered_items = flatten_wbs_with_levels(wbs_items)
    rows = []
    for entry in ordered_items:
        item = entry["item"]
        level = entry["level"]
        start_val = parse_iso_date(item.get("start_date"))
        end_val = parse_iso_date(item.get("end_date"))
        rows.append(
            {
                "id": item["id"],
                "display_name": "　" * level + item["name"],
                "start_date": start_val,
                "end_date": end_val,
            }
        )

    wbs_df = pd.DataFrame(rows)

    st.markdown("### WBS構造と期間")

    with st.expander("構造順テーブル (開始/終了予定日の編集が可能)", expanded=True):
        edited_df = st.data_editor(
            wbs_df,
            hide_index=True,
            disabled=["id", "display_name"],
            column_config={
                "display_name": st.column_config.Column("WBS名 (インデントは階層を表します)"),
                "start_date": st.column_config.DateColumn("開始予定日"),
                "end_date": st.column_config.DateColumn("終了予定日"),
            },
            key="wbs_structure_editor",
        )

        if st.button("開始/終了予定日を保存", key="save_wbs_dates"):
            updates = 0
            for _, row in edited_df.iterrows():
                target = next((i for i in data["wbs"] if i["id"] == row["id"]), None)
                if not target:
                    continue
                new_start = normalize_date_value(row.get("start_date"))
                new_end = normalize_date_value(row.get("end_date"))
                if target.get("start_date") != new_start or target.get("end_date") != new_end:
                    target["start_date"] = new_start
                    target["end_date"] = new_end
                    updates += 1
            if updates:
                save_data(data)
                st.success(f"{updates}件のWBSの予定日を更新しました")
            else:
                st.info("変更はありませんでした")

    valid_dates_df = edited_df.dropna(subset=["start_date", "end_date"]).copy()
    if valid_dates_df.empty:
        st.info("開始・終了予定日が設定されたWBSがありません。予定日を入力してください。")
        return

    valid_dates_df["start_date"] = pd.to_datetime(valid_dates_df["start_date"])
    valid_dates_df["end_date"] = pd.to_datetime(valid_dates_df["end_date"])

    earliest_start = valid_dates_df["start_date"].min().date()
    latest_end = valid_dates_df["end_date"].max().date()

    col1, col2 = st.columns(2)
    with col1:
        chart_start = st.date_input("グラフ表示開始日", value=earliest_start)
    with col2:
        chart_end = st.date_input("グラフ表示終了日", value=latest_end)

    if chart_start > chart_end:
        st.error("表示期間の開始日は終了日より後にはできません")
        return

    filtered_df = valid_dates_df[
        (valid_dates_df["end_date"].dt.date >= chart_start)
        & (valid_dates_df["start_date"].dt.date <= chart_end)
    ].copy()

    filtered_df["start_date"] = pd.to_datetime(filtered_df["start_date"])
    filtered_df["end_date"] = pd.to_datetime(filtered_df["end_date"])

    y_order = filtered_df["display_name"].tolist()
    today_df = pd.DataFrame({"today": [pd.to_datetime(date.today())]})

    bar_chart = alt.Chart(filtered_df).mark_bar(size=14).encode(
        x=alt.X(
            "start_date:T",
            title="期間",
            scale=alt.Scale(
                domain=[pd.to_datetime(chart_start), pd.to_datetime(chart_end)]
            ),
        ),
        x2="end_date:T",
        y=alt.Y("display_name:N", sort=y_order, title="WBS (構造順)"),
        tooltip=["display_name", "start_date:T", "end_date:T"],
        color=alt.value("#4C78A8"),
    )

    today_rule = (
        alt.Chart(today_df)
        .mark_rule(color="#d62728", strokeDash=[6, 4])
        .encode(x="today:T")
    )

    chart = (
        (bar_chart + today_rule)
        .properties(height=max(120, 40 * len(y_order)))
        .configure_axis(grid=True)
    )

    st.markdown("#### 期間グラフ")
    st.altair_chart(chart, use_container_width=True)


def wbs_creation_form(data: Dict[str, List[Dict]], wbs_map: Dict[str, WBSItem]):
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


def main():
    st.title("WBSとタスク管理 (かんばん式)")
    st.caption("単独ユーザ向けの簡易WBS管理＆かんばんツール")

    data = load_data()
    wbs_map = build_wbs_map(data.get("wbs", []))

    sidebar_forms(data, wbs_map)

    wbs_tab, task_tab = st.tabs(["WBS管理", "タスク管理"])

    with wbs_tab:
        wbs_creation_form(data, wbs_map)
        wbs_structure_view(data)

    with task_tab:
        wbs_filter = st.selectbox(
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
