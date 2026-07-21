import pandas as pd
import numpy as np


def _ensure_datetime(df, column):
    if column not in df.columns:
        return None
    if not pd.api.types.is_datetime64_any_dtype(df[column]):
        return pd.to_datetime(df[column], errors='coerce')
    return df[column]


def extract_year(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_year') if column else 'year'
    df_copy = df.copy()
    dt_series = _ensure_datetime(df_copy, column)
    if dt_series is None:
        return df_copy
    df_copy[new_column] = dt_series.dt.year
    return df_copy


def extract_month(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_month') if column else 'month'
    as_name = kwargs.get('as_name', False)
    df_copy = df.copy()
    dt_series = _ensure_datetime(df_copy, column)
    if dt_series is None:
        return df_copy
    if as_name:
        df_copy[new_column] = dt_series.dt.month_name()
    else:
        df_copy[new_column] = dt_series.dt.month
    return df_copy


def extract_day(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_day') if column else 'day'
    df_copy = df.copy()
    dt_series = _ensure_datetime(df_copy, column)
    if dt_series is None:
        return df_copy
    df_copy[new_column] = dt_series.dt.day
    return df_copy


def extract_weekday(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_weekday') if column else 'weekday'
    as_name = kwargs.get('as_name', True)
    df_copy = df.copy()
    dt_series = _ensure_datetime(df_copy, column)
    if dt_series is None:
        return df_copy
    if as_name:
        df_copy[new_column] = dt_series.dt.day_name()
    else:
        df_copy[new_column] = dt_series.dt.weekday + 1
    return df_copy


def extract_quarter(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_quarter') if column else 'quarter'
    df_copy = df.copy()
    dt_series = _ensure_datetime(df_copy, column)
    if dt_series is None:
        return df_copy
    df_copy[new_column] = dt_series.dt.quarter
    return df_copy


def calculate_age(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_age') if column else 'age'
    reference_date = kwargs.get('reference_date', None)
    df_copy = df.copy()
    dt_series = _ensure_datetime(df_copy, column)
    if dt_series is None:
        return df_copy
    ref = pd.to_datetime(reference_date) if reference_date else pd.Timestamp.now()
    df_copy[new_column] = ((ref - dt_series).dt.days / 365.25).astype(int)
    return df_copy


def days_between_dates(df, **kwargs):
    start_column = kwargs.get('start_column', '')
    end_column = kwargs.get('end_column', '')
    new_column = kwargs.get('new_column', 'days_between')
    df_copy = df.copy()
    start = _ensure_datetime(df_copy, start_column)
    end = _ensure_datetime(df_copy, end_column)
    if start is None or end is None:
        return df_copy
    df_copy[new_column] = (end - start).dt.days
    return df_copy


def add_days(df, **kwargs):
    column = kwargs.get('column', '')
    days = kwargs.get('days', 0)
    new_column = kwargs.get('new_column', f'{column}_plus_{days}') if column else f'plus_{days}_days'
    df_copy = df.copy()
    dt_series = _ensure_datetime(df_copy, column)
    if dt_series is None:
        return df_copy
    df_copy[new_column] = dt_series + pd.Timedelta(days=days)
    return df_copy


def subtract_days(df, **kwargs):
    column = kwargs.get('column', '')
    days = kwargs.get('days', 0)
    new_column = kwargs.get('new_column', f'{column}_minus_{days}') if column else f'minus_{days}_days'
    df_copy = df.copy()
    dt_series = _ensure_datetime(df_copy, column)
    if dt_series is None:
        return df_copy
    df_copy[new_column] = dt_series - pd.Timedelta(days=days)
    return df_copy
