"""
csv_processor.py
----------------
Handles all CSV-side logic:
  - Parse uploaded files using pandas
  - Infer column types (numeric / categorical / datetime)
  - Compute per-column statistics
  - Build compact context strings for Ollama prompts
  - Apply filters, sorts, and aggregations
  - Generate chart data from aggregation results
"""

import io
import json
import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ── INR formatting utilities ──────────────────────────────────────────────────

def format_inr(value) -> str:
    """Format a numeric value as Indian currency (INR) with Cr/L/K suffixes."""
    try:
        n = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(n) >= 10_000_000:
        return f"₹{n/10_000_000:.2f}Cr"
    if abs(n) >= 100_000:
        return f"₹{n/100_000:.2f}L"
    if abs(n) >= 1_000:
        return f"₹{n/1_000:.1f}K"
    return f"₹{n:,.0f}"


def detect_quarter_from_filename(filename: str) -> str | None:
    """
    Detect quarter/fiscal-year label from filename.

    Supports:
      - Q1 – Q12   (e.g. q1.csv, Q3_data.xlsx)
      - FY25 – FY99 (e.g. fy25.csv, FY2026.xlsx)

    Returns the canonical label (e.g. 'Q3', 'FY25') or None.
    """
    name = filename.lower()

    # Q1 – Q12  (iterate high→low so 'q12' is checked before 'q1')
    for i in range(12, 0, -1):
        if f'q{i}' in name:
            return f'Q{i}'

    # FY25 – FY99  (high→low; check 4-digit form 'fy2025' before 2-digit 'fy25')
    for yr in range(99, 24, -1):
        if f'fy20{yr:02d}' in name:   # e.g. fy2025
            return f'FY{yr}'
        if f'fy{yr}' in name:          # e.g. fy25
            return f'FY{yr}'

    return None


def get_category_values(df: pd.DataFrame, col: str = 'partyCategory') -> list:
    """Return sorted unique values of the party/category column."""
    if col not in df.columns:
        col = next(
            (c for c in df.columns if 'party' in c.lower() or 'category' in c.lower()),
            None
        )
    if col is None:
        return []
    return sorted(df[col].dropna().unique().tolist())

def is_currency_col(col_name: str) -> bool:
    """Check if a column name suggests it contains currency values."""
    return bool(re.search(r'revenue|sales|amount|price|cost|income|profit|total|value', str(col_name), re.IGNORECASE))

def format_kpi_metrics(col_name: str, metrics: dict) -> dict:
    """
    Format raw KPI metrics from calculate_kpis into dashboard card format.
    
    Args:
        col_name: Column name for automatic unit detection
        metrics: Raw dict with {sum, avg, min, max, count, median}
    
    Returns:
        Card-friendly dict with {title, value, unit, trend}
    """
    is_currency = is_currency_col(col_name)
    
    # Choose primary display metric
    if "sum" in metrics and metrics["sum"] > 0:
        primary_value = metrics["sum"]
        display_metric = "sum"
    else:
        primary_value = metrics.get("avg", metrics.get("median", 0))
        display_metric = "avg"
    
    # Format value with currency or localization
    if is_currency:
        formatted_value = format_inr(primary_value)
        unit = ""
    else:
        formatted_value = f"{primary_value:,.2f}".rstrip('0').rstrip('.')
        unit = ""
    
    # Calculate trend (compare avg to median for variability indicator)
    trend = None
    if "avg" in metrics and "median" in metrics:
        avg, median = metrics["avg"], metrics["median"]
        if median != 0:
            trend = ((avg - median) / abs(median)) * 100
        else:
            trend = 0
    
    return {
        "title": col_name.replace("_", " ").title(),
        "value": formatted_value,
        "metric": display_metric,
        "unit": unit,
        "trend": round(trend, 1) if trend is not None else 0,
        "raw_value": primary_value,
        "count": metrics.get("count", 0),
        "is_currency": is_currency,
    }

# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class ColumnMeta:
    name: str
    dtype: str          # "numeric" | "categorical" | "datetime" | "text"
    nulls: int
    unique_count: int
    # numeric only
    min_val: float | None = None
    max_val: float | None = None
    mean_val: float | None = None
    sum_val: float | None = None
    std_val: float | None = None
    # categorical only
    top_values: list[str] = field(default_factory=list)


@dataclass
class CSVFile:
    name: str
    df: pd.DataFrame
    columns: list[ColumnMeta]
    row_count: int
    file_hash: str

    @property
    def numeric_cols(self) -> list[str]:
        return [c.name for c in self.columns if c.dtype == "numeric"]

    @property
    def categorical_cols(self) -> list[str]:
        return [c.name for c in self.columns if c.dtype == "categorical"]

    @property
    def datetime_cols(self) -> list[str]:
        return [c.name for c in self.columns if c.dtype == "datetime"]


# ── In-memory store keyed by file name ──────────────────────────────────────

_store: dict[str, CSVFile] = {}


def get_file(name: str) -> CSVFile | None:
    return _store.get(name)

def list_files() -> list[str]:
    return list(_store.keys())

def remove_file(name: str) -> None:
    _store.pop(name, None)

def clear_all() -> None:
    _store.clear()


# ── Parser ────────────────────────────────────────────────────────────────────

def parse_csv(filename: str, content: bytes) -> CSVFile:
    """
    Parse raw CSV, XLSX, or XLS bytes → CSVFile with full column metadata.
    For CSV: Tries multiple encodings and separators automatically.
    For XLSX: Uses pandas read_excel with openpyxl engine.
    For XLS: Uses pandas read_excel with xlrd engine.
    """
    file_hash = hashlib.md5(content).hexdigest()[:8]

    # Detect file type by extension
    is_xlsx = filename.lower().endswith('.xlsx')
    is_xls = filename.lower().endswith('.xls')

    if is_xlsx or is_xls:
        try:
            engine = 'openpyxl' if is_xlsx else 'xlrd'
            df = pd.read_excel(io.BytesIO(content), engine=engine, sheet_name=0)
        except Exception as e:
            raise ValueError(f"Could not parse Excel file: {str(e)}")
    else:
        # CSV: try multiple encodings
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=enc, low_memory=False)
                break
            except Exception:
                continue
        else:
            raise ValueError("Could not parse CSV with any supported encoding.")

    # strip whitespace from column names
    df.columns = [str(c).strip() for c in df.columns]

    # try to parse obvious datetime columns
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().head(20).astype(str)
            if sample.str.match(r"\d{4}[-/]\d{2}[-/]\d{2}").mean() > 0.7:
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                except Exception:
                    pass

    columns = [_build_column_meta(df, c) for c in df.columns]

    csv_file = CSVFile(
        name=filename,
        df=df,
        columns=columns,
        row_count=len(df),
        file_hash=file_hash,
    )
    _store[filename] = csv_file
    logger.info(f"Parsed {filename}: {len(df)} rows, {len(df.columns)} cols")
    return csv_file


def _build_column_meta(df: pd.DataFrame, col: str) -> ColumnMeta:
    series = df[col]
    nulls = int(series.isna().sum())
    unique_count = int(series.nunique())

    if pd.api.types.is_datetime64_any_dtype(series):
        return ColumnMeta(name=col, dtype="datetime", nulls=nulls, unique_count=unique_count)

    if pd.api.types.is_numeric_dtype(series):
        clean = series.dropna()
        return ColumnMeta(
            name=col, dtype="numeric", nulls=nulls, unique_count=unique_count,
            min_val=round(float(clean.min()), 4) if len(clean) else None,
            max_val=round(float(clean.max()), 4) if len(clean) else None,
            mean_val=round(float(clean.mean()), 4) if len(clean) else None,
            sum_val=round(float(clean.sum()), 4) if len(clean) else None,
            std_val=round(float(clean.std()), 4) if len(clean) else None,
        )

    # categorical / text
    top = series.value_counts().head(8).index.tolist()
    dtype = "categorical" if unique_count <= min(50, len(df) * 0.5) else "text"
    return ColumnMeta(
        name=col, dtype=dtype, nulls=nulls, unique_count=unique_count,
        top_values=[str(v) for v in top],
    )


# ── Context builder ───────────────────────────────────────────────────────────

def build_context(filename: str, max_sample_rows: int = 6) -> str:
    """
    Build a compact context string to inject into every Ollama prompt.
    Keeps token count low while giving the model enough to reason accurately.
    """
    f = get_file(filename)
    if not f:
        return ""

    lines = [
        f"FILE: {filename}",
        f"ROWS: {f.row_count:,}  |  COLS: {len(f.columns)}",
        "",
        "COLUMNS:",
    ]

    for c in f.columns:
        if c.dtype == "numeric":
            lines.append(
                f"  [{c.dtype}] {c.name} — "
                f"min={c.min_val}, max={c.max_val}, avg={c.mean_val}, sum={c.sum_val}"
            )
        elif c.dtype in ("categorical",):
            top_str = ", ".join(c.top_values[:6])
            lines.append(f"  [{c.dtype}] {c.name} — {c.unique_count} unique vals. Top: {top_str}")
        elif c.dtype == "datetime":
            mn = f.df[c.name].min()
            mx = f.df[c.name].max()
            lines.append(f"  [datetime] {c.name} — {mn} to {mx}")
        else:
            lines.append(f"  [text] {c.name}")

    # sample rows
    sample = f.df.head(max_sample_rows).to_dict(orient="records")
    # convert numpy types for JSON serialisation
    sample = _safe_json(sample)
    lines.append("")
    lines.append(f"SAMPLE ROWS (first {len(sample)}):")
    lines.append(json.dumps(sample, default=str))

    return "\n".join(lines)


def build_multi_context(filenames: list[str]) -> str:
    """Concatenate context for multiple files."""
    parts = [build_context(fn) for fn in filenames if get_file(fn)]
    return "\n\n---\n\n".join(parts)


def build_multi_file_context(filenames: list[str], active_file: str = "") -> str:
    """
    Build a combined context string for all loaded files with active file marked.
    
    Format:
    FILE: {name} (ACTIVE) | Rows: {len} | Cols: {list}
    Sample: {head(3).to_dict()}
    ---
    FILE: {name} | Rows: {len} | Cols: {list}
    Sample: {head(3).to_dict()}
    """
    if not filenames:
        return ""
    
    parts = []
    for fname in filenames:
        f = get_file(fname)
        if not f:
            continue
        
        # Mark active file
        active_marker = " (ACTIVE)" if fname == active_file else ""
        
        # Get col names and types
        col_info = ", ".join(f"{c.name}:{c.dtype}" for c in f.columns)
        
        # Get sample rows
        sample = f.df.head(3).to_dict(orient="records")
        sample = _safe_json(sample)
        sample_json = json.dumps(sample, default=str)
        
        # Build section
        section = (
            f"FILE: {fname}{active_marker} | Rows: {f.row_count} | Cols: {len(f.columns)}\n"
            f"Columns: {col_info}\n"
            f"Sample: {sample_json}"
        )
        parts.append(section)
    
    return "\n---\n".join(parts)


def _safe_json(obj: Any) -> Any:
    if isinstance(obj, list):
        return [_safe_json(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _safe_json(v) for k, v in obj.items()}
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return round(float(obj), 4)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    if pd.isna(obj) if not isinstance(obj, (list, dict)) else False:
        return None
    return str(obj) if hasattr(obj, '__class__') and 'timestamp' in str(type(obj)).lower() else obj


# ── Filter & sort ─────────────────────────────────────────────────────────────

def apply_filters(
    filename: str,
    filters: dict,          # {"column": {"op": "eq"|"gt"|"lt"|"contains", "value": ...}}
    sort_col: str | None = None,
    sort_asc: bool = True,
    limit: int = 500,
) -> tuple[list[dict], int]:
    """
    Apply filters + sort to a CSV file.
    Returns (rows_as_dicts, total_matching_count).
    """
    f = get_file(filename)
    if not f:
        return [], 0

    df = f.df.copy()

    for col, rule in filters.items():
        if col not in df.columns:
            continue
        op, val = rule.get("op", "eq"), rule.get("value")
        if val is None or val == "":
            continue
        try:
            if op == "eq":
                df = df[df[col].astype(str) == str(val)]
            elif op == "neq":
                df = df[df[col].astype(str) != str(val)]
            elif op == "contains":
                df = df[df[col].astype(str).str.contains(str(val), case=False, na=False)]
            elif op == "gt":
                df = df[pd.to_numeric(df[col], errors="coerce") > float(val)]
            elif op == "lt":
                df = df[pd.to_numeric(df[col], errors="coerce") < float(val)]
            elif op == "gte":
                df = df[pd.to_numeric(df[col], errors="coerce") >= float(val)]
            elif op == "lte":
                df = df[pd.to_numeric(df[col], errors="coerce") <= float(val)]
        except Exception as e:
            logger.warning(f"Filter error on {col}: {e}")

    total = len(df)

    if sort_col and sort_col in df.columns:
        df = df.sort_values(by=sort_col, ascending=sort_asc, na_position="last")

    rows = _safe_json(df.head(limit).to_dict(orient="records"))
    return rows, total


# ── Aggregation engine ────────────────────────────────────────────────────────

def aggregate(
    filename: str,
    group_col: str,
    value_col: str,
    agg_func: str = "sum",  # sum | avg | count | max | min
    top_n: int = 15,
) -> list[dict]:
    """
    Aggregate a numeric column by a categorical column.
    Used by the chart handler to compute data for bar/pie charts.
    """
    f = get_file(filename)
    if not f:
        return []

    df = f.df.dropna(subset=[group_col])

    if agg_func == "count":
        result = df.groupby(group_col).size().reset_index(name=value_col)
    elif agg_func == "sum":
        result = df.groupby(group_col)[value_col].sum().reset_index()
    elif agg_func == "avg":
        result = df.groupby(group_col)[value_col].mean().reset_index()
    elif agg_func == "max":
        result = df.groupby(group_col)[value_col].max().reset_index()
    elif agg_func == "min":
        result = df.groupby(group_col)[value_col].min().reset_index()
    else:
        result = df.groupby(group_col)[value_col].sum().reset_index()

    result = result.sort_values(by=value_col, ascending=False).head(top_n)
    # Round numeric columns only
    if pd.api.types.is_numeric_dtype(result[value_col]):
        result[value_col] = result[value_col].round(2)
    
    # Add formatted versions for currency columns
    for col in result.columns:
        if is_currency_col(col):
            result[col + "_formatted"] = result[col].apply(format_inr)
    
    return _safe_json(result.to_dict(orient="records"))


def time_series(
    filename: str,
    date_col: str,
    value_col: str,
    freq: str = "M",   # M=monthly, Q=quarterly, Y=yearly
    agg_func: str = "sum",
) -> list[dict]:
    """Resample a numeric column over a datetime column."""
    f = get_file(filename)
    if not f:
        return []

    df = f.df[[date_col, value_col]].copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna()
    df = df.set_index(date_col)

    resampled = getattr(df.resample(freq)[value_col], agg_func)()
    resampled = resampled.reset_index()
    resampled.columns = [date_col, value_col]
    resampled[date_col] = resampled[date_col].dt.strftime("%Y-%m")
    # Round numeric columns only
    if pd.api.types.is_numeric_dtype(resampled[value_col]):
        resampled[value_col] = resampled[value_col].round(2)
    return _safe_json(resampled.to_dict(orient="records"))


# ── Column name lookup lists ─────────────────────────────────────────────────

IGNORE_COLS   = {'hsn', 'hsncode', 'hsnsac', 'hsn_code', 'hsnorsac', 'slno', 'serialno'}
AMOUNT_COLS   = ['amount', 'finalamount', 'grandtotal', 'totalamount', 'netamount', 'total', 'value', 'price', 'sales', 'revenue']
FINAL_COLS    = ['finalamount', 'finalamt', 'grandtotal', 'totalat', 'nettotal', 'finaltotal']
PRETAX_COLS   = ['taxableamount', 'taxablevalue', 'pretaxamount', 'pretax', 'pricebeforetax', 'assessablevalue']
CATEGORY_COLS = ['partyname', 'customername', 'party', 'company', 'category', 'subcategory', 'product', 'region', 'state', 'dc']
DATE_COLS     = ['date', 'billdate', 'voucherdate', 'invoicedate', 'month', 'year']
COUNT_COLS    = ['voucherno', 'billno', 'invoiceno', 'orderno', 'invoice', 'id', 'invoicenumber']


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find first column matching any candidate name (case-insensitive, ignoring special chars)."""
    def _clean(s): return str(s).lower().replace(' ', '').replace('_', '').replace('-', '').replace('.', '')
    
    col_map = {_clean(c): c for c in df.columns}
    for cand in candidates:
        key = _clean(cand)
        if key in col_map:
            return col_map[key]
    return None


def auto_dashboard_config(
    df_or_filename,
    filters: dict = None,
    quarter: str = None,
    category: str = None,
    filename: str = '',
) -> dict:
    """
    Generate a dashboard config (4 KPIs + 6 charts) from a DataFrame or stored filename.

    Accepts either:
      - auto_dashboard_config('file.csv')          → legacy filename-based call
      - auto_dashboard_config(df, quarter='Q1')    → new DataFrame-based call
    """
    # ── Resolve DataFrame ─────────────────────────────────────────────────
    if isinstance(df_or_filename, str):
        # Legacy call: df_or_filename is a filename string
        f = get_file(df_or_filename)
        if not f:
            return {"kpi_cards": [], "charts": [], "column_info": {}}
        df = f.df.copy()
        if not filename:
            filename = df_or_filename
    else:
        # New call: df_or_filename is already a DataFrame
        df = df_or_filename.copy()

    # ── Drop ignored columns (HSN etc.) ──────────────────────────────────
    drop_cols = [c for c in df.columns if c.lower().replace('_', '').replace(' ', '') in IGNORE_COLS]
    df = df.drop(columns=drop_cols, errors='ignore')

    # ── Locate canonical columns ──────────────────────────────────────────
    amount_col    = _find_col(df, AMOUNT_COLS)
    final_col     = _find_col(df, FINAL_COLS) or amount_col
    pretax_col    = _find_col(df, PRETAX_COLS)
    party_col     = _find_col(df, CATEGORY_COLS)
    date_col      = _find_col(df, DATE_COLS)
    invoice_col   = _find_col(df, COUNT_COLS)

    # ── Apply category filter ─────────────────────────────────────────────
    if category and category != 'All' and party_col and party_col in df.columns:
        df = df[df[party_col].astype(str) == str(category)]

    # ── Apply legacy dict filters ─────────────────────────────────────────
    if filters:
        for col, rule in filters.items():
            if col not in df.columns:
                continue
            if isinstance(rule, dict):
                op, val = rule.get('op', 'eq'), rule.get('value')
                if val is None or val == '':
                    continue
                try:
                    if op == 'eq':       df = df[df[col].astype(str) == str(val)]
                    elif op == 'neq':    df = df[df[col].astype(str) != str(val)]
                    elif op == 'contains': df = df[df[col].astype(str).str.contains(str(val), case=False, na=False)]
                    elif op == 'gt':     df = df[pd.to_numeric(df[col], errors='coerce') > float(val)]
                    elif op == 'lt':     df = df[pd.to_numeric(df[col], errors='coerce') < float(val)]
                    elif op == 'gte':    df = df[pd.to_numeric(df[col], errors='coerce') >= float(val)]
                    elif op == 'lte':    df = df[pd.to_numeric(df[col], errors='coerce') <= float(val)]
                except Exception:
                    pass
            else:
                df = df[df[col].astype(str) == str(rule)]

    # ── KPI Cards (exactly 4) ────────────────────────────────────────────
    kpi_cards = []

    def _kpi(title: str, raw_value: float, is_currency: bool) -> dict:
        return {
            'title': title,
            'value': format_inr(raw_value) if is_currency else int(raw_value),
            'raw_value': raw_value,
            'is_currency': is_currency,
            'trend': 0,
            'metric': 'sum' if is_currency else 'count',
        }

    if amount_col and amount_col in df.columns:
        kpi_cards.append(_kpi('Total Amount', pd.to_numeric(df[amount_col], errors='coerce').sum(), True))
        kpi_cards.append(_kpi('Average Amount', pd.to_numeric(df[amount_col], errors='coerce').mean(), True))
    if final_col and final_col in df.columns and final_col != amount_col:
        kpi_cards.append(_kpi('Total Final Amount', pd.to_numeric(df[final_col], errors='coerce').sum(), True))
    elif final_col and final_col in df.columns:
        # If same col, still show it as Final Amount with that label
        kpi_cards.append(_kpi('Total Final Amount', pd.to_numeric(df[final_col], errors='coerce').sum(), True))
    if pretax_col and pretax_col in df.columns:
        kpi_cards.append(_kpi('Total Pre-Tax Amount', pd.to_numeric(df[pretax_col], errors='coerce').sum(), True))

    # Pad / trim to exactly 4
    kpi_cards = kpi_cards[:4]

    # ── Helper: aggregate and return chart-ready records ─────────────────
    def _agg(group_col: str, value_col: str, limit: int = 10) -> list[dict]:
        if not group_col or not value_col:
            return []
        if group_col not in df.columns or value_col not in df.columns:
            return []
        try:
            res = (
                df.groupby(group_col)[value_col]
                .sum()
                .reset_index()
                .sort_values(by=value_col, ascending=False)
                .head(limit)
            )
            res[value_col] = pd.to_numeric(res[value_col], errors='coerce').round(2)
            return _safe_json(res.to_dict(orient='records'))
        except Exception as e:
            logger.warning(f'_agg failed ({group_col},{value_col}): {e}')
            return []

    def _make_chart(idx, ctype, title, x_col, y_col, limit=10):
        data = _agg(x_col, y_col, limit)
        if not data:
            return
        charts.append({
            'id': f'auto_chart_{idx}_{x_col}_{y_col}',
            'type': ctype,
            'title': title,
            'xKey': x_col,
            'yKey': y_col,
            'data': data,
        })

    charts = []

    # Chart 1 — Top Companies by Amount
    if party_col and amount_col:
        _make_chart(1, 'bar_horizontal', 'Top Companies by Amount', party_col, amount_col, 10)
    elif amount_col:
        # Fallback to index if no party column found
        df['_index'] = [f"Row {i+1}" for i in range(len(df))]
        _make_chart(1, 'bar_horizontal', 'Sales by Record', '_index', amount_col, 10)

    # Chart 2 — Amount Distribution
    if party_col and amount_col:
        _make_chart(2, 'pie', 'Amount Distribution by Party', party_col, amount_col, 8)
    elif amount_col:
        _make_chart(2, 'pie', 'Total Amount Breakdown', None, amount_col, 1) # simple sum if possible

    # Chart 3 — Monthly or Category trend
    if date_col and amount_col:
        try:
            temp = df[[date_col, amount_col]].copy()
            temp[date_col] = pd.to_datetime(temp[date_col], errors='coerce')
            temp = temp.dropna().set_index(date_col)
            res = temp.resample('M')[amount_col].sum().reset_index()
            res.columns = [date_col, amount_col]
            res[date_col] = res[date_col].dt.strftime('%Y-%m')
            data3 = _safe_json(res.tail(12).to_dict(orient='records'))
            if data3:
                charts.append({
                    'id': f'auto_chart_3_{date_col}_{amount_col}',
                    'type': 'bar',
                    'title': 'Monthly Sales Trend',
                    'xKey': date_col,
                    'yKey': amount_col,
                    'data': data3,
                })
        except Exception as e:
            logger.warning(f'Chart 3 time-series failed: {e}')
            if party_col and pretax_col:
                _make_chart(3, 'bar', 'Pre-Tax Amount by Company', party_col, pretax_col, 8)
    elif party_col and (pretax_col or amount_col):
        _make_chart(3, 'bar', 'Pre-Tax Amount by Company', party_col, pretax_col or amount_col, 8)

    # Chart 4 — Top Companies by Amount (Detail)
    if party_col and amount_col:
        _make_chart(4, 'bar_colored', 'Top Companies by Amount (Detail)', party_col, amount_col, 10)

    # Chart 5 — Pre-Tax vs Tax Breakdown (2-segment donut)
    if pretax_col and amount_col and pretax_col in df.columns and amount_col in df.columns:
        try:
            total_amount = float(pd.to_numeric(df[amount_col], errors='coerce').sum())
            total_pretax = float(pd.to_numeric(df[pretax_col], errors='coerce').sum())
            tax_amount   = max(total_amount - total_pretax, 0)
            charts.append({
                'id': 'auto_chart_5_pretax_vs_tax',
                'type': 'pie',
                'title': 'Pre-Tax vs Tax Breakdown',
                'xKey': 'label',
                'yKey': 'value',
                'data': [
                    {'label': 'Pre-Tax Amount', 'value': round(total_pretax, 2)},
                    {'label': 'Tax Amount',     'value': round(tax_amount, 2)},
                ],
            })
        except Exception as e:
            logger.warning(f'Chart 5 pretax/tax breakdown failed: {e}')

    # Chart 6 — Final Amount by Company (horizontal colored bars)
    if party_col and final_col:
        _make_chart(6, 'bar_horizontal_colored', 'Final Amount by Company', party_col, final_col, 8)
    elif party_col and amount_col:
        _make_chart(6, 'bar_horizontal_colored', 'Total Amount by Company', party_col, amount_col, 8)

    # ── Summary metadata ─────────────────────────────────────────────────
    top_company = ''
    top_amount  = ''
    total_revenue = ''
    invoice_count = len(df)

    if party_col and amount_col and party_col in df.columns and amount_col in df.columns:
        try:
            grp = df.groupby(party_col)[amount_col].sum()
            top_company = str(grp.idxmax())
            top_amount  = format_inr(grp.max())
            total_revenue = format_inr(df[amount_col].sum())
        except Exception:
            pass

    if invoice_col and invoice_col in df.columns:
        invoice_count = int(df[invoice_col].nunique())

    cat_values = get_category_values(df, party_col) if party_col else []

    return {
        'kpi_cards':        kpi_cards,
        'charts':           charts,
        'column_info': {
            'first_categorical': party_col,
            'has_date': bool(date_col),
        },
        'category_column':  party_col,
        'category_values':  cat_values,
        'active_category':  category or 'All',
        'quarter':          quarter,
        'row_count':        len(df),
        'top_company':      top_company,
        'top_amount':       top_amount,
        'total_revenue':    total_revenue,
        'invoice_count':    invoice_count,
    }


# ── AI Chart Selection Engine ────────────────────────────────────────────────

def ai_select_charts(df: pd.DataFrame, filename: str = "", quarter: str = "All", category: str = "All") -> list[dict]:
    """
    Intelligently analyze DataFrame and auto-select the BEST 5-6 chart types for analysis.
    Returns only essential charts sorted by business relevance.
    
    Focus: Bar, Line, Pie/Donut, Scatter, and Pareto charts only.
    Excludes: HSN, HSnCode, detailed transaction data.
    """
    charts = []
    priority = 1
    
    # STEP 1: Analyze DataFrame structure
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    category_cols = [c for c in df.columns if c in df.select_dtypes(include='object').columns]
    date_cols = [c for c in df.columns if any(k in c.lower() 
                 for k in ['date','month','year','day','week','quarter','time'])]
    currency_cols = [c for c in numeric_cols if any(k in c.lower() 
                     for k in ['amount','revenue','sales','price','cost','profit',
                               'value','total','final','pretax'])]
    count_cols = [c for c in df.columns if any(k in c.lower() 
                  for k in ['count','qty','quantity','units','volume'])]
    party_col = next((c for c in category_cols if any(k in c.lower()
                 for k in ['party','company','vendor','customer','client','name','supplier'])), 
                 category_cols[0] if category_cols else None)
    
    # EXCLUDE: HSN, HSnCode, Pincode, ZIP, PAN, GSTIN, UUID, GUID, Code columns
    ignore_cols = {c for c in df.columns if any(k in c.lower()
                   for k in ['hsn','hsncode','pincode','zip','pan','gstin','uuid','guid','code'])}
    
    # Filter out ignored columns from analysis
    numeric_cols = [c for c in numeric_cols if c not in ignore_cols]
    category_cols = [c for c in category_cols if c not in ignore_cols]
    
    # STEP 2: Apply ESSENTIAL selection rules (limit to 5-6 charts)
    
    # RULE 1: Currency + Party exist → BAR CHART (Top performers)
    if currency_cols and party_col and party_col not in ignore_cols:
        primary_currency = currency_cols[0]
        
        # Bar horizontal: Top 10 parties by primary currency
        charts.append({
            'id': f'bar_horizontal_top_{priority}',
            'chartType': 'BAR_HORIZONTAL',
            'title': f'Top 10 {party_col} by {primary_currency}',
            'x_col': party_col,
            'y_col': primary_currency,
            'z_col': None,
            'series_col': None,
            'aggregation': 'sum',
            'limit': 10,
            'orientation': 'horizontal',
            'multi_color': True,
            'business_insight': f'Identifies top-performing {party_col.lower()} by {primary_currency.lower()}.',
            'priority': priority,
        })
        priority += 1
        
        # RULE 2: Donut Chart → Distribution
        if df[party_col].nunique() <= 12:
            charts.append({
                'id': f'donut_dist_{priority}',
                'chartType': 'DONUT',
                'title': f'{primary_currency} Distribution by {party_col}',
                'x_col': party_col,
                'y_col': primary_currency,
                'z_col': None,
                'series_col': None,
                'aggregation': 'sum',
                'limit': 8,
                'orientation': 'vertical',
                'multi_color': True,
                'business_insight': f'Pie chart showing revenue proportion by {party_col.lower()}. Larger slices = higher value.',
                'priority': priority,
            })
            priority += 1
        
        # RULE 3: Pareto Chart → 80/20 Analysis
        if len(df) > 10:
            charts.append({
                'id': f'pareto_80_{priority}',
                'chartType': 'PARETO',
                'title': f'Pareto: {party_col} Contribution',
                'x_col': party_col,
                'y_col': primary_currency,
                'z_col': None,
                'series_col': None,
                'aggregation': 'sum',
                'limit': 15,
                'orientation': 'vertical',
                'multi_color': False,
                'business_insight': 'Pareto principle: Identifies which companies generate 80% of revenue.',
                'priority': priority,
            })
            priority += 1
    
    # RULE 4: Date + Currency exist → LINE CHART (Trends)
    if date_cols and currency_cols and priority <= 4:
        primary_currency = currency_cols[0]
        date_col = date_cols[0]
        charts.append({
            'id': f'line_area_trend_{priority}',
            'chartType': 'LINE_AREA',
            'title': f'{primary_currency} Trend Over Time',
            'x_col': date_col,
            'y_col': primary_currency,
            'z_col': None,
            'series_col': None,
            'aggregation': 'sum',
            'limit': 100,
            'orientation': 'vertical',
            'multi_color': False,
            'business_insight': f'Shows the trend of {primary_currency.lower()} over time with area visualization.',
            'priority': priority,
        })
        priority += 1
    
    # RULE 5: Multiple currency columns → SCATTER CHART (Correlation)
    if len(currency_cols) >= 2 and len(df) > 20 and priority <= 5:
        col1, col2 = currency_cols[0], currency_cols[1]
        charts.append({
            'id': f'scatter_corr_{priority}',
            'chartType': 'SCATTER',
            'title': f'{col1} vs {col2} Correlation',
            'x_col': col1,
            'y_col': col2,
            'z_col': None,
            'series_col': None,
            'aggregation': 'sum',
            'limit': 200,
            'orientation': 'vertical',
            'multi_color': False,
            'business_insight': f'Reveals correlation pattern between {col1.lower()} and {col2.lower()}.',
            'priority': priority,
        })
        priority += 1
    
    # LIMIT: Return only 5-6 charts maximum
    charts = sorted(charts, key=lambda c: c['priority'])[:6]
    
    return charts


# ── Chart Data Preparation Engine ────────────────────────────────────────────

def prepare_chart_data(df: pd.DataFrame, config: dict) -> dict:
    """
    Prepare data for a specific chart type based on config.
    Returns backend data structure ready for frontend ECharts rendering.
    """
    chart_type = config.get('chartType', '')
    x_col = config.get('x_col')
    y_col = config.get('y_col')
    z_col = config.get('z_col')
    series_col = config.get('series_col')
    agg = config.get('aggregation', 'sum')
    limit = config.get('limit', 10)
    
    # Validate columns exist
    for col in [x_col, y_col, z_col, series_col]:
        if col and col not in df.columns:
            col = None
    
    try:
        # Simple bar/line/pie charts
        if chart_type in ['BAR_VERTICAL','BAR_HORIZONTAL','LINE','LINE_SMOOTH','LINE_AREA','DONUT','PIE','FUNNEL','TREEMAP']:
            if not x_col or not y_col:
                return {'labels': [], 'values': []}
            
            grouped = df.groupby(x_col)[y_col].agg(agg).reset_index()
            grouped = grouped.nlargest(limit, y_col)
            
            return {
                'labels': [str(v)[:25] for v in grouped[x_col].tolist()],
                'values': grouped[y_col].round(2).tolist()
            }
        
        # Stacked/grouped bars
        elif chart_type in ['BAR_STACKED','BAR_GROUPED','LINE_AREA_STACKED']:
            if not x_col or not y_col or not series_col:
                return {'labels': [], 'series': []}
            
            if series_col not in df.columns:
                return {'labels': [], 'series': []}
            
            top_series = df[series_col].value_counts().head(5).index.tolist()
            df_filtered = df[df[series_col].isin(top_series)]
            
            try:
                pivot = df_filtered.pivot_table(
                    index=x_col, columns=series_col,
                    values=y_col, aggfunc=agg, fill_value=0
                )
                top_x = df.groupby(x_col)[y_col].sum().nlargest(limit).index
                pivot = pivot.loc[pivot.index.isin(top_x)]
                
                return {
                    'labels': [str(v)[:20] for v in pivot.index.tolist()],
                    'series': [
                        {'name': str(col), 'values': pivot[col].round(2).tolist()}
                        for col in pivot.columns
                    ]
                }
            except:
                return {'labels': [], 'series': []}
        
        # Scatter
        elif chart_type == 'SCATTER':
            if not x_col or not y_col:
                return {'data': []}
            sample = df[[x_col, y_col]].dropna().head(200)
            return {
                'data': sample.values.tolist(),
                'x_label': str(x_col),
                'y_label': str(y_col)
            }
        
        # Bubble
        elif chart_type == 'BUBBLE':
            if not x_col or not y_col or not z_col:
                return {'data': []}
            sample = df[[x_col, y_col, z_col]].dropna().head(100)
            return {
                'data': [list(row) for row in sample.values.tolist()]
            }
        
        # Heatmap
        elif chart_type == 'HEATMAP':
            if not x_col or not series_col or not y_col:
                return {'data': [], 'x_labels': [], 'y_labels': []}
            
            try:
                pivot = df.pivot_table(
                    index=x_col, columns=series_col,
                    values=y_col, aggfunc=agg, fill_value=0
                )
                pivot = pivot.iloc[:15, :10]
                heatmap_data = [
                    [j, i, float(pivot.iloc[i, j])]
                    for i in range(len(pivot.index))
                    for j in range(len(pivot.columns))
                ]
                return {
                    'data': heatmap_data,
                    'x_labels': [str(c)[:15] for c in pivot.columns.tolist()],
                    'y_labels': [str(c)[:15] for c in pivot.index.tolist()],
                    'min': float(pivot.min().min()) if len(heatmap_data) > 0 else 0,
                    'max': float(pivot.max().max()) if len(heatmap_data) > 0 else 1
                }
            except:
                return {'data': [], 'x_labels': [], 'y_labels': []}
        
        # Waterfall
        elif chart_type == 'WATERFALL':
            if not x_col or not y_col:
                return {'labels': [], 'data': []}
            
            grouped = df.groupby(x_col)[y_col].agg(agg).reset_index().sort_values(x_col)
            values = grouped[y_col].tolist()
            waterfall = []
            running = 0
            for i, val in enumerate(values):
                delta = val - (values[i-1] if i > 0 else 0)
                waterfall.append({'base': running, 'delta': delta, 'total': val})
                running = val
            
            return {
                'labels': [str(v)[:20] for v in grouped[x_col].tolist()],
                'data': waterfall
            }
        
        # Gauge
        elif chart_type == 'GAUGE':
            if not y_col:
                return {'value': 0, 'label': 'N/A', 'actual': '0', 'target': '0'}
            
            total = float(pd.to_numeric(df[y_col], errors='coerce').sum())
            target = total * 1.2
            pct = min(100, round((total / target * 100), 1)) if target > 0 else 0
            
            return {
                'value': pct,
                'label': 'vs Target',
                'actual': format_inr(total),
                'target': format_inr(target)
            }
        
        # Radar
        elif chart_type == 'RADAR':
            if not x_col:
                return {'indicators': [], 'series': []}
            
            numeric_cols_list = df.select_dtypes(include='number').columns.tolist()[:6]
            if not numeric_cols_list:
                return {'indicators': [], 'series': []}
            
            try:
                top_parties = df.groupby(x_col)[numeric_cols_list[0]].sum().nlargest(5).index.tolist()
                indicators = []
                series_data = []
                
                for col in numeric_cols_list:
                    max_val = float(df[col].max())
                    indicators.append({'name': str(col)[:12], 'max': max_val if max_val > 0 else 100})
                
                for party in top_parties:
                    party_df = df[df[x_col] == party]
                    values = [float(party_df[col].sum()) for col in numeric_cols_list]
                    series_data.append({'name': str(party)[:20], 'values': values})
                
                return {'indicators': indicators, 'series': series_data}
            except:
                return {'indicators': [], 'series': []}
        
        # Calendar heatmap
        elif chart_type == 'CALENDAR_HEATMAP':
            if not x_col or not y_col:
                return {'data': [], 'year': '2024', 'max': 0}
            
            try:
                df_copy = df.copy()
                df_copy[x_col] = pd.to_datetime(df_copy[x_col], errors='coerce')
                daily = df_copy.groupby(df_copy[x_col].dt.date)[y_col].sum().reset_index()
                year = str(daily[x_col].iloc[0].year) if len(daily) > 0 else '2024'
                
                return {
                    'data': [[str(row[0]), float(row[1])] for row in daily.values.tolist()],
                    'year': year,
                    'max': float(daily[y_col].max()) if len(daily) > 0 else 1
                }
            except:
                return {'data': [], 'year': '2024', 'max': 0}
        
        # Pareto
        elif chart_type == 'PARETO':
            if not x_col or not y_col:
                return {'labels': [], 'values': [], 'cumulative': []}
            
            grouped = df.groupby(x_col)[y_col].agg(agg).reset_index()
            grouped = grouped.nlargest(limit, y_col).reset_index(drop=True)
            total = grouped[y_col].sum()
            
            if total > 0:
                grouped['cumulative_pct'] = (grouped[y_col].cumsum() / total * 100).round(1)
            else:
                grouped['cumulative_pct'] = 0
            
            return {
                'labels': [str(v)[:25] for v in grouped[x_col].tolist()],
                'values': grouped[y_col].round(2).tolist(),
                'cumulative': grouped['cumulative_pct'].tolist()
            }
        
        # Boxplot
        elif chart_type == 'BOXPLOT':
            if not x_col or not y_col:
                return {'data': [], 'labels': []}
            
            result = []
            labels_list = []
            
            for cat in df[x_col].value_counts().head(10).index:
                vals = df[df[x_col] == cat][y_col].dropna().tolist()
                if len(vals) >= 4:
                    q1, median, q3 = np.percentile(vals, [25,50,75])
                    result.append([min(vals), q1, median, q3, max(vals)])
                    labels_list.append(str(cat)[:20])
            
            return {'data': result, 'labels': labels_list}
        
        # Histogram
        elif chart_type == 'HISTOGRAM':
            if not y_col:
                return {'counts': [], 'bins': []}
            
            vals = df[y_col].dropna().tolist()
            if len(vals) < 2:
                return {'counts': [], 'bins': []}
            
            counts, bin_edges = np.histogram(vals, bins=20)
            return {
                'counts': counts.tolist(),
                'bins': [[float(bin_edges[i]), float(bin_edges[i+1])] for i in range(len(counts))]
            }
        
        # Sankey
        elif chart_type == 'SANKEY':
            if not x_col or not y_col or not series_col:
                return {'nodes': [], 'links': []}
            
            try:
                links_df = df.groupby([x_col, series_col])[y_col].sum().reset_index()
                links_df = links_df.nlargest(30, y_col)
                all_nodes = list(set(
                    links_df[x_col].tolist() + links_df[series_col].tolist()
                ))
                
                return {
                    'nodes': [str(n)[:20] for n in all_nodes],
                    'links': [
                        {'source': str(row[0]), 'target': str(row[1]), 'value': float(row[2])}
                        for row in links_df.values.tolist()
                    ]
                }
            except:
                return {'nodes': [], 'links': []}
        
        # Donut nested
        elif chart_type == 'DONUT_NESTED':
            if not x_col:
                return {'outer': [], 'inner': []}
            
            outer_y = y_col or (numeric_cols := [c for c in df.columns if df[c].dtype in ['int64','float64']])[0] if numeric_cols else None
            
            if not outer_y:
                return {'outer': [], 'inner': []}
            
            try:
                outer_grouped = df.groupby(x_col)[outer_y].sum().nlargest(8).reset_index()
                inner_grouped = df.groupby(x_col)[outer_y].count().nlargest(8).reset_index()
                
                return {
                    'outer': [{'name': str(r[0])[:20], 'value': float(r[1])} for r in outer_grouped.values.tolist()],
                    'inner': [{'name': str(r[0])[:20], 'value': float(r[1])} for r in inner_grouped.values.tolist()]
                }
            except:
                return {'outer': [], 'inner': []}
        
        return {'error': f'No handler for {chart_type}'}
    
    except Exception as e:
        logger.exception(f'prepare_chart_data error for {chart_type}')
        return {'error': str(e)}
