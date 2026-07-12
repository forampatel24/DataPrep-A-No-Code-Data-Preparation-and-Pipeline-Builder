import os
import io
import pandas as pd
import json
from django.core.files.uploadedfile import UploadedFile


def read_csv_with_fallback(file):
    raw = file.read()
    encodings_to_try = ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'cp437', 'mac_roman', 'utf-16')
    for enc in encodings_to_try:
        try:
            decoded = raw.decode(enc)
            return pd.read_csv(io.StringIO(decoded))
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(
        'Could not read CSV file. The file encoding is not supported. '
        'Please save the file as UTF-8 encoded CSV.'
    )


def read_uploaded_file(file: UploadedFile) -> pd.DataFrame:
    ext = os.path.splitext(file.name)[1].lower()

    if ext == '.csv':
        return read_csv_with_fallback(file)
    elif ext == '.xlsx':
        return pd.read_excel(file, engine='openpyxl')
    elif ext == '.json':
        return pd.read_json(file)
    else:
        raise ValueError(f'Unsupported file format: {ext}')


def validate_uploaded_file(file: UploadedFile) -> tuple:
    ext = os.path.splitext(file.name)[1].lower()

    if ext not in ('.csv', '.xlsx', '.json'):
        return False, 'Unsupported file format. Please upload CSV, Excel (.xlsx), or JSON files.'

    if file.size == 0:
        return False, 'File is empty.'

    try:
        df = read_uploaded_file(file)
        file.seek(0)
        if df.empty:
            return False, 'File contains no data.'
        return True, df
    except Exception as e:
        return False, f'Could not read file: {str(e)}'
