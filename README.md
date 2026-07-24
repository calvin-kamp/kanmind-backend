# KanMind – Backend

A REST API for a Kanban-style project management tool, built with Django and the
Django REST Framework. It provides token-based authentication and endpoints for
boards, tasks (with assignees, reviewers, statuses and priorities) and comments,
including per-object permissions (board membership, ownership, authorship).

> **Note:** This is the **backend only**. It is meant to be run together with the
> corresponding frontend, which talks to this API. You need the frontend
> repository as well:
>
> **Frontend repository:** [kanmind-frontend](https://github.com/calvin-kamp/kanmind-frontend)

---

## Tech stack

- Python 3.12+
- Django
- Django REST Framework (token authentication)
- django-cors-headers
- python-dotenv (environment variables)
- SQLite (default development database)

---

## Prerequisites

- Python 3.12 or newer installed and available on your `PATH`
- `pip` (ships with Python)
- Git

---

## Setup

### 1. Clone the repository

```bash
git clone <this-repository-url>
cd <project-folder>
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Once activated, your shell prompt is prefixed with `(.venv)`.

### 3. Install the dependencies

If a `requirements.txt` is present:

```bash
pip install -r requirements.txt
```

Otherwise install the packages directly:

```bash
pip install django djangorestframework django-cors-headers python-dotenv
```

### 4. Configure environment variables

Sensitive settings (like the Django `SECRET_KEY`) are read from a `.env` file
that is **not** committed to the repository. A `.env.template` is provided as a
blueprint. Copy it to create your own `.env`:

**Windows (PowerShell):**

```powershell
copy .env.template .env
```

**macOS / Linux:**

```bash
cp .env.template .env
```

Then generate a fresh `SECRET_KEY` and paste it into your `.env`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Your `.env` should end up looking like this (no quotes, no spaces around `=`):

```
SECRET_KEY=your-generated-key-here
DEBUG=True
```

The `.env` file is listed in `.gitignore` and stays local. Only `.env.template`
(with empty placeholder values) is versioned, so every developer sets up their
own key.

### 5. Apply the database migrations

```bash
python manage.py migrate
```

This creates the SQLite database (`db.sqlite3`) and all tables, including the
token table used for authentication.

### 6. (Optional) Create an admin user

To access the Django admin at `/admin/`:

```bash
python manage.py createsuperuser
```

You will be asked for an email, a full name and a password.

### 7. (Optional) Seed the database with demo data

A management command creates a few users, boards, tasks and comments so you have
something to work with immediately:

```bash
python manage.py seed
```

All seeded users share the same password (see the top of the seed command). Note
that the command file must live at `kanban_app/management/commands/seed.py` for
Django to find it.

### 8. Run the development server

```bash
python manage.py runserver
```

The API is now available at:

```
http://127.0.0.1:8000/
```

---

## Authentication

The API uses **token authentication**. Register or log in to receive a token,
then send it with every request to a protected endpoint:

```
Authorization: Token <your-token>
```

- `POST /api/registration/` – create an account, returns a token
- `POST /api/login/` – log in, returns a token

---

## CORS

The frontend runs on a different origin (port) than the backend, so cross-origin
requests must be allowed. Make sure the frontend origin is listed in
`settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
]
```

Adjust the port if your frontend runs elsewhere.

---

## API overview

Base path: `/api/`

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/registration/` | Create an account, returns a token |
| POST | `/api/login/` | Log in, returns a token |
| GET / POST | `/api/boards/` | List boards / create a board |
| GET / PATCH / DELETE | `/api/boards/<id>/` | Retrieve / update / delete a board |
| GET / POST | `/api/tasks/` | List tasks / create a task |
| PATCH / DELETE | `/api/tasks/<id>/` | Update / delete a task |
| GET | `/api/tasks/assigned-to-me/` | Tasks assigned to the current user |
| GET | `/api/tasks/reviewing/` | Tasks the current user reviews |
| GET / POST | `/api/tasks/<task_id>/comments/` | List / create comments on a task |
| DELETE | `/api/tasks/<task_id>/comments/<comment_id>/` | Delete a comment |
| GET | `/api/email-check/?email=...` | Look up a user by email |

All endpoints require authentication, except `/api/registration/` and
`/api/login/` — those are public, since they are how you obtain a token in the
first place.