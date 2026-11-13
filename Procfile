web: python manage.py migrate && python manage.py load_initial_data && gunicorn craftykids.wsgi --timeout 300 --worker-class gthread --threads 4 --log-file -
