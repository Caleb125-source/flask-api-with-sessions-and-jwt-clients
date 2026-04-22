from flask import request, session
from flask_restful import Resource
from models import User
from app import db


class Signup(Resource):
    """POST /signup — register a new user."""

    def post(self):
        data = request.get_json()

        if not data or not all(k in data for k in ("username", "password")):
            return {"errors": ["username and password are required."]}, 422

        if User.query.filter_by(username=data["username"]).first():
            return {"errors": ["Username already taken."]}, 422

        # handle optional password_confirmation from the frontend
        if "password_confirmation" in data:
            if data["password"] != data["password_confirmation"]:
                return {"errors": ["Passwords do not match."]}, 422

        try:
            user = User(
                username=data["username"],
                email=data.get("email", ""),
            )
            user.password = data["password"]
            db.session.add(user)
            db.session.commit()
        except ValueError as e:
            return {"errors": [str(e)]}, 422

        session["user_id"] = user.id
        return user.to_dict(), 201


class Login(Resource):
    """POST /login — authenticate an existing user."""

    def post(self):
        data = request.get_json()

        if not data or not all(k in data for k in ("username", "password")):
            return {"errors": ["username and password are required."]}, 422

        user = User.query.filter_by(username=data["username"]).first()
        if not user or not user.authenticate(data["password"]):
            return {"errors": ["Invalid username or password."]}, 401

        session["user_id"] = user.id
        return user.to_dict(), 200


class Logout(Resource):
    """DELETE /logout — clear the session."""

    def delete(self):
        session.pop("user_id", None)
        return {}, 204


class CheckSession(Resource):
    """GET /check_session — return the currently logged-in user."""

    def get(self):
        user_id = session.get("user_id")
        if not user_id:
            return {"errors": ["Not authenticated."]}, 401

        user = User.query.get(user_id)
        if not user:
            session.pop("user_id", None)
            return {"errors": ["User not found."]}, 401

        return user.to_dict(), 200