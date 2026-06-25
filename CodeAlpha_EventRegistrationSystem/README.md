# 🎟️ Event Registration System

A lightweight Flask web application for managing events, user sign-ups, and registrations — with a built-in browser UI and a RESTful JSON API.

---

## Features

- Browse upcoming events with live seat availability
- Create user accounts and register for events
- Cancel and re-activate registrations
- Admin panel to create events and view attendee lists
- Duplicate-registration protection and capacity enforcement
- SQLite-backed persistence via SQLAlchemy

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
├── app.py          # All models, routes, and embedded frontend
└── events.db       # Auto-created SQLite database on first run
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

The app starts on **http://localhost:5001** and creates `events.db` automatically. A sample *Python Workshop* event is seeded on the first run.

---

## Data Models

### User
| Field | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `name` | String | Required |
| `email` | String | Required, unique |
| `is_admin` | Boolean | Default `false` |
| `created_at` | DateTime | Auto-set |

### Event
| Field | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `title` | String | Required |
| `description` | Text | Optional |
| `location` | String | Default `"TBD"` |
| `event_date` | DateTime | Required (ISO 8601) |
| `capacity` | Integer | Default `100` |

### Registration
| Field | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `user_id` | Integer | FK → User |
| `event_id` | Integer | FK → Event |
| `status` | String | `confirmed` or `cancelled` |
| `registered_at` | DateTime | Auto-set |

A unique constraint on `(user_id, event_id)` prevents duplicate rows. Cancelling and re-registering reuses the existing row.

---

## API Reference

All endpoints accept and return JSON. The frontend UI at `/` uses these endpoints directly.

### Events

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/events` | List all events (ordered by date) |
| `GET` | `/events/<id>` | Event detail with registration count |
| `POST` | `/events` | Create a new event |

**Create event — request body:**
```json
{
  "title": "Flask Workshop",
  "description": "Hands-on intro",
  "location": "Room 101",
  "event_date": "2025-09-15T10:00:00",
  "capacity": 30
}
```

### Users

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/users/register` | Create a user account |
| `GET` | `/users/<id>` | Get user details |
| `GET` | `/users/<id>/registrations` | List all registrations for a user |

**Register user — request body:**
```json
{ "name": "Jane Doe", "email": "jane@example.com" }
```

### Registrations

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/events/<id>/register` | Register a user for an event |
| `DELETE` | `/registrations/<id>` | Cancel a registration |

**Register for event — request body:**
```json
{ "user_id": 1 }
```

### Admin

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/events/<id>/attendees` | List confirmed attendees for an event |

---

## Business Rules

- **Capacity check** — registration is rejected if `spots_remaining` is 0.
- **Duplicate guard** — re-registering after cancellation reactivates the existing record instead of creating a new one; attempting to register while already confirmed returns `409 Conflict`.
- **Soft delete** — cancellations set `status = "cancelled"` rather than deleting the row.

---

## Example Usage (curl)

```bash
# Create a user
curl -X POST http://localhost:5001/users/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'

# List events
curl http://localhost:5001/events

# Register for event 1
curl -X POST http://localhost:5001/events/1/register \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'

# View registrations
curl http://localhost:5001/users/1/registrations

# Cancel registration
curl -X DELETE http://localhost:5001/registrations/1
```

---

## Configuration

| Setting | Default | Description |
|---|---|---|
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///events.db` | Database path |
| `debug` | `True` | Flask debug mode |
| `port` | `5001` | Server port |

To use a different database (e.g. PostgreSQL), update `SQLALCHEMY_DATABASE_URI` in `app.py` and install the appropriate driver.

---

## Limitations & Future Work

- No authentication — admin endpoints are currently open to all callers
- No pagination on list endpoints
- No email confirmation on registration
- Frontend requires manual entry of User ID (no session management)
