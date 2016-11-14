Introduction
====

This describes the server API. For installation instructions, see the README file at the root directory level.

API documentation
===

Once you have configured the api server and nginx, you can browse api endpoints at http://optima.dev/api/spec.html (click show/hide)

These APIs allow front-end to get current user or login a user

Celery
===

In order to run celery on your local machine, you need to have redis installed.

On Ubuntu:
---

`sudo apt-get install redis-server`

On MacOS X:
---

`brew install redis`

then check

`brew info redis`

for the information how to start Redis on your system.

Or (if no brew) follow [these instructions](http://jasdeep.ca/2012/05/installing-redis-on-mac-os-x/)

Ensure that your server/config.py file has settings for Redis (provided in server/config.example.py)

Then, from the <root>/server optima directory, launch `./celery.sh`

/!\ Note: whenever you make a change that could affect a celery task, you need to restart it manually.


# Example `config.py`

```
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://optima:optima@localhost:5432/optima'
SECRET_KEY = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'
UPLOAD_FOLDER = '/tmp/uploads'
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
REDIS_URL = CELERY_BROKER_URL
MATPLOTLIB_BACKEND = "agg"
```

# Installing the server
```
pip install -r localrequirements
```