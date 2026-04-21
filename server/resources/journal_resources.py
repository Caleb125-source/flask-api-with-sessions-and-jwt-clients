from flask import request, session
from flask_restful import Resource
from models import JournalEntry, User
from app import db


def get_current_user():
    """Helper — returns the logged-in User or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


class JournalEntryList(Resource):
    """
    GET  /entries  — paginated list of the current user's entries
    POST /entries  — create a new entry
    """

    def get(self):
        user = get_current_user()
        if not user:
            return {"error": "Not authenticated."}, 401

        # Pagination
        page     = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        per_page = min(per_page, 50)  # cap at 50 to prevent abuse

        pagination = (
            JournalEntry.query
            .filter_by(user_id=user.id)
            .order_by(JournalEntry.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return {
            "entries":     [e.to_dict() for e in pagination.items],
            "total":       pagination.total,
            "pages":       pagination.pages,
            "current_page": pagination.page,
            "has_next":    pagination.has_next,
            "has_prev":    pagination.has_prev,
        }, 200

    def post(self):
        user = get_current_user()
        if not user:
            return {"error": "Not authenticated."}, 401

        data = request.get_json()
        if not data or not all(k in data for k in ("title", "content")):
            return {"error": "title and content are required."}, 422

        try:
            entry = JournalEntry(
                title      = data["title"],
                content    = data["content"],
                mood       = data.get("mood"),
                is_private = data.get("is_private", True),
                user_id    = user.id,
            )
            db.session.add(entry)
            db.session.commit()
        except ValueError as e:
            return {"error": str(e)}, 422

        return entry.to_dict(), 201


class JournalEntryDetail(Resource):
    """
    PATCH  /entries/<id>  — update an entry (owner only)
    DELETE /entries/<id>  — delete an entry (owner only)
    """

    def _get_entry_for_user(self, entry_id):
        """Return the entry if it belongs to the logged-in user, else error tuple."""
        user = get_current_user()
        if not user:
            return None, ({"error": "Not authenticated."}, 401)

        entry = JournalEntry.query.get(entry_id)
        if not entry:
            return None, ({"error": "Entry not found."}, 404)

        # Ownership check — users cannot touch other users' entries
        if entry.user_id != user.id:
            return None, ({"error": "Forbidden."}, 403)

        return entry, None

    def patch(self, entry_id):
        entry, err = self._get_entry_for_user(entry_id)
        if err:
            return err

        data = request.get_json()
        if not data:
            return {"error": "No data provided."}, 422

        try:
            if "title"      in data: entry.title      = data["title"]
            if "content"    in data: entry.content    = data["content"]
            if "mood"       in data: entry.mood       = data["mood"]
            if "is_private" in data: entry.is_private = data["is_private"]
            db.session.commit()
        except ValueError as e:
            return {"error": str(e)}, 422

        return entry.to_dict(), 200

    def delete(self, entry_id):
        entry, err = self._get_entry_for_user(entry_id)
        if err:
            return err

        db.session.delete(entry)
        db.session.commit()
        return {}, 204