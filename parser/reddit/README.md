# Reddit Comment Parser
This package provides a Python library for parsing Reddit comments from a given Reddit URL. It authenticates with Reddit's API, retrieves comment data, processes the HTML content, and returns a structured representation of the comment, including metadata and metrics.

## Authentication
This package uses Reddit's OAuth2-based API for retrieving comment data. You'll need to provide:

- `client_id`: Your application's client ID from Reddit.
- `client_secret`: Your application's secret key from Reddit.
- `user_agent`: A unique string to identify your application (e.g., `os:app:version (by /u/ownername)`).

## Useful Resources for Reddit API Integration
- [Reddit API OAuth Documentation](https://www.reddit.com/dev/api/oauth/)
- [Reddit Data API Wiki](https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki)
