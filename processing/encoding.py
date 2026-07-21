import pandas as pd
from sklearn.preprocessing import LabelEncoder


def label_encode(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_encoded') if column else 'encoded'
    df_copy = df.copy()
    if column not in df_copy.columns:
        return df_copy
    le = LabelEncoder()
    df_copy[new_column] = le.fit_transform(df_copy[column].astype(str))
    return df_copy



def one_hot_encode(df, **kwargs):
    column = kwargs.get('column', '')
    drop_first = kwargs.get('drop_first', False)
    prefix = kwargs.get('prefix', column)
    df_copy = df.copy()
    if column not in df_copy.columns:
        return df_copy
    dummies = pd.get_dummies(df_copy[column], prefix=prefix, drop_first=drop_first, dtype=int)
    df_copy = pd.concat([df_copy, dummies], axis=1)
    return df_copy


def ordinal_encode(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_ordinal') if column else 'ordinal'
    categories = kwargs.get('categories', [])
    df_copy = df.copy()
    if column not in df_copy.columns or not categories:
        return df_copy
    mapping = {cat: i for i, cat in enumerate(categories)}
    df_copy[new_column] = df_copy[column].astype(str).map(mapping).fillna(-1).astype(int)
    return df_copy


def binary_encode(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_binary') if column else 'binary'
    df_copy = df.copy()
    if column not in df_copy.columns:
        return df_copy
    unique_vals = df_copy[column].unique()
    for val in unique_vals:
        if pd.isna(val):
            continue
        bin_col = f'{new_column}_{val}'
        df_copy[bin_col] = (df_copy[column] == val).astype(int)
    return df_copy


def frequency_encode(df, **kwargs):
    column = kwargs.get('column', '')
    new_column = kwargs.get('new_column', f'{column}_freq') if column else 'freq'
    df_copy = df.copy()
    if column not in df_copy.columns:
        return df_copy
    freq = df_copy[column].value_counts()
    df_copy[new_column] = df_copy[column].map(freq)
    return df_copy
