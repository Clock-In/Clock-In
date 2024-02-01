#!/usr/bin/env bash

# Wait for db to be ready
if [[ "${DB_HOST:0:1}" != '/' ]]; then 
    echo 'Waiting for DB to start at network address.'
    while ! nc -z "$DB_HOST" "$DB_PORT" ; do
        sleep 0.1
    done
fi
echo 'DB started, continuing.'

echo 'Running migrations...'
python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput
echo 'Starting server...'
python3 manage.py runserver 0.0.0.0:8000
