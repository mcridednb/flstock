#!/bin/bash

groupadd -r -g 1008 git-users

usermod -aG git-users airflow

exec /entrypoint "$@"
