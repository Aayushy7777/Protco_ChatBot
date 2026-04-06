from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from file_processor import format_number


def _first_numeric_col(profile: dict) -> str | None:
    numeric = profile.get("numeric", {}) or {}
    for c in numeric.keys():
        return c
    return None


def build_charts(df: pd.DataFrame, profile: dict) -> list:
    charts: List[Dict[str, Any]] = []
    auto = profile.get("auto", {}) or {}
    numeric = profile.get("numeric", {}) or {}
    categorical = profile.get("categorical", {}) or {}
    dates = profile.get("dates", {}) or {}

    category_col = auto.get("category_col")
    amount_col = auto.get("amount_col")
    date_col = auto.get("date_col")
    status_col = auto.get("status_col")

    # --- CHART 1: Category vs Amount/Days (vertical bar) ---
    if category_col and category_col in df.columns:
        value_col = amount_col if amount_col in df.columns else _first_numeric_col(profile)
        if value_col and value_col in df.columns and pd.api.types.is_numeric_dtype(df[value_col]):
            grouped = (
                df.groupby(category_col, dropna=False)[value_col]
                .sum(min_count=1)
                .sort_values(ascending=False)
                .reset_index()
            )
            grouped = grouped.dropna(subset=[value_col])
            if len(grouped) >= 2:
                top_item = str(grouped.iloc[0][category_col])
                top_val = float(grouped.iloc[0][value_col])
                total = float(grouped[value_col].sum())
                avg = total / max(1, len(grouped))
                pct_above = round((grouped[value_col] > avg).mean() * 100)
                insight = (
                    f"{top_item} leads with {format_number(top_val)} total {value_col.replace('_',' ')} — "
                    f"{pct_above}% of projects above average"
                )
                charts.append(
                    {
                        "id": "chart_cat_amount",
                        "type": "bar",
                        "title": f"Total {value_col.replace('_',' ')} per {category_col.replace('_',' ')}",
                        "insight": insight,
                        "x_key": category_col,
                        "y_key": value_col,
                        "data": grouped.to_dict(orient="records"),
                        "wide": False,
                    }
                )

    # --- CHART 2: Time trend (bar or line) ---
    if date_col and date_col in df.columns:
        date_series = pd.to_datetime(df[date_col], errors="coerce")
        if date_series.notna().any():
            range_days = int((date_series.max() - date_series.min()).days)
            if range_days < 60:
                freq = "W"
                label_fmt = "%b %d"
                freq_label = "week"
            elif range_days < 366:
                freq = "ME"
                label_fmt = "%b %Y"
                freq_label = "month"
            else:
                freq = "QE"
                label_fmt = "%Y-Q%q"
                freq_label = "quarter"

            df_temp = df.copy()
            df_temp["_date"] = date_series
            df_temp = df_temp.dropna(subset=["_date"])
            y_label = "count"
            if amount_col and amount_col in df_temp.columns and pd.api.types.is_numeric_dtype(df_temp[amount_col]):
                trend = df_temp.set_index("_date")[amount_col].resample(freq).sum().dropna()
                y_label = amount_col
            else:
                trend = df_temp.set_index("_date").resample(freq).size()

            data = []
            for ts, val in trend.items():
                try:
                    label = ts.strftime(label_fmt)
                except Exception:
                    label = str(ts)[:7]
                data.append({"period": label, y_label: round(float(val), 2)})

            if len(data) >= 2:
                peak = max(data, key=lambda x: float(x.get(y_label, 0)))
                insight = f"Peak in {peak['period']} with {format_number(peak[y_label])} — data spans {range_days} days"
                charts.append(
                    {
                        "id": "chart_trend",
                        "type": "bar",
                        "title": f"{'Tasks' if y_label=='count' else y_label.replace('_',' ').title()} started by {freq_label}",
                        "insight": insight,
                        "x_key": "period",
                        "y_key": y_label,
                        "data": data,
                        "wide": False,
                    }
                )

    # --- CHART 3: Status distribution (doughnut) ---
    if status_col and status_col in df.columns:
        counts = df[status_col].fillna("").astype(str).str.strip().value_counts().head(8)
        data = [{"name": str(k), "value": int(v)} for k, v in counts.items() if str(k)]
        if len(data) >= 2:
            top_status = data[0]["name"]
            top_count = data[0]["value"]
            total = len(df)
            insight = f"Most common: {top_status} ({top_count} of {total} records, {round(top_count/total*100,1)}%)"
            charts.append(
                {
                    "id": "chart_status",
                    "type": "doughnut",
                    "title": f"{status_col.replace('_',' ').title()} distribution",
                    "insight": insight,
                    "x_key": "name",
                    "y_key": "value",
                    "data": data,
                    "wide": False,
                }
            )

    # --- CHART 4: Average progress by category (bar) ---
    prog_col = auto.get("progress_col") or auto.get("pct_col")
    if category_col and prog_col and category_col in df.columns and prog_col in df.columns:
        if pd.api.types.is_numeric_dtype(df[prog_col]):
            multiplier = 100 if numeric.get(prog_col, {}).get("max", 1) <= 1.0 else 1
            grouped = (
                df.groupby(category_col, dropna=False)[prog_col]
                .mean()
                .apply(lambda x: round(float(x) * multiplier, 1))
                .sort_values(ascending=False)
                .reset_index()
            )
            grouped.columns = [category_col, "avg_progress"]
            if len(grouped) >= 2:
                top = grouped.iloc[0]
                low = grouped.iloc[-1]
                insight = (
                    f"{top[category_col]} leads at {top['avg_progress']}% — "
                    f"{low[category_col]} needs attention at {low['avg_progress']}%"
                )
                charts.append(
                    {
                        "id": "chart_progress",
                        "type": "bar",
                        "title": f"Average progress by {category_col.replace('_',' ')} (%)",
                        "insight": insight,
                        "x_key": category_col,
                        "y_key": "avg_progress",
                        "data": grouped.to_dict(orient="records"),
                        "wide": False,
                    }
                )

    # Only return charts with data
    out = []
    for c in charts:
        if isinstance(c.get("data"), list) and len(c["data"]) >= 2:
            out.append(c)
    return out

