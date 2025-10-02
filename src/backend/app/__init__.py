from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def hello() -> str:
        return "Hello World!"

    return app
