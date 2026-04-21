# Journal App — Flask Backend

A secure RESTful Flask API for a personal journal / productivity tool.
Users can register, log in, and manage private journal entries.
Authentication uses **server-side sessions**

---

## Installation

### Prerequisites
- Python 3.8.13+
- `pipenv` (`pip install pipenv`)

### Steps

```bash
# 1. Clone the repo and navigate to the server folder
git clone <your-repo-url>
cd productivity-tool/server

# 2. Install dependencies
pipenv install

# 3. Activate the virtual environment
pipenv shell

# 4. Set environment variables (edit as needed)
cp .env.example .env

# 5. Apply database migrations
flask db upgrade

# 6. (Optional) Seed the database with example data
python seed.py
```

---

## Running the server

```bash
flask run --port 5555
# or
python app.py
```

The API will be available at `http://localhost:5555`.

---

## API Endpoints

### Authentication

| Method | Path | Description | Auth required |
|--------|------|-------------|---------------|
| POST | `/signup` | Register a new user | No |
| POST | `/login` | Log in and start a session | No |
| DELETE | `/logout` | End the current session | Yes |
| GET | `/me` | Return the logged-in user | Yes |

**POST `/signup`** body:
```json
{ "username": "alice", "email": "alice@example.com", "password": "secret123" }
```

**POST `/login`** body:
```json
{ "username": "alice", "password": "secret123" }
```

---

### Journal Entries

| Method | Path | Description | Auth required |
|--------|------|-------------|---------------|
| GET | `/entries` | List own entries (paginated) | Yes |
| POST | `/entries` | Create a new entry | Yes |
| PATCH | `/entries/<id>` | Update an entry (owner only) | Yes |
| DELETE | `/entries/<id>` | Delete an entry (owner only) | Yes |

**GET `/entries`** query params:
- `page` (int, default 1)
- `per_page` (int, default 10, max 50)

**POST / PATCH `/entries`** body fields:
```json
{
  "title":      "My first entry",
  "content":    "Today was a good day...",
  "mood":       "happy",
  "is_private": true
}
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No content (successful delete/logout) |
| 401 | Unauthenticated |
| 403 | Forbidden (wrong owner) |
| 404 | Not found |
| 422 | Validation error |