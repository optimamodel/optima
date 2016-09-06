#! /usr/bin/env bash

# I restart a service on Athena using fabric, see fabfile.py:optima_restart
fab optima_restart:$1 $2
