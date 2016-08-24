#! /usr/bin/env bash

ansible-playbook playbook.yml -t "rproxy,restart,$1" $2
