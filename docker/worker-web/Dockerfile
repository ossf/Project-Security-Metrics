# pull official base image
FROM python:3.8-buster

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
		yarnpkg

# install dependencies
RUN pip install --upgrade --use-feature=2020-resolver pip
COPY src/requirements.txt .
RUN pip install --use-feature=2020-resolver -r requirements.txt

# copy entrypoint.sh
COPY docker/worker-web/entrypoint.sh .
RUN dos2unix ./entrypoint.sh

# copy worker config
COPY docker/worker/config.json .

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
