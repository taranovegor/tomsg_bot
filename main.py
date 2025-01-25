from core import app


def main():
    print(f"🐓 {app.name()}! version: {app.version()}")
    app.init().run()


if __name__ == "__main__":
    main()
