import os

class Config:
    # Secret key used to sign session cookies
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    # SQLite database stored in the server/ folder
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///journal_app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sessions are server-side (not JWT) — cookies are HttpOnly
    SESSION_TYPE = "filesystem"