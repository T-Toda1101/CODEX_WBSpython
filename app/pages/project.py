import streamlit as st

from components.data_store import build_wbs_map, ensure_data_file_exists, load_data
from views.filters_view import render_filters
from views.wbs_creation_view import wbs_creation_form
from views.task_form_view import render_task_form
from views import gantt_view, kanban_view, presentation_view, wbs_task_list


def render_project():
    st.title("Project Dashboard")
    st.caption("統合されたWBS・タスク管理ダッシュボード")

    ensure_data_file_exists()
    data = load_data()
    wbs_map = build_wbs_map(data.get("wbs", []))

    filter = render_filters(data)

    with st.sidebar:    
        wbs_creation_form(data, wbs_map)
        render_task_form(data, wbs_map)


    tab = st.radio(
        "表示するビューを選択",
        ["WBS & Task List", "Gantt", "Kanban", "Presentation"],
        horizontal=True
    )


    if tab == "WBS & Task List":
        wbs_task_list.render(data, wbs_map)
    if tab == "Gantt":
         gantt_view.render(data, wbs_map)
    if tab == "Kanban":
        kanban_view.render(data, wbs_map)   
    if tab == "Presentation":
        presentation_view.render(data, wbs_map)

if __name__ == "__main__":
    render_project()
