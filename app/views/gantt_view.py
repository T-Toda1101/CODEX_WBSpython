from datetime import date
from typing import Dict, Optional, Tuple
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.wbs_structure_table import build_wbs_dataframe


def render_period_chart(filtered_wbs_df: pd.DataFrame) -> None:
    chart_df = filtered_wbs_df.copy()
    """
    ガントチャート描画用のメイン処理。

    WBS の予定日（start_date/end_date）および実績日（actual_start_date/actual_end_date）を元に
    表示範囲に含まれるデータだけを抽出し、Plotly で視覚化する。
    """

    # --------------------------------------
    # 1) 日付列の正規化（文字列→date型）
    # --------------------------------------

    date_columns = ["start_date", "end_date", "actual_start_date", "actual_end_date"]
    for column in date_columns:
        # to_datetime で正規化、エラーは NaT として扱う
        chart_df[column] = pd.to_datetime(chart_df[column], errors="coerce").dt.date

    # --------------------------------------
    # 2) 実績終了日が未入力の場合、"今日" を実績終了とみなして可視化
    # --------------------------------------
    chart_df["actual_end_for_chart"] = chart_df["actual_end_date"]
    missing_actual_end = chart_df["actual_start_date"].notna() & chart_df["actual_end_date"].isna()
    chart_df.loc[missing_actual_end, "actual_end_for_chart"] = date.today()

    # --------------------------------------
    # 3) 予定/実績の有無チェック
    # --------------------------------------
    has_planned = chart_df["start_date"].notna() & chart_df["end_date"].notna()
    has_actual = chart_df["actual_start_date"].notna()

    # どちらも無い場合は描画できない
    if not (has_planned.any() or has_actual.any()):
        st.info("開始・終了予定日または実績日が設定されたWBSがありません。日付を入力してください。")
        return

    # 可視化対象（予定 or 実績のどちらかをもつ行）
    relevant_rows = chart_df[has_planned | has_actual].copy()

    # --------------------------------------
    # 4) ガントチャート全体のデフォルト期間を決定
    # --------------------------------------
    earliest_dates = []
    latest_dates = []

    # 予定日から最も早い/遅い日
    if has_planned.any():
        earliest_dates.append(chart_df.loc[has_planned, "start_date"].min())
        latest_dates.append(chart_df.loc[has_planned, "end_date"].max())

    # 実績日から最も早い/遅い日
    if has_actual.any():
        earliest_dates.append(chart_df.loc[has_actual, "actual_start_date"].min())
        latest_dates.append(chart_df.loc[has_actual, "actual_end_for_chart"].max())

    if not earliest_dates or not latest_dates:
        st.info("ガントチャートを描画するための日付情報が不足しています。")
        return

    default_start: Optional[date] = min(earliest_dates)
    default_end: Optional[date] = max(latest_dates)

    filtered_df = relevant_rows
    filtered_has_planned = (
        filtered_df["start_date"].notna() & filtered_df["end_date"].notna()
    )

    filtered_has_actual = filtered_df["actual_start_date"].notna()

    # 表示順は WBS の構造順
    y_order = filtered_df["display_name"].tolist()

    fig = go.Figure()

    # --------------------------------------
    # 9) 予定バーの描画
    # --------------------------------------
    if filtered_has_planned.any():
        planned_df = filtered_df[filtered_has_planned].copy()

        # 凡例が重複するのを避けるためフラグを使う
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
                        "<b>%{y}</b><br>"
                        "開始予定: %{customdata[0]|%Y-%m-%d}<br>"
                        "終了予定: %{customdata[1]|%Y-%m-%d}"
                        "<extra></extra>"
                    ),
                )
            )
            first_planned = False

    # --------------------------------------
    # 10) 実績バーの描画
    # --------------------------------------
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
                        "<b>%{y}</b><br>"
                        "実績開始: %{customdata[0]|%Y-%m-%d}<br>"
                        "実績終了: %{customdata[1]|%Y-%m-%d}"
                        "<extra></extra>"
                    ),
                )
            )
            first_actual = False

    # --------------------------------------
    # 11) 今日の縦線（基準線）
    # --------------------------------------
    today = date.today()
    chart_start_dt = default_start
    chart_end_dt = default_end
    fig.add_vline(
        x=today,
        line_color="#d62728",
        line_dash="dash"  # 破線
    )
    fig.add_annotation(
        x=today,
        xref="x",
        y=1,
        yref="paper",
        text="今日",
        showarrow=False,
        xanchor="left"
    )

    # --------------------------------------
    # 12) レイアウト調整（高さ・軸フォーマット等）
    # --------------------------------------
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

    # --------------------------------------
    # 13) Streamlit に表示
    # --------------------------------------
    st.markdown("#### 期間グラフ")
    st.plotly_chart(fig, use_container_width=True)


def render(data, wbs_map):

    st.write("#### ガントチャート")

    # wbs データが存在する場合のみ描画
    if data.get("wbs"):
        render_period_chart(build_wbs_dataframe(data.get("wbs", [])))
