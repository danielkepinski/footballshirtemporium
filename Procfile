web: gunicorn myshop.wsgi:application --log-file -
worker: celery -A myshop worker --loglevel=info