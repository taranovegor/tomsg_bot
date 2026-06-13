from bootstrap import app


def main():
    print(f"🐓 {app.name()}! version: {app.version()}", flush=True)
    app.init().run()


if __name__ == "__main__":
    main()
