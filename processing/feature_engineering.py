import pandas as pd
import numpy as np


def conditional_column(df, **kwargs):
    new_column = kwargs.get('new_column', 'condition')
    column = kwargs.get('column', '')
    operator = kwargs.get('operator', '==')
    value = kwargs.get('value', None)
    true_value = kwargs.get('true_value', True)
    false_value = kwargs.get('false_value', False)
    df_copy = df.copy()
    if column not in df_copy.columns:
        return df_copy
    col = df_copy[column]
    if operator == '==':
        mask = col == value
    elif operator == '!=':
        mask = col != value
    elif operator == '>':
        mask = pd.to_numeric(col, errors='coerce') > float(value)
    elif operator == '<':
        mask = pd.to_numeric(col, errors='coerce') < float(value)
    elif operator == '>=':
        mask = pd.to_numeric(col, errors='coerce') >= float(value)
    elif operator == '<=':
        mask = pd.to_numeric(col, errors='coerce') <= float(value)
    elif operator == 'in':
        values_list = kwargs.get('values_list', [])
        mask = col.isin(values_list)
    elif operator == 'contains':
        mask = col.astype(str).str.contains(str(value), na=False)
    elif operator == 'isnull':
        mask = col.isna()
    elif operator == 'notnull':
        mask = col.notna()
    else:
        mask = pd.Series(False, index=df_copy.index)
    df_copy[new_column] = np.where(mask, true_value, false_value)
    return df_copy


def bin_values(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_binned') if column else 'binned'
    bins = kwargs.get('bins', 4)
    labels = kwargs.get('labels', None)
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    if isinstance(bins, int):
        try:
            df_copy[new_column] = pd.cut(df_copy[column], bins=bins, labels=labels)
        except Exception:
            df_copy[new_column] = pd.qcut(df_copy[column], q=bins, labels=labels, duplicates='drop')
    elif isinstance(bins, list):
        df_copy[new_column] = pd.cut(df_copy[column], bins=bins, labels=labels)
    return df_copy


def percentage_column(df, **kwargs):
    numerator = kwargs.get('numerator', '')
    denominator = kwargs.get('denominator', '')
    new_column = kwargs.get('new_column', 'percentage')
    multiply = kwargs.get('multiply', True)
    df_copy = df.copy()
    if numerator not in df_copy.columns or denominator not in df_copy.columns:
        return df_copy
    denom = df_copy[denominator].replace(0, pd.NA)
    result = pd.to_numeric(df_copy[numerator], errors='coerce') / pd.to_numeric(denom, errors='coerce')
    if multiply:
        result = result * 100
    df_copy[new_column] = result
    return df_copy


def average_columns(df, **kwargs):
    columns = kwargs.get('columns', [])
    new_column = kwargs.get('new_column', 'average')
    df_copy = df.copy()
    valid_cols = [c for c in columns if c in df_copy.columns]
    if not valid_cols:
        return df_copy
    df_copy[new_column] = df_copy[valid_cols].apply(pd.to_numeric, errors='coerce').mean(axis=1)
    return df_copy


def count_non_null(df, **kwargs):
    columns = kwargs.get('columns', [])
    new_column = kwargs.get('new_column', 'non_null_count')
    df_copy = df.copy()
    valid_cols = [c for c in columns if c in df_copy.columns]
    if not valid_cols:
        return df_copy
    df_copy[new_column] = df_copy[valid_cols].notna().sum(axis=1)
    return df_copy
