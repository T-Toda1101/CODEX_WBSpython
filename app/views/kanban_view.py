import streamlit as st

from app.components.kanban import render_kanban_columns
from app.components.models import WBSItem


def render(data, wbs_map: dict[str, WBSItem]):
    st.subheader("Kanban")
    render_kanban_columns(data.get("tasks", []), wbs_map)
