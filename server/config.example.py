# Copy this file to config.py

import os
import multiprocessing
import math

SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI','postgresql+psycopg2://optima:optima@vladh.net:5432/optima')
SECRET_KEY = os.getenv('SECRET_KEY','F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER','/tmp/uploads')
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/4') # Shortcut for setting both the celery broker and result backend cache
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL',REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND',REDIS_URL)
CELERY_ACCEPT_CONTENT = os.getenv('CELERY_ACCEPT_CONTENT','pickle,json,msgpack,yaml').split(',') # Comma separated list
SQLALCHEMY_TRACK_MODIFICATIONS = bool(os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS',False))
MATPLOTLIB_BACKEND = os.getenv('MATPLOTLIB_BACKEND',"agg")
SERVER_PORT = int(os.getenv('PORT', 8080))
WORKERS = int(os.getenv('WORKERS',min(math.ceil(multiprocessing.cpu_count()/2.0),8))) # By default use half the CPUs, up to a maximum of 8
BIND_IP = os.getenv('BIND_IP',"0.0.0.0")  # Bind address for gunicorn. '0.0.0.0' allows external connections e.g. from a remote nginx, while '127.0.0.1' allows only local access (e.g., a locally running nginx)

# GUNICORN VARIABLES - the variable names below are special and recognized by `gunicorn`
bind = '%s:%d' % (BIND_IP,SERVER_PORT)
workers = WORKERS
timeout = 60  # Increase BE timeout for long running RPCs

# To use gunicorn, run 'gunicorn --config config.py server.api:app' 
# Unfortunately, the WSGI app 'server.api:app' cannot be set in this file
