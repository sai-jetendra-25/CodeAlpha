# 🔗 URL Shortener

A minimal Flask web application that shortens long URLs into 6-character codes, tracks click counts, and serves a clean browser UI alongside a JSON API.

---

## Features

- Shorten any URL to a compact alphanumeric code
- Redirect short codes to their original destination
- Click count tracking per short URL
- Deduplication — shortening the same URL twice returns the existing code
- Auto-prepends `https://` if no scheme is provided
- Recent-links history table in the UI

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database | SQLite via Flask-SQLAlchemy |
| CORS | Flask-CORS |
| Frontend | Vanilla JS + HTML (served by Flask) |

---

## Project Structure

```
.
├── app.py      # All models, routes, and embedded frontend
└── urls.db     # Auto-created SQLite database on first run
```

---

## Getting Started

### 1. Install dependencies

```bash
pip install flask flask-sqlalchemy flask-cors
```

### 2. Run the server

```bash
python app.py
```

The app starts on **http://localhost:5000** and creates `urls.db` automatically.

---

## Data Model

### URLMapping

| Field | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `short_code` | String(10) | Unique, indexed |
| `long_url` | Text | Required |
| `created_at` | DateTime | Auto-set by the database |
| `click_count` | Integer | Incremented on every redirect |

Short codes are 6-character strings drawn from `[a-zA-Z0-9]`, generated randomly and checked for uniqueness before being saved.

---

## API Reference

### `POST /shorten`

Shorten a long URL. Returns an existing mapping if the URL has been shortened before.

**Request body:**
```json
{ "long_url": "https://example.com/very/long/path" }
```

**Response `201 Created` (new) or `200 OK` (existing):**
```json
{
  "id": 1,
  "short_code": "aB3xYz",
  "long_url": "https://example.com/very/long/path",
  "created_at": "2025-09-01 10:00:00",
  "click_count": 0
}
```

---

### `GET /<code>`

Redirects to the original URL (`302 Found`) and increments `click_count`.

```
GET /aB3xYz  →  302 → https://example.com/very/long/path
```

Returns `404` if the code does not exist.

---

### `GET /urls`

Returns all stored mappings, newest first.

**Response:**
```json
[
  {
    "id": 1,
    "short_code": "aB3xYz",
    "long_url": "https://example.com/very/long/path",
    "created_at": "2025-09-01 10:00:00",
    "click_count": 4
  }
]
```

---

### `DELETE /urls/<code>`

Deletes a mapping by its short code.

**Response `200 OK`:**
```json
{ "message": "Deleted aB3xYz" }
```

Returns `404` if the code does not exist.

---

## Example Usage (curl)

```bash
# Shorten a URL
curl -X POST http://localhost:5000/shorten \
  -H "Content-Type: application/json" \
  -d '{"long_url": "https://example.com/some/long/path"}'

# Follow a short link (use -L to follow the redirect)
curl -L http://localhost:5000/aB3xYz

# List all URLs
curl http://localhost:5000/urls

# Delete a short URL
curl -X DELETE http://localhost:5000/urls/aB3xYz
```

---

## Configuration

| Setting | Default | Description |
|---|---|---|
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///urls.db` | Database path |
| `debug` | `True` | Flask debug mode |
| `port` | `5000` | Server port |

To use a different database (e.g. PostgreSQL), update `SQLALCHEMY_DATABASE_URI` in `app.py` and install the appropriate driver.

---

## Limitations & Future Work

- No authentication — anyone can shorten or delete URLs
- No expiry / TTL on short codes
- No custom alias support (codes are always random)
- No pagination on `GET /urls`
- Short codes are not cryptographically random (not suitable for high-security use cases)
