#! /usr/bin/env bash

# I run the Ansible playbook against athena. Only the rproxy and the specified
# service are deployed, to minimise disruption of other Optima installations.
ansible-playbook playbook.yml -t "rproxy,$1" $2 $3

# I regenerate the Optima front end on Athena using fabric.
# See fabfile.py:optima_regenerate_frontend
fab optima_regenerate_frontend:$1
