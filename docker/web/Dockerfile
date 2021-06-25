# pull official base image
FROM python:3.9.5-buster

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
		cron \
		apt-transport-https \
		ca-certificates \
		gnupg

# Google Cloud SDK
RUN sh -c "echo 'deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main' >> /etc/apt/sources.list.d/google-cloud-sdk.list"
RUN sh -c "curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -"
RUN apt-get update && \
    apt-get install -y google-cloud-sdk

# Start the cron service
RUN service cron start

# install dependencies
RUN pip install --upgrade pip
COPY src/requirements.txt .
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY docker/web/entrypoint.sh .
RUN dos2unix ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

COPY docker/web/cron.daily /etc/cron.daily/openssf-reload-all
RUN dos2unix /etc/cron.daily/openssf-reload-all
RUN chmod +x /etc/cron.daily/openssf-reload-all

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
