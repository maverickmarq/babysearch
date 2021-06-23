#!/bin/sh
exec gunicorn app:app \
     -w 2 -t 120 \
     -b 0.0.0.0:8000 \
     --max-requests 1000 \
     --log-level=debug
