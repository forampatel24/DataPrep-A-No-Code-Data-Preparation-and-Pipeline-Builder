import pandas as pd
import re


def convert_dtype(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    column = kwargs.get('column', '')
    target_type = kwargs.get('target_type', 'string')

    if column not in df.columns:
        return df

    df_copy = df.copy()

    if target_type == 'string':
        df_copy[column] = df_copy[column].astype(str)
    elif target_type == 'integer':
        df_copy[column] = pd.to_numeric(df_copy[column], errors='coerce').astype('Int64')
    elif target_type == 'float':
        df_copy[column] = pd.to_numeric(df_copy[column], errors='coerce').astype('float64')
    elif target_type == 'datetime':
        df_copy[column] = pd.to_datetime(df_copy[column], errors='coerce')

    return df_copy


def format_dates(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    column = kwargs.get('column', '')
    date_format = kwargs.get('date_format', '%Y-%m-%d')

    if column not in df.columns:
        return df

    df_copy = df.copy()
    df_copy[column] = pd.to_datetime(df_copy[column], errors='coerce')
    df_copy[column] = df_copy[column].dt.strftime(date_format)

    return df_copy


def uppercase(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    columns = kwargs.get('columns', [])
    df_copy = df.copy()

    for col in columns:
        if col in df_copy.columns and df_copy[col].dtype == 'object':
            df_copy[col] = df_copy[col].astype(str).str.upper()

    return df_copy


def lowercase(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    columns = kwargs.get('columns', [])
    df_copy = df.copy()

    for col in columns:
        if col in df_copy.columns and df_copy[col].dtype == 'object':
            df_copy[col] = df_copy[col].astype(str).str.lower()

    return df_copy


def title_case(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    columns = kwargs.get('columns', [])
    df_copy = df.copy()

    for col in columns:
        if col in df_copy.columns and df_copy[col].dtype == 'object':
            df_copy[col] = df_copy[col].astype(str).str.title()

    return df_copy


def remove_special_chars(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    columns = kwargs.get('columns', [])
    df_copy = df.copy()

    for col in columns:
        if col in df_copy.columns and df_copy[col].dtype == 'object':
            df_copy[col] = df_copy[col].astype(str).str.replace(r'[^a-zA-Z0-9\s]', '', regex=True)

    return df_copy


def regex_replace(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    column = kwargs.get('column', '')
    pattern = kwargs.get('pattern', '')
    replacement = kwargs.get('replacement', '')
    case_sensitive = kwargs.get('case_sensitive', True)

    if column not in df.columns:
        return df

    df_copy = df.copy()
    flags = 0 if case_sensitive else re.IGNORECASE
    df_copy[column] = df_copy[column].astype(str).str.replace(pattern, replacement, regex=True, flags=flags)
    return df_copy


def auto_detect_dtypes(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    df_copy = df.copy()
    for col in df_copy.columns:
        if pd.api.types.is_string_dtype(df_copy[col]) or df_copy[col].dtype == 'object':
            lowered = df_copy[col].astype(str).str.lower()
            if lowered.str.match(r'^(true|false|yes|no|1|0)$').all():
                df_copy[col] = lowered.map({'true': True, 'false': False, 'yes': True, 'no': False, '1': True, '0': False})
                continue
            try:
                parsed = pd.to_datetime(df_copy[col], errors='coerce')
                if parsed.notna().sum() > len(df_copy) * 0.7:
                    df_copy[col] = parsed
                    continue
            except Exception:
                pass
            try:
                numeric = pd.to_numeric(df_copy[col], errors='coerce')
                if numeric.notna().sum() > len(df_copy) * 0.7:
                    df_copy[col] = numeric
            except Exception:
                pass
        elif pd.api.types.is_numeric_dtype(df_copy[col]):
            if df_copy[col].dropna().apply(lambda x: float(x).is_integer()).all():
                df_copy[col] = df_copy[col].astype('Int64')
    return df_copy


def boolean_conversion(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_bool') if column else 'boolean'
    true_values = kwargs.get('true_values', ['true', 'yes', '1', 1, 'y', 't'])
    false_values = kwargs.get('false_values', ['false', 'no', '0', 0, 'n', 'f'])
    df_copy = df.copy()
    if column not in df_copy.columns:
        return df_copy
    col_str = df_copy[column].astype(str).str.lower().str.strip()
    result = pd.Series(index=df_copy.index, dtype='object')
    for v in true_values:
        result = result.mask(col_str == str(v).lower(), True)
    for v in false_values:
        result = result.mask(col_str == str(v).lower(), False)
    df_copy[new_column] = result
    return df_copy


def add_derived_column(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    new_column = kwargs.get('new_column', 'derived')
    expression = kwargs.get('expression', '')
    source_columns = kwargs.get('source_columns', [])

    df_copy = df.copy()

    if expression == 'concat' and len(source_columns) >= 2:
        sep = kwargs.get('separator', ' ')
        cols = [c for c in source_columns if c in df_copy.columns]
        if len(cols) >= 2:
            df_copy[new_column] = df_copy[cols[0]].astype(str) + sep + df_copy[cols[1]].astype(str)
    elif expression == 'sum' and source_columns:
        cols = [c for c in source_columns if c in df_copy.columns]
        if cols:
            df_copy[new_column] = df_copy[cols].sum(axis=1)
    elif expression == 'difference' and len(source_columns) >= 2:
        cols = [c for c in source_columns if c in df_copy.columns]
        if len(cols) >= 2:
            df_copy[new_column] = df_copy[cols[0]] - df_copy[cols[1]]
    elif expression == 'product' and source_columns:
        cols = [c for c in source_columns if c in df_copy.columns]
        if cols:
            df_copy[new_column] = df_copy[cols].prod(axis=1)
    elif expression == 'quotient' and len(source_columns) >= 2:
        cols = [c for c in source_columns if c in df_copy.columns]
        if len(cols) >= 2:
            df_copy[new_column] = df_copy[cols[0]] / df_copy[cols[1]].replace(0, pd.NA)
    elif expression == 'formula':
        formula = kwargs.get('formula', '')
        if formula:
            df_copy[new_column] = df_copy.eval(formula)

    return df_copy
