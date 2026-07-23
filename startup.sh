#!/bin/bash
set -e

python manage.py migrate --noinput

python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
if email and password and not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(email=email, username=email.split('@')[0], password=password)
    print(f'Superuser created: {email}')
"

python manage.py shell -c "
import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.module_loading import import_string

print(f'  [s3test] DEFAULT_FILE_STORAGE = {settings.DEFAULT_FILE_STORAGE}')
print(f'  [s3test] storage class = {type(default_storage).__name__}')

resolved_cls = import_string(settings.DEFAULT_FILE_STORAGE)
print(f'  [s3test] resolved storage class = {resolved_cls.__module__}.{resolved_cls.__name__}')
if 's3' not in resolved_cls.__name__.lower():
    print(f'  [s3test] >>> WARNING: resolved backend is NOT S3 (S3 uploads will break!) <<<')

try:
    print(f'  [s3test] underlying = {type(default_storage._wrapped).__name__}')
except:
    pass
print(f'  [s3test] AWS_S3_ENDPOINT_URL = {os.environ.get(\"SUPABASE_S3_ENDPOINT\", \"NOT SET\")}')
print(f'  [s3test] AWS_STORAGE_BUCKET_NAME = {os.environ.get(\"SUPABASE_BUCKET\", \"NOT SET\")}')

try:
    path = default_storage.save('startup_test.txt', ContentFile(b'S3 test file'))
    print(f'  [s3test] UPLOAD OK: saved to {path}')
    content = default_storage.open(path).read()
    print(f'  [s3test] READ OK: content = {content.decode()}')
    
    try:
        dirs, files = default_storage.listdir('')
        print(f'  [s3test] BUCKET LISTING: dirs={dirs}, files={files}')
    except Exception as e:
        print(f'  [s3test] LISTDIR ERROR (non-fatal): {e}')
    
    default_storage.delete(path)
    print(f'  [s3test] DELETE OK')
    print(f'  [s3test] S3 is WORKING correctly')
except Exception as e:
    import traceback
    print(f'  [s3test] S3 ERROR: {e}')
    traceback.print_exc()
    print(f'  [s3test] FILES WILL BE LOST on deploy/sleep!')
"

exec gunicorn cleanslate.wsgi --log-file -
