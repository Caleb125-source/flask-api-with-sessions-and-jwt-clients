import os

class Config:
    # Secret key used to sign session cookies
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    # SQLite database stored in the server/ folder
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///journal_app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Required for cross-origin session cookies to work in the browser
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True

    # Set to True in production when serving over HTTPS
    SESSION_COOKIE_SECURE = False