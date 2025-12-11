import streamlit as st


def two_pane_layout(left_ratio: int = 3, right_ratio: int = 1):
    return st.columns([left_ratio, right_ratio])
