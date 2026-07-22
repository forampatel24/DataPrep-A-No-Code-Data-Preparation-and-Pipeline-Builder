import os
import tempfile
import pandas as pd
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def read_file_to_df(file_field):
    ext = os.path.splitext(file_field.name)[1].lower()
    if ext == '.csv':
        content = file_field.read()
        file_field.seek(0)
        raw = content.decode('utf-8-sig', errors='replace')
        return pd.read_csv(BytesIO(raw.encode('utf-8')))
    elif ext == '.xlsx':
        content = file_field.read()
        file_field.seek(0)
        return pd.read_excel(BytesIO(content), engine='openpyxl')
    elif ext == '.json':
        content = file_field.read()
        file_field.seek(0)
        return pd.read_json(BytesIO(content))
    raise ValueError(f'Unsupported format: {ext}')


def save_df_to_filefield(file_field, df, name):
    ext = os.path.splitext(name)[1].lower()
    if ext == '.csv':
        content = df.to_csv(index=False).encode('utf-8')
    elif ext == '.json':
        content = df.to_json(orient='records', date_format='iso').encode('utf-8')
    else:
        content = df.to_csv(index=False).encode('utf-8')
    file_field.save(name, ContentFile(content))


def storage_exists(path):
    return default_storage.exists(path)


def storage_open(path, mode='rb'):
    return default_storage.open(path, mode)


def download_to_temp(storage_path):
    if not default_storage.exists(storage_path):
        return None
    f = default_storage.open(storage_path, 'rb')
    suffix = os.path.splitext(storage_path)[1]
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(f.read())
    tmp.close()
    f.close()
    return tmp.name


def read_storage_to_df(storage_path):
    ext = os.path.splitext(storage_path)[1].lower()
    if not default_storage.exists(storage_path):
        return None
    content = default_storage.open(storage_path, 'rb').read()
    if ext == '.csv':
        raw = content.decode('utf-8-sig', errors='replace')
        return pd.read_csv(BytesIO(raw.encode('utf-8')))
    elif ext == '.xlsx':
        return pd.read_excel(BytesIO(content), engine='openpyxl')
    elif ext == '.json':
        return pd.read_json(BytesIO(content))
    return None


def delete_storage_path(path):
    if default_storage.exists(path):
        default_storage.delete(path)


def get_storage_file_list(prefix):
    from django.core.files.storage import default_storage as ds
    if hasattr(ds, 'listdir'):
        try:
            dirs, files = ds.listdir(prefix)
            return files
        except Exception:
            return []
    return []
