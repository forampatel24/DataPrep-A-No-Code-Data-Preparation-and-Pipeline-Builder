import pandas as pd
import numpy as np


def normalize_minmax(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_normalized') if column else 'normalized'
    min_val = kwargs.get('min', 0)
    max_val = kwargs.get('max', 1)
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    col = df_copy[column]
    col_min, col_max = col.min(), col.max()
    if col_max == col_min:
        df_copy[new_column] = max_val
    else:
        df_copy[new_column] = (col - col_min) / (col_max - col_min) * (max_val - min_val) + min_val
    return df_copy


def standardize_zscore(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_zscore') if column else 'zscore'
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    col = df_copy[column]
    mean, std = col.mean(), col.std()
    if std == 0 or pd.isna(std):
        df_copy[new_column] = 0
    else:
        df_copy[new_column] = (col - mean) / std
    return df_copy


def log_transform(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_log') if column else 'log'
    base = kwargs.get('base', 'natural')
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    col = pd.to_numeric(df_copy[column], errors='coerce')
    col = col.clip(lower=0)
    if base == 'natural':
        df_copy[new_column] = np.log1p(col)
    elif base == '10':
        df_copy[new_column] = np.log10(col + 1)
    elif base == '2':
        df_copy[new_column] = np.log2(col + 1)
    return df_copy


def sqrt_transform(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_sqrt') if column else 'sqrt'
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    col = pd.to_numeric(df_copy[column], errors='coerce')
    col = col.clip(lower=0)
    df_copy[new_column] = np.sqrt(col)
    return df_copy


def absolute_value(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_abs') if column else 'abs'
    inplace = kwargs.get('inplace', False)
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    if inplace:
        df_copy[column] = df_copy[column].abs()
    else:
        df_copy[new_column] = df_copy[column].abs()
    return df_copy


def round_values(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_rounded') if column else 'rounded'
    decimals = kwargs.get('decimals', 0)
    inplace = kwargs.get('inplace', False)
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    if inplace:
        df_copy[column] = df_copy[column].round(decimals)
    else:
        df_copy[new_column] = df_copy[column].round(decimals)
    return df_copy


def floor_values(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_floor') if column else 'floor'
    inplace = kwargs.get('inplace', False)
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    if inplace:
        df_copy[column] = np.floor(df_copy[column])
    else:
        df_copy[new_column] = np.floor(df_copy[column])
    return df_copy


def ceiling_values(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_ceil') if column else 'ceil'
    inplace = kwargs.get('inplace', False)
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    if inplace:
        df_copy[column] = np.ceil(df_copy[column])
    else:
        df_copy[new_column] = np.ceil(df_copy[column])
    return df_copy


def clip_values(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_clipped') if column else 'clipped'
    lower = kwargs.get('lower', None)
    upper = kwargs.get('upper', None)
    inplace = kwargs.get('inplace', False)
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    if inplace:
        df_copy[column] = df_copy[column].clip(lower=lower, upper=upper)
    else:
        df_copy[new_column] = df_copy[column].clip(lower=lower, upper=upper)
    return df_copy


def scale_by_constant(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_scaled') if column else 'scaled'
    factor = kwargs.get('factor', 1)
    inplace = kwargs.get('inplace', False)
    df_copy = df.copy()
    if column not in df_copy.columns or not pd.api.types.is_numeric_dtype(df_copy[column]):
        return df_copy
    if inplace:
        df_copy[column] = df_copy[column] * factor
    else:
        df_copy[new_column] = df_copy[column] * factor
    return df_copy
