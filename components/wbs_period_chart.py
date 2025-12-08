from datetime import date
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
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

    fig = go.Figure()

    if filtered_has_planned.any():
        planned_df = filtered_df[filtered_has_planned].copy()
        planned_df["duration"] = planned_df["end_date"] - planned_df["start_date"]
        fig.add_trace(
            go.Bar(
                x=planned_df["duration"],
                base=planned_df["start_date"],
                y=planned_df["display_name"],
                orientation="h",
                name="予定",
                marker_color="#4C78A8",
                customdata=planned_df[["end_date"]],
                hovertemplate=(
                    "<b>%{y}</b><br>開始予定: %{base|%Y-%m-%d}<br>終了予定: "
                    "%{customdata[0]|%Y-%m-%d}<extra></extra>"
                ),
            )
        )

    if filtered_has_actual.any():
        actual_df = filtered_df[filtered_has_actual].copy()
        first_actual = True
        for _, row in actual_df.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[row["actual_start_date"], row["actual_end_date"]],
                    y=[row["display_name"], row["display_name"]],
                    mode="lines+markers",
                    line=dict(color="#f28e2c", width=4),
                    marker=dict(color="#f28e2c", size=8),
                    name="実績",
                    showlegend=first_actual,
                    customdata=[[row["actual_start_date"], row["actual_end_date"]]] * 2,
                    hovertemplate=(
                        "<b>%{y}</b><br>実績開始: %{customdata[0]|%Y-%m-%d}<br>実績終了: "
                        "%{customdata[1]|%Y-%m-%d}<extra></extra>"
                    ),
                )
            )
            first_actual = False

    today = pd.to_datetime(date.today()).to_pydatetime()
    chart_start_dt = pd.to_datetime(chart_start).to_pydatetime()
    chart_end_dt = pd.to_datetime(chart_end).to_pydatetime()

    fig.add_vline(
        x=today,
        line_color="#d62728",
        line_dash="dash",
        annotation_text="今日",
        annotation_position="top left",
    )

    fig.update_layout(
        barmode="overlay",
        height=max(120, 40 * len(y_order)),
        xaxis_title="期間",
        yaxis_title="WBS (構造順)",
        xaxis_range=[chart_start_dt, chart_end_dt],
        legend_title="凡例",
    )
    fig.update_yaxes(categoryorder="array", categoryarray=y_order)

    st.markdown("#### 期間グラフ")
    st.plotly_chart(fig, use_container_width=True)
