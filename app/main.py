import streamlit as st

from app.pages.project import render_project
from app.pages.settings import render_settings

st.set_page_config(page_title="WBS & Kanban", layout="wide")


def main():
    st.sidebar.title("Menu")
    page = st.sidebar.radio("Navigate", ["Project", "Settings"])

    if page == "Project":
        render_project()
    else:
        render_settings()


if __name__ == "__main__":
    main()
