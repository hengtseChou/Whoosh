from application import create_app
from application.config import ENV


if ENV == "debug":
    DEBUG = True
else:
    DEBUG = False

app = create_app()

if __name__ == "__main__":
    if DEBUG:
        app.run(debug=True)
    else:
        app.run()
