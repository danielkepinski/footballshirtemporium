web: gunicorn myshop.wsgi --log-file -
worker: celery -A myshop worker --loglevel=info --pool=solo --concurrency=1 --max-tasks-per-child=50
