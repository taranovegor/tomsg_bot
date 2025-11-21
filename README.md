# tomsg_bot
Easily turn comments into messages with this bot

![GitHub License](https://img.shields.io/github/license/taranovegor/tomsg_bot)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/taranovegor/tomsg_bot/publish.yaml)
[![Docker Image Version](https://img.shields.io/docker/v/taranovegor/tomsg_bot?logo=docker)](https://hub.docker.com/r/taranovegor/tomsg_bot)

## Set up
### Requirements
- [Docker](https://docs.docker.com/engine/install/)
- [docker-compose](https://docs.docker.com/compose/gettingstarted/)

### Configuration
Copy an instance of the environment file and save it as a file `.env`
```shell
cp .env.dist .env
```
... and configure as you need. A full list of required environment variables can be found in the **[Environment Variables Overview](#environment-variables)** section.

Build or pull docker images of application
```shell
make container-build
```
```shell
make container-pull
```

### Launch
Run the application using the Make tool
```shell
make start
```

## Environment variables

| **Variable**                    | **Description**                                                                                                                             |
|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `DEBUG`                         | Indicates whether the application is running in debug mode (`true/false`).                                                                  |
| `LOG_LEVEL`                     | Defines the logging level for the application. Possible values: `CRITICAL`, `FATAL`, `ERROR`, `WARN`, `WARNING`, `INFO`, `DEBUG`, `NOTSET`. |
| `TELEGRAM_BOT_TOKEN`            | Telegram bot token required for the bot to operate.                                                                                         |
| `TELEGRAM_BASE_URL`             | Optional custom Telegram API base URL. Use this if you are running the bot with a self-hosted Telegram API or a proxy.                      |
| `INSTAGRAM_VIDEO_PARSER_URL`    | Instagram video parser address.                                                                                                             |
| `INSTAGRAM_ENCRYPTION_KEY`      | Encryption key for sensitive data.                                                                                                          |
| `REDDIT_CLIENT_ID`              | Reddit API Client ID used for API authentication.                                                                                           |
| `REDDIT_CLIENT_SECRET`          | Reddit API Client Secret for secure API access.                                                                                             |
| `REDDIT_OWNER_USERNAME`         | Owner's Reddit username for identification purposes in operations.                                                                          |
| `TIKTOK_VIDEO_RESOURCE_URL`     | URL template for accessing TikTok video files, with %s as a placeholder for the video ID.                                                   | 
| `TIKTOK_THUMBNAIL_RESOURCE_URL` | URL template for accessing TikTok video thumbnails, with %s as a placeholder for the video ID.                                              |
| `GA_MEASUREMENT_ID`             | Unique identifier for the Google Analytics property used to track and measure app activity.                                                 |
| `GA_SECRET`                     | Secret key used for authenticating requests to Google Analytics API, ensuring secure data handling.                                         |
| `GA_UID_SALT`                   | The salt used for securely hashing user and client identifiers before sending to Google Analytics.                                          |
| `VK_THUMBNAIL_URL`              | Static URL for VK clips thumbnails used in the application.                                                                                 |
| `YOUTUBE_API_KEY`               | API key for accessing the YouTube Data API, used to retrieve video information.                                                             |
