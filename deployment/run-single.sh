#! /usr/bin/env bash

ansible-playbook playbook.yml -t "rproxy,$1" $2
