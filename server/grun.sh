#!/bin/bash

if [ ! -f "src/config.py" ]; then
  cp config.example.py config.py
fi

./sandbox.sh

pip install gunicorn

gunicorn --workers 2 --error-logfile=- --log-file=- --bind 127.0.0.1:5000 --log-level debug api:app