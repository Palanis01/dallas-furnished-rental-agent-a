#!/bin/bash
set -e
exec gunicorn -w 2 -k uvicorn.workers.UvicornWorker app.main:app
