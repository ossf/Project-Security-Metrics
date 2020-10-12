FROM ubuntu:20.04

LABEL schema-version="1.0"
LABEL name="Metric Project - Analysis Container"
LABEL maintainer="Open Source Security Foundation - github.com/ossf"
LABEL vendor="Linux Foundation"
LABEL build-date="2020-09-13T00:00:00.00Z"
LABEL version="0.0.2"

# Overridable Arguments
ARG DOTNET_VERSION="3.1"
ARG APPLICATION_INSPECTOR_VERSION="1.2.62"
ARG OSSGADGET_VERSION="0.1.239"
ARG CODEQL_VERSION="v2.2.5"
ARG GO_VERSION="1.15"

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Los_Angeles

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

SHELL ["/bin/bash", "-c"]

# Core utilities
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
            build-essential \
            fakeroot \
            devscripts \
            curl \
            git \
            make \
            wget \
            mc \
            unzip \
            nano \
            vim \
            dos2unix \
            sed \
            gcc \
            libpq-dev \
            make \
            apt-transport-https \
            python3.8 \
            python3-pip \
            python3-setuptools \
            python3-dev \
            python3-wheel \
            python-is-python3 \
            jq \
            gnupg \
            g++ \
            make \
            gcc \
            apt-utils \
            file \
            gettext \
            sqlite3 \
            software-properties-common

##################################
####### Install Core Tools #######
##################################

# Install .NET Core
RUN cd /tmp && \
    wget -q https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    add-apt-repository universe && \
    apt-get update && \
    rm packages-microsoft-prod.deb && \
    apt-get install -y dotnet-sdk-${DOTNET_VERSION} && \
    rm -rf /var/lib/apt/lists/*

# Download Go
RUN cd /opt && \
    wget https://golang.org/dl/go$GO_VERSION.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go$GO_VERSION.linux-amd64.tar.gz && \
    rm go$GO_VERSION.linux-amd64.tar.gz

# Install DevSkim
RUN dotnet tool install --global Microsoft.CST.DevSkim.CLI

# Install Node.js
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get update && \
    apt-get install -y nodejs

# Install NodeJsScan
RUN pip3 install --disable-pip-version-check nodejsscan

# Install CppCheck
RUN apt-get install -y cppcheck

# Download CodeQL and queries
RUN cd /opt && \
    wget https://github.com/github/codeql-cli-binaries/releases/download/$CODEQL_VERSION/codeql-linux64.zip && \
    unzip codeql-linux64.zip && \
    rm codeql-linux64.zip && \
    git clone https://github.com/github/codeql codeql-queries && \
    git clone https://github.com/github/codeql-go codeql-queries-go

# Install Lizard (code complexity analyzer)
RUN pip3 install --disable-pip-version-check lizard

# Install SCC (line of code calcaulator)
RUN cd /opt && \
    wget https://github.com/boyter/scc/releases/download/v2.12.0/scc-2.12.0-i386-unknown-linux.zip && \
    unzip scc-2.12.0-i386-unknown-linux.zip && \
    mv scc /usr/local/bin && \
    rm scc-2.12.0-i386-unknown-linux.zip

# Install Brakeman
RUN apt-get install -y ruby
RUN cd /opt && \
    git clone --depth 1 git://github.com/presidentbeef/brakeman.git && \
    cd brakeman && \
	gem build brakeman.gemspec && \
	gem install brakeman-*.gem

# Install Graudit
RUN cd /opt && \
    git clone --depth 1 https://github.com/wireghoul/graudit

# Install OSS Gadget
RUN cd /opt && \
    wget -q https://github.com/microsoft/OSSGadget/releases/download/v${OSSGADGET_VERSION}/OSSGadget_linux_${OSSGADGET_VERSION}.zip -O OSSGadget.zip && \
    unzip OSSGadget.zip && \
    rm OSSGadget.zip && \
    mv OSSGadget_linux_${OSSGADGET_VERSION} OSSGadget && \
    cd OSSGadget && \
    find . -name 'oss-*' -exec file {} \; | grep ELF | cut -d: -f1 | xargs -n1 -I{} chmod a+x {}

# ApplicationInspector
RUN cd /opt && \
    wget -q https://github.com/microsoft/ApplicationInspector/releases/download/v${APPLICATION_INSPECTOR_VERSION}/ApplicationInspector_linux_${APPLICATION_INSPECTOR_VERSION}.zip -O ApplicationInspector.zip && \
    unzip ApplicationInspector.zip && \
    rm ApplicationInspector.zip && \
    mv ApplicationInspector_linux_${APPLICATION_INSPECTOR_VERSION} ApplicationInspector && \
    cd ApplicationInspector && \
    chmod a+x ./ApplicationInspector.CLI

#####################################
####### Install Scanner Tools #######
#####################################

# Install Scanner Dependencies
RUN pip3 install azure-storage-queue \
        requests \
        PyGithub \
        requests-cache \
        packageurl-python \
        django

########################
####### Finalize #######
########################

# Set up the path
RUN echo "export PATH=/opt/codeql:/opt/brakeman:/opt/OSSGadget:/opt/ApplicationInspector:$PATH" >> /root/.bashrc
ENV PATH="/opt/codeql:/opt/brakeman:/opt/OSSGadget:/opt/ApplicationInspector:${PATH}"

# copy project
COPY docker/worker/orchestrator.py .
COPY docker/worker/config.json .
COPY jobs/docker-scanner/processors ./processors
COPY docker/worker/entrypoint.sh .
RUN dos2unix ./entrypoint.sh

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
