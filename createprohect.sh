# Make sure your virtual environment is activated (you should see (env) in your prompt)
# Create the Django project
django-admin startproject earthquake_warning

# Create the earthquake_app
cd earthquake_warning
python manage.py startapp earthquake_app

# Create the services directory
mkdir services
touch services/__init__.py
touch services/earthquake_data.py

# Create the templates directory
mkdir earthquake_app/templates
touch earthquake_app/templates/dashboard.html

# Create initial migration
python manage.py makemigrations
python manage.py migrate

# Create a superuser for admin access
python manage.py createsuperuser