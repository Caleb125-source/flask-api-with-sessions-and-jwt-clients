from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_restful import Api

# Initialise extensions (not bound to an app yet)
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()


def create_app():
    """Application factory — returns a configured Flask app instance."""
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Bind extensions to this app instance
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # Register all API resources
    api = Api(app)

    # Import here to avoid circular imports
    from resources.auth_resources import (
        Signup, Login, Logout, CheckSession
    )
    from resources.journal_resources import (
        JournalEntryList, JournalEntryDetail
    )

    # Auth routes
    api.add_resource(Signup,       "/signup")
    api.add_resource(Login,        "/login")
    api.add_resource(Logout,       "/logout")
    api.add_resource(CheckSession, "/me")

    # Journal entry routes
    api.add_resource(JournalEntryList,   "/entries")
    api.add_resource(JournalEntryDetail, "/entries/<int:entry_id>")

    return app


# Allow running directly with `python app.py` or `flask run`
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5555)