#!/bin/sh

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
    sleep 0.1
done
echo "PostgreSQL is up and running!"

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z $REDIS_HOST $REDIS_PORT; do
    sleep 0.1
done
echo "Redis is up and running!"

# Change to the correct directory
cd /app/earthquake_warning

# Run Django management commands
echo "Running Django management commands..."
python manage.py collectstatic --noinput 
python manage.py migrate

# Create superuser if not exists
echo "Creating superuser..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'suabiut@gmail.com', 'admin1234')
    print("Superuser created with username: admin and password: admin1234")
else:
    print("Superuser already exists.")
EOF

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn earthquake_warning.wsgi:application --bind 0.0.0.0:8000
