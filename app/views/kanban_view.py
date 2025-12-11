import streamlit as st

from components.kanban import render_kanban_columns
from components.models import WBSItem


def render(data, wbs_map):
    st.subheader("Kanban")
    render_kanban_columns(data.get("tasks", []), wbs_map)
