# CodeAlpha Event Registration System

A Django-powered event platform for discovering local experiences, saving a spot, and managing registrations. It includes a responsive public website, a browsable JSON API, attendee accounts, and an organizer admin panel.

## Features

- Browse and search published upcoming events; view details, availability, and location.
- Create an attendee account, sign in, register for events, and cancel or renew registrations.
- Enforce event capacity and one active registration per attendee/event.
- Keep draft and cancelled events private from the public site and event API.
- Manage events and registrations in Django Admin.
- Use SQLite out of the box or connect PostgreSQL with `DATABASE_URL`.
- Protect browser forms against CSRF, apply API throttling, and use Django password validation.

## Quick start

Requires Python 3.10 or later.

```powershell
cd codealpha_event_registration_system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

Open <http://127.0.0.1:8000> for the site, <http://127.0.0.1:8000/admin/> for event management, or <http://127.0.0.1:8000/api/> for the browsable API. Create and publish events in the admin panel; the included demo command creates three sample events.

The development settings use a local SQLite database and a development-only secret key. For production, set environment variables rather than using `.env.example` values:

```text
DEBUG=false
SECRET_KEY=<a long, randomly generated secret>
ALLOWED_HOSTS=events.example.com
CSRF_TRUSTED_ORIGINS=https://events.example.com
DATABASE_URL=postgresql://user:password@host:5432/codealpha_events
```

When deployed behind HTTPS, keep `DEBUG=false`, provide a strong `SECRET_KEY`, set the correct allowed host and trusted origin, and run:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

The production settings require HTTPS and trust `X-Forwarded-Proto` from the fronting proxy. Deploy only behind a trusted proxy that overwrites this header with the actual connection scheme.

## API

All API paths are relative to `/api/`. JSON responses use ISO-8601 timestamps. Event endpoints are public; registration endpoints require an authenticated Django session. New accounts and successful sign-ins receive the normal Django session cookie. For browser clients, first load a same-origin page to receive a CSRF cookie, then include its `csrftoken` value in the `X-CSRFToken` header on unsafe requests.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/events/` | List published upcoming events (paginated) |
| `GET` | `/api/events/?search=design&category=Community` | Search/filter the event list |
| `GET` | `/api/events/{slug}/` | Read an event |
| `POST` | `/api/auth/register/` | Create an account and sign in |
| `POST` | `/api/auth/login/` | Sign in with username or email |
| `POST` | `/api/auth/logout/` | Sign out |
| `GET` | `/api/registrations/` | List the signed-in attendee’s registrations |
| `POST` | `/api/registrations/` | Register for an event with `{"event_id": 1}` |
| `GET` | `/api/registrations/{id}/` | Read one of your registrations |
| `POST` | `/api/registrations/{id}/cancel/` | Cancel one of your registrations |

Account creation accepts `username`, `email`, `first_name`, and `password` (at least eight characters). Sign-in accepts `username` or `email` with `password`. Unsafe API requests must include a valid CSRF token. Registration records are always scoped to the signed-in user; trying to read or cancel another attendee’s registration returns `404`.

Example API flow:

```bash
# Fetch a CSRF cookie before making an unsafe request.
curl -c cookies.txt http://127.0.0.1:8000/
CSRF=$(awk '$6=="csrftoken" {print $7}' cookies.txt)

# Create an account; save the session cookie from the response.
curl -i -c cookies.txt -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" -H "X-CSRFToken: $CSRF" \
  -d '{"username":"alex","email":"alex@example.com","first_name":"Alex","password":"Use-a-strong-password"}'

# Public event list.
curl -b cookies.txt http://127.0.0.1:8000/api/events/
```

## Tests and maintenance

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

The test suite covers public event visibility, registration and cancellation, event capacity, attendee privacy, and the event detail page.
