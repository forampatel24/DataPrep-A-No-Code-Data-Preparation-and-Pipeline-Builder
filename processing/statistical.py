import pandas as pd
import numpy as np
import json


def _add_stat_column(df, column, new_column, value):
    df_copy = df.copy()
    df_copy[new_column] = value
    return df_copy


def compute_mean(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_mean') if column else 'mean'
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    val = df_copy[column].mean()
    return _add_stat_column(df_copy, column, new_column, val)


def compute_median(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_median') if column else 'median'
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    val = df_copy[column].median()
    return _add_stat_column(df_copy, column, new_column, val)


def compute_mode(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_mode') if column else 'mode'
    df_copy = df.copy()
    if column not in df_copy.columns:
        return df_copy
    mode_vals = df_copy[column].mode()
    val = mode_vals.iloc[0] if not mode_vals.empty else None
    return _add_stat_column(df_copy, column, new_column, val)


def compute_std(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_std') if column else 'std'
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    val = df_copy[column].std()
    return _add_stat_column(df_copy, column, new_column, val)


def compute_variance(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_variance') if column else 'variance'
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    val = df_copy[column].var()
    return _add_stat_column(df_copy, column, new_column, val)


def compute_skewness(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_skewness') if column else 'skewness'
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    val = df_copy[column].skew()
    return _add_stat_column(df_copy, column, new_column, val)


def compute_kurtosis(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_kurtosis') if column else 'kurtosis'
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    val = df_copy[column].kurtosis()
    return _add_stat_column(df_copy, column, new_column, val)


def correlation_matrix(df, **kwargs):
    columns = kwargs.get('columns', None)
    new_column = kwargs.get('new_column', '_correlation')
    df_copy = df.copy()
    if columns:
        valid_cols = [c for c in columns if c in df_copy.columns and pd.api.types.is_numeric_dtype(df_copy[c])]
    else:
        valid_cols = [c for c in df_copy.columns if pd.api.types.is_numeric_dtype(df_copy[c])]
    if len(valid_cols) < 2:
        return df_copy
    corr = df_copy[valid_cols].corr()
    for col in valid_cols:
        corr_series = corr[col]
        for other_col in valid_cols:
            if col != other_col:
                df_copy[f'{new_column}_{col}_{other_col}'] = corr_series[other_col]
    return df_copy
