# tomsg_bot
Easily turn comments and posts into readable Telegram messages.

![GitHub License](https://img.shields.io/github/license/taranovegor/tomsg_bot)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/taranovegor/tomsg_bot/publish.yaml)
[![Docker Image Version](https://img.shields.io/docker/v/taranovegor/tomsg_bot?logo=docker)](https://hub.docker.com/r/taranovegor/tomsg_bot)
[![GHCR](https://img.shields.io/badge/ghcr.io-tomsg__bot-2496ED?logo=github)](https://github.com/taranovegor/tomsg_bot/pkgs/container/tomsg_bot)

Send the bot a link to a supported social-media post or comment, and it replies with the
content (text, media, author, metrics) as a native Telegram message. Works in private chats
and via inline queries.

## Supported platforms
Twitter / X, Instagram, Reddit, YouTube (comments), TikTok, VK, Tumblr, Truth Social,
Habr, DTF & vc.ru (CMTT), redspecial & trashbox (bobs.pro).

Each platform is a self-contained parser in [`parsers/`](parsers/).

## Set up
### Requirements
- [Docker](https://docs.docker.com/engine/install/)
- [docker-compose](https://docs.docker.com/compose/gettingstarted/)

### Configuration
Copy the environment file and fill it in:
```shell
cp .env.dist .env
```
See the **[Environment variables](#environment-variables)** section for the full list.

Build or pull the docker image:
```shell
make container-build
# or
make container-pull
```

### Launch
```shell
make start
```

## Environment variables

| **Variable**                    | **Description**                                                                                    |
|---------------------------------|----------------------------------------------------------------------------------------------------|
| `DEBUG`                         | Indicates whether the application is running in debug mode (`true/false`).                         |
| `LOG_LEVEL`                     | Logging level. One of: `CRITICAL`, `FATAL`, `ERROR`, `WARN`, `WARNING`, `INFO`, `DEBUG`, `NOTSET`. |
| `TELEGRAM_BOT_TOKEN`            | Telegram bot token required for the bot to operate.                                                |
| `TELEGRAM_BASE_URL`             | Optional custom Telegram API base URL. Use this if you run a self-hosted Telegram API or a proxy.  |
| `INSTAGRAM_VIDEO_PARSER_URL`    | Instagram video parser address.                                                                    |
| `INSTAGRAM_ENCRYPTION_KEY`      | Encryption key used to pass URLs to the Instagram parser.                                          |
| `REDDIT_CLIENT_ID`              | Reddit API client ID used for API authentication.                                                  |
| `REDDIT_CLIENT_SECRET`          | Reddit API client secret for secure API access.                                                    |
| `REDDIT_APP_OWNER_USERNAME`     | Reddit username of the app owner, sent in the API User-Agent.                                      |
| `TIKTOK_VIDEO_RESOURCE_URL`     | URL template for TikTok video files, with `%s` as a placeholder for the video ID.                  |
| `TIKTOK_THUMBNAIL_RESOURCE_URL` | URL template for TikTok video thumbnails, with `%s` as a placeholder for the video ID.             |
| `TUMBLR_API_KEY`                | API key from your Tumblr application (required for API access).                                    |
| `GA_MEASUREMENT_ID`             | Google Analytics measurement ID used to track app activity.                                        |
| `GA_SECRET`                     | Secret used to authenticate requests to the Google Analytics API.                                  |
| `GA_UID_SALT`                   | Salt used to hash user/client identifiers before sending them to Google Analytics.                 |
| `VK_THUMBNAIL_URL`              | Static URL for VK clip thumbnails.                                                                 |
| `YOUTUBE_API_KEY`               | API key for the YouTube Data API, used to retrieve video information.                              |

## Development

Requires Python 3.13.

```shell
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Run the test suite, linter and formatter:
```shell
pytest
ruff check .
ruff format --check .
```

### Project layout
| Directory    | Responsibility                                                  |
|--------------|-----------------------------------------------------------------|
| `bootstrap/` | Composition root: config, DI container, entrypoint.             |
| `core/`      | Domain model, contracts (`ports/`) and the neutral `pipeline/`. |
| `parsers/`   | Source adapters — one auto-registered package per platform.     |
| `platforms/` | Delivery front-ends (Telegram).                                 |
| `infra/`     | Infrastructure: file download, media processing, analytics.     |
| `shared/`    | Cross-cutting helpers (HTML, URL, ids).                         |

## Contributing
Contributions are welcome. Please read [CONTRIBUTING.md](.github/CONTRIBUTING.md) and the
[Code of Conduct](.github/CODE_OF_CONDUCT.md). To report a vulnerability, see the
[Security policy](.github/SECURITY.md).

## License
[MIT](LICENSE) © Egor Taranov
