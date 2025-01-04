# For Python 3
python3 -m venv env

# Activate the virtual environment
# On Linux/Mac:
source env/bin/activate
# On Windows:
# env\Scripts\activate

# Verify it's activated - should show Python path in your env directory
which python

# Create requirements.txt with initial dependencies
cat > requirements.txt << 'EOL'
Django>=3.2.7
psycopg2-binary>=2.9.1
requests>=2.26.0
python-dotenv>=0.19.0
gunicorn>=20.1.0
redis>=4.0.0
celery>=5.2.0
django-cors-headers>=3.10.0
djangorestframework>=3.12.0
EOL

# Install the requirements
pip install -r requirements.txt

# Freeze the exact versions into requirements.txt
pip freeze > requirements.txt