from datetime import date
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_period_chart(wbs_df: pd.DataFrame) -> None:
    chart_df = wbs_df.copy()
    date_columns = ["start_date", "end_date", "actual_start_date", "actual_end_date"]
    for column in date_columns:
        chart_df[column] = pd.to_datetime(chart_df[column], errors="coerce").dt.date

    chart_df["actual_end_for_chart"] = chart_df["actual_end_date"]
    missing_actual_end = chart_df["actual_start_date"].notna() & chart_df["actual_end_date"].isna()
    chart_df.loc[missing_actual_end, "actual_end_for_chart"] = date.today()

    has_planned = chart_df["start_date"].notna() & chart_df["end_date"].notna()
    has_actual = chart_df["actual_start_date"].notna()

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
        latest_dates.append(chart_df.loc[has_actual, "actual_end_for_chart"].max())

    col1, col2 = st.columns(2)
    default_start: Optional[date] = min(earliest_dates)
    default_end: Optional[date] = max(latest_dates)
    with col1:
        chart_start = st.date_input("グラフ表示開始日", value=default_start)
    with col2:
        chart_end = st.date_input("グラフ表示終了日", value=default_end)

    if chart_start > chart_end:
        st.error("表示期間の開始日は終了日より後にはできません")
        return

    filtered_df = relevant_rows[
        (relevant_rows["end_date"].fillna(chart_start) >= chart_start)
        & (relevant_rows["start_date"].fillna(chart_end) <= chart_end)
    ].copy()

    filtered_has_planned = (
        filtered_df["start_date"].notna() & filtered_df["end_date"].notna()
    )
    filtered_has_actual = filtered_df["actual_start_date"].notna()

    y_order = filtered_df["display_name"].tolist()

    fig = go.Figure()

    if filtered_has_planned.any():
        planned_df = filtered_df[filtered_has_planned].copy()
        first_planned = True
        for _, row in planned_df.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[row["start_date"], row["end_date"]],
                    y=[row["display_name"], row["display_name"]],
                    mode="lines", 
                    line=dict(color="#4C78A8", width=50),
                    name="予定",
                    showlegend=first_planned,
                    customdata=[[row["start_date"], row["end_date"]]] * 2,
                    hovertemplate=(
                        "<b>%{y}</b><br>開始予定: %{customdata[0]|%Y-%m-%d}<br>終了予定: "
                        "%{customdata[1]|%Y-%m-%d}<extra></extra>"
                    ),
                )
            )
            first_planned = False

    if filtered_has_actual.any():
        actual_df = filtered_df[filtered_has_actual].copy()
        first_actual = True
        for _, row in actual_df.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[row["actual_start_date"], row["actual_end_for_chart"]],
                    y=[row["display_name"], row["display_name"]],
                    mode="lines+markers",
                    line=dict(color="#f28e2c", width=4),
                    marker=dict(color="#f28e2c", size=8),
                    name="実績",
                    showlegend=first_actual,
                    customdata=[[row["actual_start_date"], row["actual_end_for_chart"]]] * 2,
                    hovertemplate=(
                        "<b>%{y}</b><br>実績開始: %{customdata[0]|%Y-%m-%d}<br>実績終了: "
                        "%{customdata[1]|%Y-%m-%d}<extra></extra>"
                    ),
                )
            )
            first_actual = False
    today = date.today()
    chart_start_dt = chart_start
    chart_end_dt = chart_end
    fig.add_vline(
        x=today,
        line_color="#d62728",
        line_dash="dash"
    )
    fig.add_annotation(
        x=today,
        xref="x",
        y=1,          # グラフの一番上（yref="paper" と組み合わせ）
        yref="paper",
        text="今日",
        showarrow=False,
        xanchor="left",   # 線の少し右に出したければ "right" など調整可
    )


    chart_height = max(400, len(y_order) * 60)
    fig.update_layout(
        barmode="overlay",
        height=chart_height,
        xaxis_title="期間",
        yaxis_title="WBS (構造順)",
        xaxis_range=[chart_start_dt, chart_end_dt],
        legend_title="凡例",
    )

    fig.update_yaxes(categoryorder="array", categoryarray=y_order)
    fig.update_xaxes(tickformat="%y/%m")


    st.markdown("#### 期間グラフ")
    st.plotly_chart(fig, use_container_width=True)
