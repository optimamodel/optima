#!/bin/bash
# Run this first to start the Optima server.
# Assumes redis database is already running (check with "ps -ef | grep redis")
# Version: 2016sep01

cd ..
python bin/run_server.py 8080
