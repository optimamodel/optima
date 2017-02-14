# Copy this file to config.py
UPLOAD_FOLDER = '/tmp/uploads'
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
REDIS_URL = CELERY_BROKER_URL
MATPLOTLIB_BACKEND = "agg"
