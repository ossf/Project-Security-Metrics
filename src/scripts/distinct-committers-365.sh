#!/bin/bash

PURL="$1"
GITHUB_URL=$(oss-find-source "$PURL" | sed 's/\t/ /' | cut -d" " -f2)

git clone --bare "$GITHUB_URL" work
cd work
SIX_MONTH=$(git log --pretty=format:"%ae" --since="1 year ago" | sort | uniq | wc -l)
ONE_YEAR=$(git log --pretty=format:"%ae" --since="3 years ago" | sort | uniq | wc -l)

curl -X POST -d '[{"package_url":"'$PURL'","operation":"replace","key":"metric.development.contributors.unique[365d]","values":[{"value":'$ONE_YEAR'}]},
				  {"package_url":"'$PURL'","operation":"replace","key":"metric.development.contributors.unique[90d]","values":[{"value":'$SIX_MONTH'}]}]' "$METRIC_API_ENDPOINT"

cd ..
rm -rf work
echo Operation complete.