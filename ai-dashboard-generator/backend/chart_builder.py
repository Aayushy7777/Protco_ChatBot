from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from file_processor import format_value


def build_charts(df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    charts: List[Dict[str, Any]] = []
    auto = profile.get("auto") or {}
    cat_col = auto.get("category_col")
    amt_col = auto.get("amount_col")
    status_col = auto.get("status_col")
    date_col = auto.get("date_col")
    prog_col = auto.get("progress_col") or auto.get("pct_col")

    # 1) Category vs amount (horizontal ranking)
    if cat_col in df.columns and amt_col in df.columns:
        g = df[[cat_col, amt_col]].copy()
        g[amt_col] = pd.to_numeric(g[amt_col], errors="coerce")
        g = g.dropna(subset=[cat_col, amt_col])
        s = g.groupby(cat_col)[amt_col].sum().sort_values(ascending=False).head(15)
        if len(s) > 0:
            top_name, top_val = str(s.index[0]), float(s.iloc[0])
            total = float(s.sum()) or 1.0
            charts.append(
                {
                    "id": "chart_1",
                    "type": "horizontalBar",
                    "title": f"{cat_col} by total {amt_col}",
                    "insight": f"{top_name} contributes {format_value(top_val)} ({(top_val/total)*100:.1f}% of top groups).",
                    "labels": [str(x) for x in s.index.tolist()],
                    "data": [round(float(x), 2) for x in s.values.tolist()],
                    "wide": True,
                }
            )

    # 2) Status distribution (doughnut)
    if status_col in df.columns:
        vc = df[status_col].astype(str).value_counts().head(8)
        if len(vc) > 0:
            charts.append(
                {
                    "id": "chart_2",
                    "type": "doughnut",
                    "title": f"{status_col} distribution",
                    "insight": f"Most frequent status is {vc.index[0]} with {int(vc.iloc[0])} records.",
                    "labels": [str(x) for x in vc.index.tolist()],
                    "data": [int(x) for x in vc.values.tolist()],
                    "wide": False,
                }
            )

    # 3) Category vs avg progress
    if cat_col in df.columns and prog_col in df.columns:
        g = df[[cat_col, prog_col]].copy()
        g[prog_col] = pd.to_numeric(g[prog_col], errors="coerce")
        g = g.dropna(subset=[cat_col, prog_col])
        s = g.groupby(cat_col)[prog_col].mean().sort_values(ascending=False)
        if len(s) > 0:
            max_v = float(profile.get("numeric", {}).get(prog_col, {}).get("max", 100))
            mult = 100.0 if max_v <= 1 else 1.0
            charts.append(
                {
                    "id": "chart_3",
                    "type": "bar",
                    "title": f"Average {prog_col} by {cat_col}",
                    "insight": f"{s.index[0]} leads at {float(s.iloc[0]) * mult:.1f} average progress.",
                    "labels": [str(x) for x in s.index.tolist()],
                    "data": [round(float(x) * mult, 2) for x in s.values.tolist()],
                    "wide": False,
                }
            )

    # 4) Trend over time
    if date_col in df.columns:
        d = df.copy()
        d["_date"] = pd.to_datetime(d[date_col], errors="coerce")
        d = d.dropna(subset=["_date"])
        if len(d) > 0:
            range_days = int((d["_date"].max() - d["_date"].min()).days)
            if range_days < 60:
                freq = "D"
                label_fmt = "%d %b"
            elif range_days < 365:
                freq = "ME"
                label_fmt = "%b %Y"
            else:
                freq = "QE"
                # Python strftime has no quarter token; compute quarter labels manually.
                label_fmt = None

            if amt_col in d.columns:
                d[amt_col] = pd.to_numeric(d[amt_col], errors="coerce")
                trend = d.set_index("_date")[amt_col].resample(freq).sum().dropna()
                y_title = amt_col
            else:
                trend = d.set_index("_date").resample(freq).size().astype(float)
                y_title = "Volume"

            if len(trend) > 0:
                charts.append(
                    {
                        "id": "chart_4",
                        "type": "line",
                        "title": f"{y_title} trend over time",
                        "insight": f"Timeline spans {range_days} days from {d['_date'].min().date()} to {d['_date'].max().date()}.",
                        "labels": [
                            (f"{ts.year}-Q{((int(ts.month) - 1) // 3) + 1}" if label_fmt is None else str(ts.strftime(label_fmt)))
                            for ts in trend.index
                        ],
                        "data": [round(float(v), 2) for v in trend.values.tolist()],
                        "wide": True,
                    }
                )

    # 5) Record count by category
    if cat_col in df.columns:
        vc = df[cat_col].astype(str).value_counts().head(12)
        if len(vc) > 0:
            charts.append(
                {
                    "id": "chart_5",
                    "type": "bar",
                    "title": f"Record count by {cat_col}",
                    "insight": f"{vc.index[0]} has the highest record count ({int(vc.iloc[0])}).",
                    "labels": [str(x) for x in vc.index.tolist()],
                    "data": [int(x) for x in vc.values.tolist()],
                    "wide": False,
                }
            )

    # 6) Name vs amount if available
    name_col = auto.get("name_col")
    if name_col in df.columns and amt_col in df.columns and len(charts) < 6:
        g = df[[name_col, amt_col]].copy()
        g[amt_col] = pd.to_numeric(g[amt_col], errors="coerce")
        g = g.dropna(subset=[name_col, amt_col])
        s = g.groupby(name_col)[amt_col].sum().sort_values(ascending=False).head(10)
        if len(s) > 0:
            charts.append(
                {
                    "id": "chart_6",
                    "type": "pie",
                    "title": f"Top {name_col} share by {amt_col}",
                    "insight": f"Top {name_col} contributes {format_value(float(s.iloc[0]))}.",
                    "labels": [str(x) for x in s.index.tolist()],
                    "data": [round(float(x), 2) for x in s.values.tolist()],
                    "wide": False,
                }
            )

    return charts[:6]


def build_kpis(df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, str]]:
    kpis: List[Dict[str, str]] = [{"label": "Total Records", "value": str(len(df)), "color": "blue"}]
    auto = profile.get("auto") or {}
    amount_col = auto.get("amount_col")
    status_col = auto.get("status_col")
    date_col = auto.get("date_col")

    if amount_col and amount_col in (profile.get("numeric") or {}):
        total = float(profile["numeric"][amount_col]["sum"])
        kpis.append({"label": f"Total {amount_col}", "value": format_value(total), "color": "green"})

    if status_col and status_col in df.columns:
        vc = df[status_col].astype(str).value_counts().head(3)
        for name, count in vc.items():
            kpis.append({"label": str(name), "value": str(int(count)), "color": "amber"})

    if date_col and date_col in (profile.get("dates") or {}):
        info = profile["dates"][date_col]
        start = pd.to_datetime(info["min"]).strftime("%b %Y")
        end = pd.to_datetime(info["max"]).strftime("%b %Y")
        kpis.append({"label": "Date Range", "value": f"{start} → {end}", "color": "purple"})

    return kpis[:6]
