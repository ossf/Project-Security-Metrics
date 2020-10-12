#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for PostgreSQL..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# Perform an initial configuration (if needed)
yarnpkg --non-interactive
python manage.py collectstatic --noinput
python manage.py migrate

exec "$@"
