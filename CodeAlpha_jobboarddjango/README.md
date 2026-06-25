# 💼 Job Board — Django REST API

A simple job board backend built with Django and Django REST Framework.

---

## Tech Stack

- Python 3
- Django
- Django REST Framework
- Pillow (image handling)
- SQLite (default)

---

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Apply migrations

```bash
python manage.py migrate
```

### 3. Run the server

```bash
python manage.py runserver
```

The API will be available at **http://localhost:8000**

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/jobs/` | List all job postings |
| `POST` | `/api/jobs/` | Create a new job posting |
| `GET` | `/api/jobs/<id>/` | Retrieve a job posting |
| `PUT` | `/api/jobs/<id>/` | Update a job posting |
| `DELETE` | `/api/jobs/<id>/` | Delete a job posting |

---

## Project Structure

```
CodeAlpha_jobboarddjango/
├── job_board/          # Project settings and root URLs
├── jobs/               # Jobs app — models, views, serializers
├── requirements.txt
└── manage.py
```

---

## Dependencies

```
django
djangorestframework
pillow
```
