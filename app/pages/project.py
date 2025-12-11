import streamlit as st

from components.data_store import build_wbs_map, ensure_data_file_exists, load_data
from components.filtering import apply_filters
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

    filter_options = render_filters(data)
    filtered_data = apply_filters(data, filter_options)
    filtered_wbs_map = build_wbs_map(filtered_data.get("wbs", []))

    with st.sidebar:    
        wbs_creation_form(data, wbs_map)
        render_task_form(data, wbs_map)


    tab = st.radio(
        "表示するビューを選択",
        ["WBS & Task List", "Gantt", "Kanban", "Presentation"],
        horizontal=True
    )


    if tab == "WBS & Task List":
        wbs_task_list.render(data, filtered_data, filtered_wbs_map)
    if tab == "Gantt":
        gantt_view.render(filtered_data, filtered_wbs_map)
    if tab == "Kanban":
        kanban_view.render(filtered_data, filtered_wbs_map)
    if tab == "Presentation":
        presentation_view.render(filtered_data, filtered_wbs_map)

if __name__ == "__main__":
    render_project()
