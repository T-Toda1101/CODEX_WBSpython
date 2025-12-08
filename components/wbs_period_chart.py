from datetime import date
from typing import Optional

import altair as alt
import pandas as pd
import streamlit as st


def render_period_chart(wbs_df: pd.DataFrame) -> None:
    chart_df = wbs_df.copy()
    date_columns = ["start_date", "end_date", "actual_start_date", "actual_end_date"]
    for column in date_columns:
        chart_df[column] = pd.to_datetime(chart_df[column], errors="coerce")

    has_planned = chart_df["start_date"].notna() & chart_df["end_date"].notna()
    has_actual = chart_df["actual_start_date"].notna() & chart_df["actual_end_date"].notna()

    if not (has_planned.any() or has_actual.any()):
        st.info("開始・終了予定日または実績日が設定されたWBSがありません。日付を入力してください。")
        return

    relevant_rows = chart_df[has_planned | has_actual].copy()
    earliest_dates = []
    latest_dates = []
    if has_planned.any():
        earliest_dates.append(chart_df.loc[has_planned, "start_date"].min())
        latest_dates.append(chart_df.loc[has_planned, "end_date"].max())
    if has_actual.any():
        earliest_dates.append(chart_df.loc[has_actual, "actual_start_date"].min())
        latest_dates.append(chart_df.loc[has_actual, "actual_end_date"].max())

    col1, col2 = st.columns(2)
    default_start: Optional[date] = min(earliest_dates).date()
    default_end: Optional[date] = max(latest_dates).date()
    with col1:
        chart_start = st.date_input("グラフ表示開始日", value=default_start)
    with col2:
        chart_end = st.date_input("グラフ表示終了日", value=default_end)

    if chart_start > chart_end:
        st.error("表示期間の開始日は終了日より後にはできません")
        return

    filtered_df = relevant_rows[
        (relevant_rows["end_date"].dt.date.fillna(chart_start) >= chart_start)
        & (relevant_rows["start_date"].dt.date.fillna(chart_end) <= chart_end)
    ].copy()

    filtered_has_planned = (
        filtered_df["start_date"].notna() & filtered_df["end_date"].notna()
    )
    filtered_has_actual = (
        filtered_df["actual_start_date"].notna()
        & filtered_df["actual_end_date"].notna()
    )

    y_order = filtered_df["display_name"].tolist()
    today_df = pd.DataFrame({"today": [pd.to_datetime(date.today())]})

    layers = []
    if filtered_has_planned.any():
        planned_bars = (
            alt.Chart(filtered_df[filtered_has_planned])
            .mark_bar(size=14, color="#4C78A8")
            .encode(
                x=alt.X(
                    "start_date:T",
                    title="期間",
                    scale=alt.Scale(
                        domain=[pd.to_datetime(chart_start), pd.to_datetime(chart_end)]
                    ),
                    axis=alt.Axis(format="%Y-%m-%d", labelAngle=-45),
                ),
                x2="end_date:T",
                y=alt.Y("display_name:N", sort=y_order, title="WBS (構造順)"),
                tooltip=["display_name", "start_date:T", "end_date:T"],
            )
        )
        layers.append(planned_bars)

    if filtered_has_actual.any():
        actual_lines = (
            alt.Chart(filtered_df[filtered_has_actual])
            .mark_rule(color="#f28e2c", strokeWidth=3)
            .encode(
                x=alt.X("actual_start_date:T", title="期間"),
                x2="actual_end_date:T",
                y=alt.Y("display_name:N", sort=y_order, title="WBS (構造順)"),
                tooltip=[
                    "display_name",
                    alt.Tooltip("actual_start_date:T", title="実績開始"),
                    alt.Tooltip("actual_end_date:T", title="実績終了"),
                ],
            )
        )
        layers.append(actual_lines)

    today_rule = (
        alt.Chart(today_df)
        .mark_rule(color="#d62728", strokeDash=[6, 4])
        .encode(x="today:T")
    )
    layers.append(today_rule)

    chart = (
        alt.layer(*layers)
        .properties(height=max(120, 40 * len(y_order)))
        .configure_axis(grid=True)
    )

    st.markdown("#### 期間グラフ")
    st.altair_chart(chart, use_container_width=True)
