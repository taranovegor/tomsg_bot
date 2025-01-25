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

| **Variable**            | **Description**                                                            |
|-------------------------|----------------------------------------------------------------------------|
| `DEBUG`                 | Indicates whether the application is running in debug mode (`true/false`). |
| `TELEGRAM_BOT_TOKEN`    | Telegram bot token required for the bot to operate.                        |
