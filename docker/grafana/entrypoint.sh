#!/bin/bash

grafana-cli plugins install marcusolsson-dynamictext-panel
#grafana-cli plugins install jdbranham-diagram-panel
#grafana-cli plugins install yesoreyeram-boomtheme-panel

export GF_EXPLORE_ENABLED="false"
export GF_ALERTING_ENABLED="false"
export GF_AUTH_ANONYMOUS_ENABLED="true"
export GF_AUTH_ANONYMOUS_ORG_NAME="Open Source Security Foundation"
export GF_AUTH_ANONYMOUS_ROLE="Viewer"
export GF_AUTH_ANONYMOUS_HIDE_VERSION="true"
export GF_ALLOW_SIGN_UP="false"
export GF_REMOTE_CACHE_TYPE="redis"
export GF_REMOTE_CACHE_CONNSTR="addr=redis:6379,pool_size=20,db=1,ssl=insecure"
export GF_SERVER_ROOT_URL="%(protocol)s://%(domain)s:%(http_port)s/grafana/"

/run.sh