from flask import request, session
from flask_restful import Resource
from models import User
from app import db


class Signup(Resource):
    """POST /signup — create a new user account."""

    def post(self):
        data = request.get_json()

        # Validate required fields are present
        if not data or not all(k in data for k in ("username", "email", "password")):
            return {"error": "username, email, and password are required."}, 422

        # Check for duplicate username or email
        if User.query.filter_by(username=data["username"]).first():
            return {"error": "Username already taken."}, 422
        if User.query.filter_by(email=data["email"]).first():
            return {"error": "Email already registered."}, 422

        try:
            user = User(username=data["username"], email=data["email"])
            user.password = data["password"]   # triggers the bcrypt setter
            db.session.add(user)
            db.session.commit()
        except ValueError as e:
            return {"error": str(e)}, 422

        # Log the user in immediately after signup
        session["user_id"] = user.id
        return user.to_dict(), 201


class Login(Resource):
    """POST /login — authenticate an existing user."""

    def post(self):
        data = request.get_json()

        if not data or not all(k in data for k in ("username", "password")):
            return {"error": "username and password are required."}, 422

        user = User.query.filter_by(username=data["username"]).first()

        if not user or not user.authenticate(data["password"]):
            return {"error": "Invalid username or password."}, 401

        session["user_id"] = user.id
        return user.to_dict(), 200


class Logout(Resource):
    """DELETE /logout — clear the server-side session."""

    def delete(self):
        # Remove the user_id key — session effectively ends
        session.pop("user_id", None)
        return {}, 204


class CheckSession(Resource):
    """GET /me — return the currently logged-in user, or 401."""

    def get(self):
        user_id = session.get("user_id")

        if not user_id:
            return {"error": "Not authenticated."}, 401

        user = User.query.get(user_id)
        if not user:
            session.pop("user_id", None)
            return {"error": "User not found."}, 401

        return user.to_dict(), 200