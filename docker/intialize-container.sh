#!/bin/bash

mkdir -p /opt/metric

# Intialize Database
if [ -d /opt/metric/db ]; then
    echo Database already initialized. If you want to re-create, delete the directory on
    echo your host machine that is mapped to /opt/metric/db and re-run.
    exit 1
else
    mkdir -p /opt/metric/db
    chown postgres:postgres /opt/metric/db
    /etc/init.d/postgresql start
    su postgres -c "psql --command \"CREATE USER oss with SUPERUSER PASSWORD 'oss';\""
    su postgres -c "psql --command \"CREATE TABLESPACE oss_tablespace OWNER oss LOCATION '/opt/metric/db';\""
    su postgres -c "psql --command \"CREATE DATABASE ossdb OWNER oss TABLESPACE oss_tablespace;\""
fi

if [ -d /opt/metric/app/project]; then
    echo Project already initialized. If you want to re-build, delete the 'project' directory on
    echo your host machine that is mapped to /opt/metric/app and re-run.
    exit 1
else
    mkdir -p /opt/metric/app
    cd /opt/metric/app
    python3 -mvenv project
    source project/bin/activate
fi
