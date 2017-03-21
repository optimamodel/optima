#!/bin/bash
# Run this first to start the Optima server.
# Assumes redis database is already running (check with "ps -ef | grep redis")
# Version: 2016sep01

tput reset # Try to reset the screen, but don't worry if it fails
cd `dirname $0` # Make sure we're in the bin folder
cd .. # Main Optima folder
python bin/run_server.py 8080
