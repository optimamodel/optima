#! /usr/bin/env bash

ansible-playbook playbook.yml -t "rproxy,$1" $2 $3
fab service_regenerate_frontend:$1
