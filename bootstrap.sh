#!/bin/bash
export FLASK_APP=./api/index.py
export FLASK_ENV=development
export ROOT_DIR=/data
export BOOT_USERNAME=github-bot
source $(pipenv --venv)/bin/activate
flask run -h 0.0.0.0
