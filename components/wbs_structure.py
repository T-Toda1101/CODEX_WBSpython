from datetime import date
from typing import Dict, List, Optional

import altair as alt
import pandas as pd
import streamlit as st

from .data_store import save_data
from .models import WBSItem


def parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def flatten_wbs_with_levels(wbs_items: List[Dict]) -> List[Dict]:
    ordered: List[Dict] = []

    def walk(parent: Optional[str], level: int):
        children = [item for item in wbs_items if item.get("parent") == parent]
        for child in children:
            ordered.append({"item": child, "level": level})
            walk(child["id"], level + 1)

    walk(None, 0)
    return ordered


def normalize_date_value(value: Optional[object]) -> Optional[str]:
    """Convert mixed date inputs from data_editor rows to ISO strings."""

    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, str):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            return None

    return None


def wbs_structure_view(data: Dict[str, List[Dict]]):
    wbs_items = data.get("wbs", [])
    if not wbs_items:
        st.info("まだWBSがありません。下のフォームから追加してください。")
        return

    ordered_items = flatten_wbs_with_levels(wbs_items)
    rows = []
    for entry in ordered_items:
        item = entry["item"]
        level = entry["level"]
        rows.append(
            {
                "id": item["id"],
                "display_name": "　" * level + item["name"],
                "start_date": parse_iso_date(item.get("start_date")),
                "end_date": parse_iso_date(item.get("end_date")),
                "actual_start_date": parse_iso_date(item.get("actual_start_date")),
                "actual_end_date": parse_iso_date(item.get("actual_end_date")),
            }
        )

    wbs_df = pd.DataFrame(rows)

    st.markdown("### WBS構造と期間")

    with st.expander("構造順テーブル (予定・実績日を編集可能)", expanded=True):
        edited_df = st.data_editor(
            wbs_df,
            hide_index=True,
            disabled=["id", "display_name"],
            column_config={
                "display_name": st.column_config.Column("WBS名 (インデントは階層を表します)"),
                "start_date": st.column_config.DateColumn("開始予定日"),
                "end_date": st.column_config.DateColumn("終了予定日"),
                "actual_start_date": st.column_config.DateColumn("実績開始日"),
                "actual_end_date": st.column_config.DateColumn("実績終了日"),
            },
            key="wbs_structure_editor",
        )

        if st.button("予定・実績日を保存", key="save_wbs_dates"):
            updates = 0
            for _, row in edited_df.iterrows():
                target = next((i for i in data["wbs"] if i["id"] == row["id"]), None)
                if not target:
                    continue
                new_start = normalize_date_value(row.get("start_date"))
                new_end = normalize_date_value(row.get("end_date"))
                new_actual_start = normalize_date_value(row.get("actual_start_date"))
                new_actual_end = normalize_date_value(row.get("actual_end_date"))
                if (
                    target.get("start_date") != new_start
                    or target.get("end_date") != new_end
                    or target.get("actual_start_date") != new_actual_start
                    or target.get("actual_end_date") != new_actual_end
                ):
                    target["start_date"] = new_start
                    target["end_date"] = new_end
                    target["actual_start_date"] = new_actual_start
                    target["actual_end_date"] = new_actual_end
                    updates += 1
            if updates:
                save_data(data)
                st.success(f"{updates}件のWBSの日付を更新しました")
            else:
                st.info("変更はありませんでした")

    chart_df = edited_df.copy()
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
    default_start = min(earliest_dates).date()
    default_end = max(latest_dates).date()
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
