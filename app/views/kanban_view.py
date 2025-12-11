import streamlit as st

from components.kanban import format_wbs_label, group_tasks_by_status
from components.models import STATUSES


def render_task_card(task, wbs_map):
    """Render a single task card with metadata and description."""
    st.markdown(f"**{task.get('title', 'No Title')}**")
    st.caption(f"WBS: {format_wbs_label(wbs_map, task.get('wbs_id'))}")

    meta = []
    if task.get("priority"):
        meta.append(f"優先度: {task['priority']}")
    if task.get("due"):
        meta.append(f"期日: {task['due']}")
    if meta:
        st.caption(" / ".join(meta))

    if task.get("description"):
        st.write(task["description"])


def render_status_section(status, tasks, wbs_map):
    """Render a vertical section for a single status."""
    st.markdown(f"### {status}")
    if not tasks:
        st.caption("タスクなし")
        return

    for task in tasks:
        with st.container(border=True):
            render_task_card(task, wbs_map)


def render(data, wbs_map):
    st.subheader("かんばんボード")

    tasks = data.get("tasks", [])
    grouped_tasks = group_tasks_by_status(tasks)

    # 横並びではなく縦にステータスごとに表示する
    for status in STATUSES:
        render_status_section(status, grouped_tasks.get(status, []), wbs_map)
