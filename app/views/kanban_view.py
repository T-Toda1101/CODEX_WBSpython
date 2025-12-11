import streamlit as st

from components.kanban import wbs_label
from components.models import STATUSES


def render_kanban_columns(tasks, wbs_map):
    cols = st.columns(len(STATUSES))
    for col, status in zip(cols, STATUSES):
        col.write(f"### {status}")
        status_tasks = [t for t in tasks if t.get("status") == status]
        if not status_tasks:
            col.write("(カードを後で実装)")
            continue
        for task in status_tasks:
            with col.container(border=True):
                col.markdown(f"**{task.get('title', 'No Title')}**")
                col.caption(f"WBS: {wbs_label(wbs_map, task.get('wbs_id'))}")
                meta = []
                if task.get("priority"):
                    meta.append(f"優先度: {task['priority']}")
                if task.get("due"):
                    meta.append(f"期日: {task['due']}")
                if meta:
                    col.caption(" / ".join(meta))
                if task.get("description"):
                    col.write(task["description"])


def render(data, wbs_map):
    st.subheader("Kanban")
    render_kanban_columns(data.get("tasks", []), wbs_map)
