from typing import Dict, List

from .wbs_period_chart import render_period_chart
from .wbs_structure_table import render_structure_and_period_table


def wbs_structure_view(data: Dict[str, List[Dict]]):
    edited_df = render_structure_and_period_table(data)
    if edited_df is None:
        return

    render_period_chart(edited_df)
