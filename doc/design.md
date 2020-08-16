## Metrics

### Active Maintainers

Goal: Number of maintainers making a contribution to the repo over the last 1 year(?).
      Maybe a time series/moving-average or some kind.

Strategy:

For code, we can gather the list of the last 500 contributors via the GitHub API, or clone
the repository and search through the commit log.

Either way, we'll get name/e-mail pairs, which we can upsert and link