import streamlit as st

from app.components.models import WBSItem


def render(data, wbs_map: dict[str, WBSItem]):
    st.subheader("Presentation View")
    st.write("(整形されたWBSツリーをここに表示予定)")
