from datetime import date
from typing import Dict, Optional

import streamlit as st

from components.models import STATUSES


def render_filters(data: Dict) -> Dict[str, Optional[str]]:
    st.markdown("### Project Filters")
    col1,col2,col3,col4 = st.columns(4)
    with col1:
        start = st.date_input("表示開始日", value=date.today())
    with col2:
        end = st.date_input("表示終了日", value=date.today())
    with col3:
        status = st.selectbox(
            "ステータス", options=[None] + STATUSES, format_func=lambda x: "指定なし" if x is None else x
        )
    with col4:
        level = st.text_input("WBS階層", placeholder="例: 1-2 など")

    return {"start": start, "end": end, "status": status, "level": level}
