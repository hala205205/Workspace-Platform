# Workspace Platform

Workspace Platform is an internal workspace system for managing team announcements, calendar events, notifications, users, roles, and departments.

## The project includes

* FastAPI backend
* React frontend
* JWT authentication
* Role-based permissions
* Admin dashboard
* Announcements module
* Calendar module
* Notifications module
* User, role, and department management

---

## Features

### Authentication

* First-time admin setup
* Login and logout
* JWT access and refresh tokens
* Change password from settings
* Admin can reset user passwords

### Administration

* Create users
* Create roles
* Assign permissions to roles
* Create departments
* Assign users to departments
* Reset user passwords by admin

### Announcements

* Create, edit, and delete announcements
* Pin announcements
* Target announcements to:

  * All users
  * Specific department
  * Specific role
  * Specific user
* Comments and likes
* Admin can see all announcements
* Creator sees their targeted announcements

### Calendar

* Create, edit, and delete events
* Target events to:

  * All users
  * Specific department
  * Specific role
  * Specific user
* Department calendar view
* Personal calendar view
* RSVP options:

  * Attend
  * Maybe
* Event reminders

### Notifications

* Internal inbox
* Mark as read / mark all as read
* Reminder worker support

---

## Project Structure

```text
workspace_backend_professional/
│
├── app/
├── alembic/
├── frontend/
├── tests/
├── requirements.txt
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── .env.example
└── .gitignore
```

---

## Requirements

* Python 3.10+
* Node.js 18+
* npm
* Git (optional)

---

## Backend Setup

```powershell
cd workspace_backend_professional
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If blocked:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

Then:

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### URLs

```text
Backend: http://127.0.0.1:8000
Docs:    http://127.0.0.1:8000/docs
Health:  http://127.0.0.1:8000/health
```

---

## Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

```text
http://localhost:3000
```

---

## First Time Usage

1. Start backend
2. Start frontend
3. Open: http://localhost:3000
4. Setup admin account
5. Login
6. Create departments, roles, users

---

## Environment Variables

```env
APP_NAME=Workspace Platform API
ENVIRONMENT=development
DEBUG=false
DATABASE_URL=sqlite+aiosqlite:///./workspace.db
JWT_SECRET=replace-with-at-least-32-random-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:3000
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=10
```

### Notes

* Do NOT upload `.env`
* Use strong `JWT_SECRET`

Generate secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## Running Tests

```powershell
pytest
# or
python -m pytest
```

---

## Docker Usage

```powershell
Copy-Item .env.example .env
docker compose up --build
```

```text
http://localhost:3000
```

---

## Notes

* `/` may show 404 (normal)
* Use `/docs` for API
* Use `/health` for status
* Frontend runs on `http://localhost:3000`

---

## License

Educational and internal workspace management use.
