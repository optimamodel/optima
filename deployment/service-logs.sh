#! /usr/bin/env bash

# I view the logs of a systemd service on Athena using fabric, see fabfile.py:service_logs
fab service_logs:$1 $2
