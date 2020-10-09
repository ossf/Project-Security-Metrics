from ubuntu:20.04

RUN export TZ="America/Los_Angeles"
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    	software-properties-common \
    	python3-venv \
    	python3-pip \
    	python3-setuptools \
        python3-dev \
        postgresql \
        postgresql-contrib \
        postgresql-client \
    	vim \
    	curl \
    	wget \
    	git \
    	build-essential \
    	unzip \
    	apt-transport-https \
    	g++ \
    	make \
    	gcc \
    	apt-utils \
    	file
