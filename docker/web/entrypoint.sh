#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for PostgreSQL..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

service cron start

# Perform an initial configuration (if needed)
python manage.py createsuperuser --noinput
yarnpkg --non-interactive
python manage.py collectstatic --noinput
#python manage.py makemigrations
python manage.py migrate

exec "$@"
