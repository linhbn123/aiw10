#!/bin/bash
export FLASK_APP=./app/api/index.py
export FLASK_ENV=development
export ROOT_DIR=/data
export BOOT_USERNAME=github-bot
flask run -h 0.0.0.0 --debug
