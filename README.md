# tomsg_bot
Easily turn comments into messages with this bot

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
| `INSTAGRAM_VIDEO_META_URL`      | URL template for retrieving Instagram video metadata, with `{0}` and `{1}` as placeholders.                                                 |
| `INSTAGRAM_VIDEO_STORAGE_URL`   | URL template for accessing stored Instagram videos, with `{0}` as a placeholder.                                                            |
| `INSTAGRAM_THUMBNAIL_URL`       | Static URL for Instagram video thumbnails used in the application.                                                                          |
| `REDDIT_CLIENT_ID`              | Reddit API Client ID used for API authentication.                                                                                           |
| `REDDIT_CLIENT_SECRET`          | Reddit API Client Secret for secure API access.                                                                                             |
| `REDDIT_OWNER_USERNAME`         | Owner's Reddit username for identification purposes in operations.                                                                          |
| `TIKTOK_VIDEO_RESOURCE_URL`     | URL template for accessing TikTok video files, with %s as a placeholder for the video ID.                                                   | 
| `TIKTOK_THUMBNAIL_RESOURCE_URL` | URL template for accessing TikTok video thumbnails, with %s as a placeholder for the video ID.                                              |
| `GA_MEASUREMENT_ID`             | Unique identifier for the Google Analytics property used to track and measure app activity.                                                 |
| `GA_SECRET`                     | Secret key used for authenticating requests to Google Analytics API, ensuring secure data handling.                                         |
| `VK_THUMBNAIL_URL`              | Static URL for VK clips thumbnails used in the application.                                                                                 |
