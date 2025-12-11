import streamlit as st

from components.data_store import build_wbs_map, ensure_data_file_exists, load_data
from components.filters import render_filters
from views import gantt_view, kanban_view, presentation_view, wbs_task_list


def render_project():
    st.title("Project Dashboard")
    st.caption("統合されたWBS・タスク管理ダッシュボード")

    ensure_data_file_exists()
    data = load_data()
    wbs_map = build_wbs_map(data.get("wbs", []))

    render_filters(data)

    tab1, tab2, tab3, tab4 = st.tabs(
        ["WBS & Task List", "Gantt", "Kanban", "Presentation"]
    )

    with tab1:
        wbs_task_list.render(data, wbs_map)
    with tab2:
        gantt_view.render(data, wbs_map)
    with tab3:
        kanban_view.render(data, wbs_map)
    with tab4:
        presentation_view.render(data, wbs_map)

if __name__ == "__main__":
    render_project()