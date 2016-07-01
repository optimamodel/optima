SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://optima:optima@localhost:5432/optima_cdc'
SECRET_KEY = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'
UPLOAD_FOLDER = '/tmp/uploads'
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
REDIS_URL = CELERY_BROKER_URL
MATPLOTLIB_BACKEND = "agg"
