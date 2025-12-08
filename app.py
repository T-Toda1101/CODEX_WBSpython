import json
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

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
            id=item["id"], name=item["name"], parent=item.get("parent")
        )
        for item in items
    }


def render_wbs_tree(wbs_items: List[Dict], parent: Optional[str] = None, level: int = 0):
    children = [item for item in wbs_items if item.get("parent") == parent]
    for child in children:
        indent = "  " * level
        st.markdown(f"{indent}• **{child['name']}**")
        render_wbs_tree(wbs_items, child["id"], level + 1)


def add_wbs_item(data: Dict[str, List[Dict]], name: str, parent: Optional[str]):
    data["wbs"].append({"id": str(uuid.uuid4()), "name": name, "parent": parent})
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
    return wbs_map.get(wbs_id, WBSItem(id="-", name="削除済み", parent=None)).name


def sidebar_forms(data: Dict[str, List[Dict]], wbs_map: Dict[str, WBSItem]):
    st.sidebar.header("新規作成")
    with st.sidebar.form("create_wbs"):
        wbs_name = st.text_input("WBS名", placeholder="例: フェーズA / 要件定義")
        parent_choice = st.selectbox(
            "親WBS",
            options=[None] + list(wbs_map.keys()),
            format_func=lambda x: "(トップレベル)" if x is None else wbs_map[x].name,
        )
        if st.form_submit_button("WBSを追加") and wbs_name:
            add_wbs_item(data, wbs_name, parent_choice)

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


def main():
    st.title("WBSとタスク管理 (かんばん式)")
    st.caption("単独ユーザ向けの簡易WBS管理＆かんばんツール")

    data = load_data()
    wbs_map = build_wbs_map(data.get("wbs", []))

    sidebar_forms(data, wbs_map)

    st.subheader("WBS構造")
    if data["wbs"]:
        render_wbs_tree(data["wbs"])
    else:
        st.info("まだWBSがありません。左のフォームから追加してください。")

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
