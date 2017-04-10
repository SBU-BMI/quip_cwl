#!/bin/bash 

nohup celery worker -A cwl_flask.celery -Q cwlqueue --uid 0 --gid 0 --loglevel=info &
python cwl_flask.py
