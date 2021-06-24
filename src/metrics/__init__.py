import logging

from .Base import BaseJob
from .BestPractices import RefreshBestPractices
from .GitHubIssueTrend import RefreshGithubIssueTrend
from .GithubProjectReleases import RefreshGithubProjectReleases
from .LibrariesIO import RefreshLibrariesIO
from .Scorecard import RefreshScorecard
from .SecurityReviews import RefreshSecurityReviews

logging.basicConfig(level=logging.INFO)
