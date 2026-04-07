"""
Local CSV Chat Module
======================
Intelligent data analyst using pandas + Ollama for accurate data-driven responses.

Core Design:
- Registers DataFrames from CSV uploads
- Builds rich prompts with ACTUAL dataset statistics
- Injects full or sample data directly into prompts
- Executes smart queries with pandas for instant answers
- Falls back to pre-computed answers if Ollama fails
- Zero cloud dependency - 100% local processing with Ollama
"""

import os
import re
import httpx
import pandas as pd
from typing import Optional, Dict, List, Any
from file_processor import read_file
from tabulate import tabulate

# Load environment
from dotenv import load_dotenv
load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("CHAT_MODEL", "phi3")

# ── Global DataFrame store ──────────────────────────────────
_current_df: Optional[pd.DataFrame] = None
_current_filename: str = ""
_data_profile: Dict[str, Any] = {}


def register_dataframe(df: pd.DataFrame, filename: str):
    """
    Call this immediately after every CSV/XLSX upload.
    Builds and caches all data statistics for efficient prompt building.
    """
    global _current_df, _current_filename, _data_profile
    _current_df = df.copy()
    _current_filename = filename
    _data_profile = _build_full_profile(df, filename)
    print(f"[CSV Chat] Registered: {filename} | {len(df)} rows x {len(df.columns)} columns")


def get_current_df() -> Optional[pd.DataFrame]:
    """Get the current registered DataFrame."""
    return _current_df


def is_data_loaded() -> bool:
    """Check if a DataFrame is currently loaded."""
    return _current_df is not None and len(_current_df) > 0


# ── Profile Builder ─────────────────────────────────────────
def _build_full_profile(df: pd.DataFrame, filename: str) -> dict:
    """
    Compute everything about the DataFrame once on upload.
    Pre-computes all stats to make prompt building fast.
    
    Returns: dict with
      - filename, rows, columns
      - numeric_stats: {col: {sum, mean, median, min, max, count}}
      - categorical_stats: {col: {unique, top10, most_common}}
      - date_cols: list of detected date columns
      - sample_markdown: first 40 rows as markdown table
      - full_csv: complete CSV if ≤300 rows, else empty
    """
    profile = {
        "filename": filename,
        "rows": len(df),
        "columns": list(df.columns),
        "numeric_stats": {},
        "categorical_stats": {},
        "date_cols": [],
        "sample_markdown": "",
        "full_csv": "",
    }

    # Compute numeric statistics
    for col in df.select_dtypes(include="number").columns:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        profile["numeric_stats"][col] = {
            "sum":    round(float(s.sum()), 2),
            "mean":   round(float(s.mean()), 2),
            "median": round(float(s.median()), 2),
            "min":    round(float(s.min()), 2),
            "max":    round(float(s.max()), 2),
            "count":  int(s.count()),
        }

    # Compute categorical statistics
    for col in df.select_dtypes(include="object").columns:
        vc = df[col].value_counts()
        profile["categorical_stats"][col] = {
            "unique": int(df[col].nunique()),
            "top10":  {str(k): int(v) for k, v in vc.head(10).items()},
            "most_common": str(vc.index[0]) if len(vc) > 0 else "",
        }

    # Detect date columns
    for col in df.columns:
        if any(kw in col.lower() for kw in ["date", "time", "created", "updated", "start", "end"]):
            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().sum() > len(df) * 0.3:
                    profile["date_cols"].append(col)
            except:
                pass

    # Sample rows as markdown (first 40 rows)
    try:
        profile["sample_markdown"] = df.head(40).fillna("").to_markdown(index=False)
    except:
        # Fallback if to_markdown not available
        profile["sample_markdown"] = df.head(40).fillna("").to_string(index=False)

    # Full CSV for small datasets (≤300 rows)
    # This is injected directly into the Ollama prompt for maximum accuracy
    if len(df) <= 300:
        profile["full_csv"] = df.fillna("").to_csv(index=False)

    return profile


def _detect_graph_request(question: str) -> Dict[str, str] | None:
    """
    Detect if user is asking for a graph generation.
    Returns: {"type": "bar|line|doughnut", "column": "col_name"} or None
    """
    question_lower = question.lower()
    
    # Graph keywords
    graph_keywords = ["graph", "chart", "visualize", "trend", "breakdown", "distribution", "compare", "plot"]
    if not any(kw in question_lower for kw in graph_keywords):
        return None
    
    # Detect chart type
    chart_type = "bar"  # default
    if "line" in question_lower or "trend" in question_lower or "over time" in question_lower:
        chart_type = "line"
    elif "pie" in question_lower or "doughnut" in question_lower or "distribution" in question_lower or "breakdown" in question_lower:
        chart_type = "doughnut"
    elif "scatter" in question_lower:
        chart_type = "scatter"
    
    # Try to extract column name from question
    profile = _data_profile
    all_columns = profile.get("columns", [])
    
    target_column = None
    for col in all_columns:
        if col.lower() in question_lower:
            target_column = col
            break
    
    return {
        "type": chart_type,
        "column": target_column,
        "question": question
    }


def generate_dynamic_chart(request: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Generate a chart dynamically based on user request.
    
    Returns chart config ready for Chart.js or None if can't generate.
    """
    if not is_data_loaded():
        return None
    
    df = _current_df
    profile = _data_profile
    
    chart_type = request.get("type", "bar")
    column = request.get("column")
    
    try:
        # Auto-detect column if not specified
        if not column:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            if chart_type == "doughnut" and categorical_cols:
                column = categorical_cols[0]
            elif numeric_cols:
                column = numeric_cols[0]
            else:
                return None
        
        if column not in df.columns:
            return None
        
        # Generate based on column type
        if pd.api.types.is_numeric_dtype(df[column]):
            # Numeric column - create line or bar chart
            data_agg = df[column].describe().to_dict()
            
            chart_config = {
                "id": f"dynamic_{column}",
                "type": chart_type if chart_type in ["line", "bar"] else "bar",
                "title": f"{column.replace('_', ' ').title()} Distribution",
                "labels": ["Min", "Mean", "Median", "Max"],
                "datasets": [{
                    "label": column,
                    "data": [
                        float(data_agg.get("min", 0)),
                        float(data_agg.get("mean", 0)),
                        float(data_agg.get("50%", 0)),
                        float(data_agg.get("max", 0))
                    ],
                    "borderColor": "rgb(75, 165, 245)",
                    "backgroundColor": ["rgba(75, 165, 245, 0.1)", "rgba(100, 165, 245, 0.1)", 
                                      "rgba(125, 165, 245, 0.1)", "rgba(150, 165, 245, 0.1)"],
                }]
            }
        else:
            # Categorical column - create doughnut/pie
            value_counts = df[column].value_counts().head(10).to_dict()
            colors = ["#60a5fa", "#34d399", "#fbbf24", "#f87171", "#a78bfa", 
                     "#fb923c", "#0ea5e9", "#6366f1", "#ec4899", "#14b8a6"]
            
            chart_config = {
                "id": f"dynamic_{column}",
                "type": "doughnut",
                "title": f"{column.replace('_', ' ').title()} Breakdown",
                "labels": list(value_counts.keys()),
                "datasets": [{
                    "label": column,
                    "data": list(value_counts.values()),
                    "backgroundColor": colors[:len(value_counts)],
                    "borderColor": "#1a1d2e",
                    "borderWidth": 2
                }]
            }
        
        return chart_config
    
    except Exception as e:
        print(f"[Chart Generation Error] {e}")
        return None


def register_dataframe(df: pd.DataFrame, filename: str) -> None:
    """
    Register a DataFrame immediately after CSV/XLSX upload.
    
    CRITICAL: Call this in the upload endpoint RIGHT AFTER reading the file.
    
    Args:
        df: Pandas DataFrame from read_csv() or read_excel()
        filename: Original filename (e.g., "sales.csv")
    """
    global _current_df, _current_filename, _data_profile
    
    _current_df = df.copy()
    _current_filename = filename
    _data_profile = _build_data_profile(df)
    
    print(f"[CSV Chat] Registered: {filename} ({len(df)} rows × {len(df.columns)} columns)")


def is_data_loaded() -> bool:
    """Check if a DataFrame is currently loaded."""
    return _current_df is not None and len(_current_df) > 0


def get_current_df() -> Optional[pd.DataFrame]:
    """Get the currently registered DataFrame."""
    return _current_df if is_data_loaded() else None


def _build_data_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """Build comprehensive data profile for prompt building."""
    profile = {
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
        "numeric_stats": {},
        "categorical_stats": {},
    }
    
    # Numeric column statistics
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        profile["numeric_stats"][col] = {
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "mean": float(df[col].mean()),
            "median": float(df[col].median()),
            "sum": float(df[col].sum()),
        }
    
    # Categorical column top values
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        top_vals = df[col].value_counts().head(5).to_dict()
        profile["categorical_stats"][col] = top_vals
    
    return profile


def _execute_smart_query(question: str, df: pd.DataFrame, profile: Dict) -> str:
    """
    Try to answer directly using pandas before going to Ollama.
    This provides instant, accurate answers for common questions.
    
    Returns empty string if pandas can't answer the question.
    """
    import re
    question_lower = question.lower()
    
    try:
        # CUSTOMER DETAIL REPORT (e.g., "give me customer report of 2140056-Siliguri Agencies...")
        # Pattern: "customer report of" + customer identifier + optional filtering
        if ("customer report" in question_lower or "report of" in question_lower) and ("of " in question_lower or "for " in question_lower):
            # Extract customer name/identifier from the question
            customer_search = None
            
            # Try multiple patterns
            if "customer report of " in question_lower:
                parts = question_lower.split("customer report of ")
                customer_search = parts[1].split(" by ")[0].split(" throughout ")[0].split(" in ")[0].split(" show ")[0].strip()
            elif "report of " in question_lower:
                parts = question_lower.split("report of ")
                customer_search = parts[1].split(" by ")[0].split(" throughout ")[0].split(" in ")[0].split(" show ")[0].strip()
            elif "report for " in question_lower:
                parts = question_lower.split("report for ")
                customer_search = parts[1].split(" by ")[0].split(" throughout ")[0].split(" in ")[0].split(" show ")[0].strip()
            
            if customer_search and len(customer_search) > 2:
                # Find customer name column
                customer_col = None
                for col in df.columns:
                    col_clean = col.lower().replace('<br/>', '').strip()
                    if 'customer' in col_clean and 'name' in col_clean:
                        customer_col = col
                        break
                
                # Find amount column
                amount_col = None
                for col in df.columns:
                    col_clean = col.lower().replace('<br/>', '').strip()
                    if any(kw in col_clean for kw in ['amount', 'total', 'value', 'sales', 'revenue']):
                        amount_col = col
                        break
                
                # Try to find the customer in the dataframe
                if customer_col:
                    # Find matching customer(s) in dataframe
                    # Try the extracted search term first
                    mask = df[customer_col].astype(str).str.contains(customer_search, case=False, na=False)
                    
                    # If no exact match, try pattern matching on parts of the customer name
                    if not mask.any():
                        # Try first part (ID)
                        first_part = customer_search.split('-')[0].strip()
                        if first_part and len(first_part) > 2:
                            mask = df[customer_col].astype(str).str.contains(first_part, case=False, na=False)
                    
                    if mask.any():
                        customer_df = df[mask].copy()
                        
                        # Convert amount to numeric if needed
                        if amount_col and customer_df[amount_col].dtype == 'object':
                            customer_df[amount_col] = pd.to_numeric(customer_df[amount_col], errors='coerce')
                        
                        # Sort by amount descending
                        if amount_col:
                            customer_df = customer_df.sort_values(by=amount_col, ascending=False, na_position='last')
                        
                        # Build report
                        result = f"CUSTOMER REPORT: {customer_search.upper()}\n"
                        result += f"{'═' * 70}\n"
                        result += f"Total Transactions: {len(customer_df)}\n"
                        
                        if amount_col:
                            total_amount = customer_df[amount_col].sum()
                            avg_amount = customer_df[amount_col].mean()
                            result += f"Total Amount: Rs {total_amount:,.2f}\n"
                            result += f"Average per Transaction: Rs {avg_amount:,.2f}\n"
                            result += f"{'─' * 70}\n"
                            result += f"Transactions (sorted by amount, highest first):\n"
                            result += f"{'─' * 70}\n"
                            
                            for idx, (i, row) in enumerate(customer_df.iterrows(), 1):
                                amt = row[amount_col] if pd.notna(row[amount_col]) else 0
                                result += f"{idx:3d}. Rs {float(amt):>12,.2f}\n"
                        
                        return result.strip()
        
        # TOP N BY CATEGORY/AMOUNT QUERIES (e.g., "Top 5 Customer Categories by Amount" or "Top 5 Customers by Amount")
        top_match = re.search(r'top\s+(\d+)\s+(.+?)\s+by\s+(\w+)', question_lower)
        if top_match:
            n = int(top_match.group(1))
            group_mention = top_match.group(2).strip()
            amount_col_name = top_match.group(3).strip()
            
            # Determine which column to group by based on the question
            group_col = None
            
            # Priority 1: Check if "category" is mentioned → Customer Category column
            if 'category' in group_mention.lower() or 'categor' in group_mention.lower():
                for col in df.columns:
                    col_lower = col.lower()
                    if 'category' in col_lower:
                        group_col = col
                        break
            
            # Priority 2: Check if question mentions "customer" (name) without "category"
            elif 'customer' in group_mention.lower() and 'category' not in group_mention.lower():
                # Looking for customer names, not categories
                for col in df.columns:
                    col_clean = col.lower().replace('<br/>', '').strip()
                    if 'customer' in col_clean and 'name' in col_clean:
                        group_col = col
                        break
                # If no "customer name" found, try any "customer" column
                if not group_col:
                    for col in df.columns:
                        col_clean = col.lower().replace('<br/>', '').strip()
                        if col_clean == 'customer' or (col_clean.startswith('customer') and 'name' in col_clean):
                            group_col = col
                            break
            
            # Priority 3: Match the mentioned text in column names
            if not group_col:
                for col in df.columns:
                    col_clean = col.lower().replace('<br/>', '').strip()
                    group_mention_clean = group_mention.lower().replace('<br/>', '').strip()
                    if col_clean in group_mention_clean or group_mention_clean in col_clean:
                        group_col = col
                        break
            
            # Priority 4: Use keyword matching
            if not group_col:
                for col in df.columns:
                    col_lower = col.lower()
                    if any(kw in col_lower for kw in ['name', 'category', 'type', 'group']):
                        group_col = col
                        break
            
            # Priority 5: Default to first non-numeric column
            if not group_col:
                for col in df.select_dtypes(include=['object']).columns:
                    group_col = col
                    break
            
            # Find matching amount/value column
            amount_col = None
            for col in df.columns:
                col_clean = col.lower().replace('<br/>', '').strip()
                if any(kw in col_clean for kw in ['amount', 'total', 'value', 'sales', 'revenue']):
                    amount_col = col
                    break
            
            # If no amount column found, use first numeric column
            if not amount_col:
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if numeric_cols:
                    amount_col = numeric_cols[0]
            
            # Execute the aggregation
            if group_col and amount_col:
                try:
                    # Convert to numeric if needed (Amount is sometimes stored as text)
                    if df[amount_col].dtype == 'object':
                        df = df.copy()
                        df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
                    
                    # Group by the column and sum the amounts
                    grouped = df.groupby(group_col)[amount_col].sum().nlargest(n)
                    col_display = group_col.replace('<br/>', ' ').strip()
                    result = "Top {} {} by {}:\n".format(n, col_display, amount_col.replace('<br/>', ' ').strip())
                    for rank, (val, amt) in enumerate(grouped.items(), 1):
                        result += "{}. {}: {:,.2f}\n".format(rank, val, float(amt))
                    return result.strip()
                except Exception as e:
                    print(f"[Smart Query] Group-by failed: {e}")
                    pass
        
        # Count rows
        if "how many rows" in question_lower or "total records" in question_lower or "number of rows" in question_lower:
            return f"The dataset contains {len(df)} rows."
        
        # Sum numeric columns
        for col in df.select_dtypes(include=['number']).columns:
            if f"total {col.lower()}" in question_lower or f"sum of {col.lower()}" in question_lower:
                total = float(df[col].sum())
                return f"The total {col} is {total:,.2f}."
        
        # Average numeric columns
        for col in df.select_dtypes(include=['number']).columns:
            if f"average {col.lower()}" in question_lower or f"mean {col.lower()}" in question_lower:
                avg = float(df[col].mean())
                return f"The average {col} is {avg:,.2f}."
        
        # Count distinct categorical values
        for col in df.select_dtypes(include=['object']).columns:
            if f"unique {col.lower()}" in question_lower or f"distinct {col.lower()}" in question_lower or f"how many {col.lower()}" in question_lower:
                count = df[col].nunique()
                return f"There are {count} unique values in {col}."
        
        # List unique values
        for col in df.select_dtypes(include=['object']).columns:
            if f"values in {col.lower()}" in question_lower or f"values of {col.lower()}" in question_lower:
                values = df[col].unique()[:10]
                values_str = ", ".join(str(v) for v in values)
                return f"Values in {col}: {values_str}"
        
        # Max/min values
        for col in df.select_dtypes(include=['number']).columns:
            if f"highest {col.lower()}" in question_lower or f"max {col.lower()}" in question_lower:
                max_val = float(df[col].max())
                return f"The highest {col} is {max_val:,.2f}."
            if f"lowest {col.lower()}" in question_lower or f"min {col.lower()}" in question_lower:
                min_val = float(df[col].min())
                return f"The lowest {col} is {min_val:,.2f}."
        
        # Distribution/breakdown by category
        for col in df.select_dtypes(include=['object']).columns:
            if f"breakdown" in question_lower and col.lower() in question_lower:
                breakdown = df[col].value_counts().to_dict()
                breakdown_str = ", ".join(f"{k}: {v}" for k, v in list(breakdown.items())[:5])
                return f"Breakdown by {col}: {breakdown_str}"
        
        # HIGHEST/LOWEST VALUES (e.g., "highest sales", "lowest price")
        for col in df.select_dtypes(include=['number']).columns:
            col_lower = col.lower()
            if ("highest" in question_lower or "max" in question_lower or "maximum" in question_lower) and col_lower in question_lower:
                max_val = float(df[col].max())
                max_idx = df[col].idxmax()
                return f"The highest {col} is {max_val:,.2f}."
            if ("lowest" in question_lower or "min" in question_lower or "minimum" in question_lower) and col_lower in question_lower:
                min_val = float(df[col].min())
                min_idx = df[col].idxmin()
                return f"The lowest {col} is {min_val:,.2f}."
        
        # SPECIFIC VALUE LOOKUPS (e.g., "how many units of mouse", "quantity of keyboard")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        for col in df.select_dtypes(include=['object']).columns:
            col_lower = col.lower()
            for idx, row in df.iterrows():
                val_str = str(row[col]).lower()
                if val_str in question_lower and len(val_str) > 2:  # Avoid matching tiny strings
                    # Found the product/value in the data - choose best numeric column
                    if numeric_cols:
                        # Prioritize: units, quantity, count, amount, then first numeric
                        best_col = None
                        for priority_col in ['units', 'quantity', 'count', 'amount']:
                            for nc in numeric_cols:
                                if priority_col in nc.lower():
                                    best_col = nc
                                    break
                            if best_col:
                                break
                        
                        best_col = best_col or numeric_cols[0]
                        result_val = float(row[best_col])
                        return f"For {row[col]}: {best_col} = {result_val:,.0f}."
        
    except Exception as e:
        # If smart query fails, return empty and let Ollama handle it
        print(f"[CSV Chat] Smart query failed: {e}")
    
    return ""


def _build_numeric_block(profile: Dict) -> str:
    """Build formatted block of numeric statistics."""
    block = "\n=== NUMERIC COLUMNS ===\n"
    
    for col, stats in profile["numeric_stats"].items():
        block += f"{col}:\n"
        block += f"  Sum: {stats['sum']:,.2f} | Mean: {stats['mean']:,.2f} | Median: {stats['median']:,.2f}\n"
        block += f"  Min: {stats['min']:,.2f} | Max: {stats['max']:,.2f}\n"
    
    return block if profile["numeric_stats"] else ""


def _build_categorical_block(profile: Dict) -> str:
    """Build formatted block of categorical statistics."""
    block = "\n=== CATEGORICAL COLUMNS ===\n"
    
    for col, top_vals in profile["categorical_stats"].items():
        block += f"{col} (top values):\n"
        for val, count in list(top_vals.items())[:5]:
            block += f"  {val}: {count}\n"
    
    return block if profile["categorical_stats"] else ""


def _build_data_block(df: pd.DataFrame) -> str:
    """Build sample data table for the prompt."""
    block = "\n=== DATA SAMPLE ===\n"
    
    # If dataset is small, include all rows; otherwise first 30 + last 10
    if len(df) <= 100:
        sample = df.head(100)
    else:
        sample = pd.concat([df.head(30), df.tail(10)])
    
    try:
        block += tabulate(sample, headers="keys", tablefmt="plain", showindex=False) + "\n"
    except Exception:
        # Fallback if tabulate fails
        block += df.head(50).to_string() + "\n"
    
    return block


def _build_ollama_prompt(question: str, profile: Dict, pre_answer: str = "") -> str:
    """
    Build optimized prompt for phi3:latest focused on accurate data analysis.
    
    phi3:latest excels at:
    - Precise numerical analysis
    - Clear aggregation from data
    - Specific factual answers
    - Direct column-based calculations
    """
    df = _current_df
    
    prompt = f"""You are a precise data analyst. Your task is to answer the question BASED ONLY ON THE DATA PROVIDED.

IMPORTANT RULES:
1. Use ONLY the data shown below - never make assumptions
2. When calculating totals or averages, use the actual data values
3. Be specific: mention actual product names, categories, or values
4. If you cannot find the answer in the data, say so clearly
5. Always provide numerical answers when the question asks for numbers

DATASET: {_current_filename}
ROWS: {profile['rows']} | COLUMNS: {len(profile['columns'])}
COLUMN NAMES: {', '.join(profile['columns'])}

{_build_numeric_block(profile)}
{_build_categorical_block(profile)}
"""
    
    # Include full data sample for phi3 (more capable)
    if len(df) <= 100:
        sample = df.copy()
    else:
        sample = pd.concat([df.head(30), df.tail(20)])
    
    try:
        prompt += "\nFULL DATA:\n"
        prompt += tabulate(sample, headers="keys", tablefmt="grid", showindex=True) + "\n"
    except Exception:
        prompt += "\nDATA:\n" + df.to_string() + "\n"
    
    # Include pre-computed answer as validation
    if pre_answer:
        prompt += f"\nVALIDATION: {pre_answer}\n"
    
    prompt += f"\nUSER QUESTION: {question}\n\nANSWER (be specific and data-backed):"
    
    return prompt


# ─── Main Chat Function ───────────────────────────────────
def chat_with_data(question: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
    """
    Main entry point for chat. Call this from FastAPI /api/chat endpoint.
    
    Args:
        question: The user's question
        conversation_history: List of {"role": "user"/"assistant", "content": "..."} dicts
    
    Returns:
        {
            "answer": str,           # The response to return to user
            "data_used": bool,       # Whether actual data was used
            "pre_computed": bool,    # Whether answer came from pandas (vs Ollama)
            "error": str|None        # Error message if any
        }
    """
    
    # Check if data is loaded
    if not is_data_loaded():
        return {
            "answer": "No CSV file is currently loaded. Please upload a CSV or Excel file first, then ask your question.",
            "data_used": False,
            "pre_computed": False,
            "error": None,
            "chart": None
        }
    
    df = _current_df
    profile = _data_profile
    
    # Check if user is asking for a graph
    graph_request = _detect_graph_request(question)
    chart_config = None
    if graph_request:
        chart_config = generate_dynamic_chart(graph_request)
        
        # If chart generated successfully, return early with confirmation
        if chart_config:
            col_name = chart_config.get("title", "Chart")
            return {
                "answer": f"✓ Generated {chart_config['type'].title()} chart: {col_name}",
                "data_used": True,
                "pre_computed": True,
                "error": None,
                "chart": chart_config
            }
    
    # Step 1: Try to answer directly from pandas (instant + accurate)
    pre_answer = _execute_smart_query(question, df, profile)
    
    # If we have a strong pre-computed answer (like top-N results), return it directly
    if pre_answer and (pre_answer.startswith("Top") or pre_answer.startswith("1.")):
        return {
            "answer": pre_answer,
            "data_used": True,
            "pre_computed": True,
            "error": None,
            "chart": None
        }
    
    # Step 2: Build rich prompt with all data context
    prompt = _build_ollama_prompt(question, profile, pre_answer)
    
    # Step 3: Call Ollama locally
    try:
        # Build messages array for Ollama chat API
        messages = []
        
        # Add conversation history (last 6 messages for context)
        if conversation_history:
            for msg in conversation_history[-6:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # Add the current prompt as the final user message
        messages.append({"role": "user", "content": prompt})
        
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": CHAT_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.1,      # Low temperature for precise analysis (phi3)
                    "num_predict": 500,      # Concise but complete responses
                    "top_p": 0.9,            # Maintain diversity while staying on topic
                    "top_k": 30,             # Reduced for more focused outputs
                }
            },
            timeout=120.0  # phi3 needs time for analysis
        )
        
        if response.status_code == 200:
            try:
                # Safely parse JSON response - Ollama might return non-JSON on error
                data = response.json()
                answer = data.get("message", {}).get("content", "").strip()
                
                if not answer:
                    answer = "Ollama returned an empty response. Please try again."
                
                return {
                    "answer": answer,
                    "data_used": True,
                    "pre_computed": bool(pre_answer),
                    "error": None,
                    "chart": chart_config
                }
            except ValueError as json_err:
                # Handle invalid JSON gracefully - return pre-computed answer or fallback message
                if pre_answer:
                    return {"answer": pre_answer, "data_used": True, "pre_computed": True, "error": json_err}
                return {"answer": "Analysis service temporarily unavailable", "data_used": False, "pre_computed": False, "error": json_err}
        else:
            error_msg = f"Ollama API error: {response.status_code}"
            print(f"[CSV Chat Error] {error_msg}")
            print(f"[CSV Chat Debug] Response: {response.text[:200]}")
            
            # If Ollama fails but we have a pre-computed answer, return that
            if pre_answer:
                return {
                    "answer": f"Here's what I found in your data:\n\n{pre_answer}\n\n(Note: Ollama service temporarily unavailable)",
                    "data_used": True,
                    "pre_computed": True,
                    "error": error_msg,
                    "chart": chart_config
                }
            return {
                "answer": "Analysis service is not responding. Please check Ollama: `ollama serve`",
                "data_used": False,
                "pre_computed": False,
                "error": error_msg,
                "chart": None
            }
    
    except httpx.ConnectError as e:
        msg = "Cannot connect to Ollama. Start it with: ollama serve"
        if pre_answer:
            return {
                "answer": f"Ollama is offline, but here's what I calculated directly:\n\n{pre_answer}",
                "data_used": True,
                "pre_computed": True,
                "error": msg,
                "chart": chart_config
            }
        return {
            "answer": msg,
            "data_used": False,
            "pre_computed": False,
            "error": msg,
            "chart": None
        }
    
    except httpx.TimeoutException:
        if pre_answer:
            return {
                "answer": f"Ollama timed out, but here's the direct calculation:\n\n{pre_answer}",
                "data_used": True,
                "pre_computed": True,
                "error": "Timeout",
                "chart": chart_config
            }
        return {
            "answer": "Ollama took too long. Try a smaller model: `ollama pull llama3.2` or `ollama pull phi3`",
            "data_used": False,
            "pre_computed": False,
            "error": "Timeout",
            "chart": None
        }
    
    except Exception as e:
        return {
            "answer": f"Unexpected error: {str(e)}",
            "data_used": False,
            "pre_computed": False,
            "error": str(e),
            "chart": None
        }


def chat_with_data_stream(question: str):
    """
    Generator version for streaming responses (optional, for better UX).
    Use with FastAPI StreamingResponse for real-time token output.
    
    Usage in FastAPI:
        from fastapi.responses import StreamingResponse
        return StreamingResponse(chat_with_data_stream(question), media_type="text/plain")
    """
    if not is_data_loaded():
        yield "No CSV loaded. Please upload a file first."
        return
    
    profile = _data_profile
    pre_answer = _execute_smart_query(question, _current_df, profile)
    prompt = _build_ollama_prompt(question, profile, pre_answer)
    
    try:
        with httpx.stream(
            "POST",
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": CHAT_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "options": {"temperature": 0.1, "num_predict": 1024}
            },
            timeout=120.0
        ) as response:
            for line in response.iter_lines():
                if line:
                    try:
                        import json
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"\n[Error: {str(e)}]"
