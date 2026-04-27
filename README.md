# DTS303 Northshore Books

A Django web application for a small bookshop with public catalogue, REST API, user authentication, order management, and admin interface.

## Tech Stack

- **Backend**: Python 3.11+, Django 5.0.3
- **API**: Django REST Framework 3.14.0
- **Authentication**: Session (web) + JWT via `djangorestframework-simplejwt` (API)
- **API Documentation**: OpenAPI 3.0 schema + Swagger UI via `drf-spectacular`
- **Database**: MySQL (mysqlclient 2.2.0); SQLite supported for local dev via `USE_SQLITE=True`
- **Frontend**: HTML (Django templates), CSS (plain CSS), minimal vanilla JavaScript
- **Configuration**: python-decouple 3.8

## Features

- Public book catalogue (no authentication required)
- REST API for books (JSON, admin-only write operations)
- User registration and authentication
- Order management (basket, submit, view history)
- Admin interface for books and orders
- Security best practices (CSRF, XSS prevention, session hardening)
- Fable.co style UI clone

## Setup Instructions

### Quick Setup (Automated)

**Windows:**
```bash
setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
1. Create virtual environment
2. Install dependencies
3. Create `.env` file from `ENV_EXAMPLE.txt`
4. Create necessary directories
5. Run initial migrations (if database is configured)

**Note:** After running the setup script, you still need to:
- Edit `.env` and update `SECRET_KEY` and database credentials
- Create the MySQL database
- Run migrations again (if database is now configured)
- Create a superuser

### Manual Setup

If you prefer to set up manually:

#### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `ENV_EXAMPLE.txt` to `.env` and update with your settings:

```bash
# On Linux/Mac:
cp ENV_EXAMPLE.txt .env

# On Windows:
copy ENV_EXAMPLE.txt .env
```

Edit `.env` with your:
- `SECRET_KEY` (generate a new one for production)
- Database credentials
- `ALLOWED_HOSTS` (comma-separated list)

### 4. Create MySQL Database

You have two options.

**Option A — Docker (recommended, no system install):**

```bash
docker compose up -d
```

This starts MySQL 8.0 on `localhost:3306` with the database `northshore_books` already created. Credentials default to `root` / `northshore_root_pw` (override via `.env`). Stop with `docker compose down`; wipe data with `docker compose down -v`.

**Option B — Native MySQL install:**

```sql
CREATE DATABASE northshore_books CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Then ensure `.env` has `USE_SQLITE=False` and the correct `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin user.

### 7. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

## Test Credentials

After creating a superuser, you can:
- Access admin panel at `/admin/`
- Create regular users via registration at `/accounts/register/`
- Test API endpoints at `/api/books/`

## API Endpoints

### Interactive Documentation

- `GET /api/docs/` - Swagger UI (interactive, try requests in the browser)
- `GET /api/redoc/` - ReDoc (clean reference docs)
- `GET /api/schema/` - Raw OpenAPI 3.0 schema (YAML)

### Authentication (JWT)

- `POST /api/auth/token/` - Obtain access + refresh tokens (body: `{"username", "password"}`)
- `POST /api/auth/token/refresh/` - Get a new access token from a refresh token
- `POST /api/auth/token/verify/` - Validate an access token

Send the access token on subsequent requests as `Authorization: Bearer <token>`. Access tokens expire in 30 minutes; refresh tokens last 1 day and rotate on each use.

### Books API

- `GET /api/books/` - List all books (public, paginated)
- `GET /api/books/<id>/` - Retrieve a book (public)
- `POST /api/books/` - Create a book (admin only)
- `PUT /api/books/<id>/` - Update a book (admin only)
- `PATCH /api/books/<id>/` - Partially update a book (admin only)
- `DELETE /api/books/<id>/` - Delete a book (admin only)

### Filtering and Pagination

- `?author=<name>` - Filter by author
- `?min_price=<number>` - Filter by minimum price
- `?max_price=<number>` - Filter by maximum price
- `?search=<query>` - Search in title and author
- `?ordering=<field>` - Order by field (title, author, price, created_at)
- `?page=<number>` - Pagination (10 items per page)

### Example API Requests

```bash
# List all books
curl http://localhost:8000/api/books/

# Search for books
curl http://localhost:8000/api/books/?search=django

# Filter by author
curl http://localhost:8000/api/books/?author=Smith

# Filter by price range
curl http://localhost:8000/api/books/?min_price=10&max_price=50

# Obtain a JWT access token for an admin user
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Create a book using the JWT access token
curl -X POST http://localhost:8000/api/books/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access-token>" \
  -d '{"title": "New Book", "author": "Author Name", "price": "29.99"}'
```

## Security Notes

### Implemented Security Controls

1. **SQL Injection Prevention**: Django ORM exclusively, no raw SQL queries
2. **XSS Prevention**: Django auto-escaping enabled, no `|safe` filter on user input
3. **CSRF Protection**: CsrfViewMiddleware + `{% csrf_token %}` in all forms
4. **Session Security**: Secure cookie flags, session regeneration on login, timeouts
5. **Password Security**: Django password hashing, rate limiting (5 attempts), generic error messages
6. **Authentication/Authorization**: `@login_required` decorators, ownership checks, admin-only API endpoints
7. **Security Logging**: JSON-structured logs to `storage/logs/security.log`
8. **Input Validation**: Server-side validation with allowlists, numeric checks, length limits
9. **Order Protection**: Server-side total recalculation, price snapshots

### File Locations

- Security settings: `config/settings.py`
- Security logging: `config/security_logger.py`
- CSRF tokens: All templates with POST forms
- Authentication: `accounts/views.py`
- Authorization: `orders/views.py`, `catalogue/api.py`

See `docs/SECURITY.md` for detailed security documentation.

## Project Structure

```
northshore/
├── manage.py
├── config/              # Project settings
├── catalogue/           # Books app
├── orders/              # Orders app
├── accounts/            # Authentication app
├── templates/           # HTML templates
├── static/              # CSS and icons
├── docs/                # Documentation
├── storage/logs/        # Log files
├── requirements.txt
├── README.md
└── .env.example
```

## Running Tests

```bash
python manage.py test
```

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Set `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True` (requires HTTPS)
3. Update `ALLOWED_HOSTS` with your domain
4. Configure proper database credentials
5. Set up static file serving (e.g., WhiteNoise or nginx)
6. Use a production WSGI server (e.g., Gunicorn)

## License

This project is for educational purposes.
