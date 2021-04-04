# pull official base image
FROM python:3.9.3-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install OS dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    	software-properties-common \
    	python3-venv \
    	python3-pip \
    	python3-setuptools \
        python3-dev \
		python3-wheel \
		build-essential \
		apt-utils \
		gcc \
		g++ \
		make \
		dos2unix \
		netcat \
		yarnpkg \
		cron

RUN service cron start

# install dependencies
RUN pip install --upgrade --use-feature=2020-resolver pip
COPY src/requirements.txt .
RUN pip install --use-feature=2020-resolver -r requirements.txt

# copy entrypoint.sh
COPY docker/web/entrypoint.sh .
RUN dos2unix ./entrypoint.sh

COPY docker/web/cron.daily /etc/cron.daily/openssf-reload-all
RUN dos2unix /etc/cron.daily/openssf-reload-all

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
