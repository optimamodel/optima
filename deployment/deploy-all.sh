#! /usr/bin/env bash

# I deploy the whole server.
# WARNING: This will possibly update the branches of all Optima installations!
ansible-playbook playbook.yml $1
