#!/bin/bash

source ./env.sh

if [ ! -f "config.py" ]; then
  cp config.example.py config.py
fi

migrate upgrade postgresql://optima:optima@localhost:5432/optima db/

python api.py

