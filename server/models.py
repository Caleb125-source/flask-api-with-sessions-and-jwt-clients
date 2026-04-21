from app import db, bcrypt
from sqlalchemy.orm import validates


class User(db.Model):
    """Represents an authenticated user of the app."""
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    # Stores only the bcrypt hash — never the plaintext password
    _password_hash = db.Column(db.String(128), nullable=False)

    entries = db.relationship(
        "JournalEntry", back_populates="user", cascade="all, delete-orphan"
    )

    # Password helpers

    @property
    def password(self):
        """Block accidental reads of the hash."""
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, plaintext):
        """Hash and store the password when assigned."""
        self._password_hash = bcrypt.generate_password_hash(plaintext).decode("utf-8")

    def authenticate(self, plaintext):
        """Return True if plaintext matches the stored hash."""
        return bcrypt.check_password_hash(self._password_hash, plaintext)

    # Validation

    @validates("username")
    def validate_username(self, key, value):
        if not value or len(value.strip()) < 3:
            raise ValueError("Username must be at least 3 characters.")
        return value.strip()

    @validates("email")
    def validate_email(self, key, value):
        if "@" not in value:
            raise ValueError("Invalid email address.")
        return value.lower().strip()

    def to_dict(self):
        return {"id": self.id, "username": self.username, "email": self.email}

    def __repr__(self):
        return f"<User {self.username}>"


class JournalEntry(db.Model):
    """A single journal entry owned by a user."""
    __tablename__ = "journal_entries"

    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    mood       = db.Column(db.String(50), nullable=True)   # extra custom field
    is_private = db.Column(db.Boolean, default=True)        # extra custom field
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user    = db.relationship("User", back_populates="entries")

    # Validation

    @validates("title")
    def validate_title(self, key, value):
        if not value or len(value.strip()) == 0:
            raise ValueError("Title cannot be blank.")
        return value.strip()

    @validates("content")
    def validate_content(self, key, value):
        if not value or len(value.strip()) == 0:
            raise ValueError("Content cannot be blank.")
        return value.strip()

    def to_dict(self):
        return {
            "id":         self.id,
            "title":      self.title,
            "content":    self.content,
            "mood":       self.mood,
            "is_private": self.is_private,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user_id":    self.user_id,
        }

    def __repr__(self):
        return f"<JournalEntry {self.title[:30]}>"