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

exec gunicorn cleanslate.wsgi --log-file -
