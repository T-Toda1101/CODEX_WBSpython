from datetime import date
from typing import Dict, Optional

import streamlit as st

from .models import STATUSES


def render_filters(data: Dict) -> Dict[str, Optional[str]]:
    st.markdown("### Project Filters")
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("表示開始日", value=date.today())
    with col2:
        end = st.date_input("表示終了日", value=date.today())

    status = st.selectbox(
        "ステータス", options=[None] + STATUSES, format_func=lambda x: "指定なし" if x is None else x
    )
    level = st.text_input("WBS階層", placeholder="例: 1-2 など")
    owner = st.text_input("担当者", placeholder="担当者名 (任意)")

    return {"start": start, "end": end, "status": status, "level": level, "owner": owner}
