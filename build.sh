
#!/usr/bin/env bash
set -o errexit

# Install project dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Create or update the online administrator account
python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

if not username or not password:
    raise RuntimeError("Admin username or password environment variable is missing!")

User = get_user_model()

user, created = User.objects.get_or_create(username=username)

user.is_staff = True
user.is_superuser = True
user.set_password(password)
user.save()

print("Admin account created successfully!" if created else "Admin account updated successfully!")
PY
