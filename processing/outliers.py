import pandas as pd
import numpy as np


def detect_outliers_iqr(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    columns = kwargs.get('columns', None)
    factor = kwargs.get('factor', 1.5)
    action = kwargs.get('action', 'flag')

    target_cols = columns if columns else [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])]
    df_copy = df.copy()

    combined_mask = pd.Series(False, index=df_copy.index)

    for col in target_cols:
        if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
            continue

        col_data = df_copy[col].astype(float)
        q1 = col_data.quantile(0.25)
        q3 = col_data.quantile(0.75)
        iqr = q3 - q1

        lower = q1 - factor * iqr
        upper = q3 + factor * iqr

        col_mask = (col_data < lower) | (col_data > upper)
        combined_mask = combined_mask | col_mask

    if action == 'remove':
        df_copy = df_copy[~combined_mask].reset_index(drop=True)
    else:
        df_copy['_outlier_iqr'] = combined_mask

    return df_copy


def detect_outliers_zscore(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    columns = kwargs.get('columns', None)
    threshold = kwargs.get('threshold', 3)
    action = kwargs.get('action', 'flag')

    target_cols = columns if columns else [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])]
    df_copy = df.copy()

    combined_mask = pd.Series(False, index=df_copy.index)

    for col in target_cols:
        if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
            continue

        col_data = df_copy[col].astype(float)
        mean = col_data.mean()
        std = col_data.std()

        if std == 0 or pd.isna(std):
            continue

        z_scores = np.abs((col_data - mean) / std)
        col_mask = z_scores > threshold
        combined_mask = combined_mask | col_mask

    if action == 'remove':
        df_copy = df_copy[~combined_mask].reset_index(drop=True)
    else:
        df_copy['_outlier_zscore'] = combined_mask

    return df_copy
