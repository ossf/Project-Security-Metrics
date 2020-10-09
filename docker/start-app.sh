#!/bin/bash

# Usage:
# 1. git clone https://github.com/ossf/Project-Security-Metrics
# 2. cd Project-Security-Metrics
# 3. docker build -t metric-dev:latest docker
# 4. docker run --rm -it --name metric-container --mount type=bind,source=$(pwd),target=/opt/metric/app/src metric-dev:latest docker/initialize-container.sh
# 5. docker run --rm -it --name metric-container --mount type=bind,source=$(pwd),target=/opt/metric/app/src metric-dev:latest docker/start-app.sh
# 6. Open http://host.docker.internal:8000

cd /opt/metric/app
source project/bin/activate
cd src
pip install -r requirements.txt
python manage.py migrate
yarn
python manage.py runserver
