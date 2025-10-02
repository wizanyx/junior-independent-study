from . import create_app
from .config import get_settings


def main() -> None:
    s = get_settings()
    app = create_app(s)
    app.run(port=s.api_port, debug=(s.flask_env == "development"))


if __name__ == "__main__":  # pragma: no cover
    main()
