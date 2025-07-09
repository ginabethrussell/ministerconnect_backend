# MinisterConnect Backend

This is the backend API for the MinisterConnect app, built with Django and PostgreSQL.

## Features
- Django 5.x
- PostgreSQL database
- Environment variable support via `.env`

## Local Development Setup

### 1. Clone the Repository
```bash
git clone <repo-url>
cd ministerconnect_backend
```

### 2. Create a Virtual Environment
```bash
python3 -m venv env
source env/bin/activate
```

### 3. Install Dependencies
```bash
pip install django psycopg2-binary
```

### 4. Set Up Environment Variables
Create a `.env` file in the project root with at least:
```env
SECRET_KEY="your-very-secret-key"
```

To generate a secure secret key, you can run:
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```
Copy the output and use it as your SECRET_KEY value.

### 5. Configure the Database
Edit `ministerconnect_backend/settings.py` if needed. Default settings:
- Name: `ministerconnect`
- User: `devuser`
- Password: `devpassword`
- Host: `localhost`
- Port: `5432`

#### Setting up PostgreSQL locally on macOS
1. **Install PostgreSQL** (if not already installed):
   ```bash
   brew install postgresql
   brew services start postgresql
   ```
2. **Create a database user and database:**
   ```bash
   psql postgres
   # In the psql prompt, run:
   CREATE USER devuser WITH PASSWORD 'devpassword';
   CREATE DATABASE ministerconnect OWNER devuser;
   \q
   ```
3. **Verify connection:**
   ```bash
   psql -U devuser -d ministerconnect
   ```

#### Verify PostgreSQL is Running and User Exists

- **Check if PostgreSQL is running:**
  ```bash
  brew services list | grep postgresql
  # or
  pg_isready
  ```
  If not running, start it with:
  ```bash
  brew services start postgresql
  ```

- **Check if the user exists:**
  ```bash
  psql -U postgres -c "\du"
  ```
  Look for `devuser` in the list. If not present, create it as shown above.

- **Check if the database exists:**
  ```bash
  psql -U postgres -lqt | cut -d \| -f 1 | grep ministerconnect
  ```
  If not present, create it as shown above.

Continue only after confirming PostgreSQL is running and both the user and database exist.

### 6. Run Migrations
```bash
python manage.py migrate
```

### 7. Verify Django Can Access the Database

After running migrations, you can confirm Django can read/write to the database:

1. Open the Django shell:
   ```bash
   python manage.py shell
   ```
2. In the shell, run:
   ```python
   from django.contrib.auth.models import User
   User.objects.create_user(username='testuser', password='testpass')
   User.objects.all()
   ```
   You should see a user object returned, confirming read/write access to the DB.
3. Exit the shell:
   ```python
   exit()
   ```

### 8. (Optional) Create a Superuser
```bash
python manage.py createsuperuser
```
You can then log into the Django admin at [http://localhost:8000/admin](http://localhost:8000/admin) once the server is running.

### 9. Run the Development Server
```bash
python manage.py runserver
```

Visit [http://localhost:8000](http://localhost:8000) to view the API or Django welcome page.

## Authentication (JWT)

This API uses JWT (JSON Web Token) authentication. You must obtain a token and include it in the Authorization header for all protected endpoints.

### Obtain Token

**POST** `/api/token/`

Request body:
```json
{
  "email": "user@church.org",
  "password": "yourpassword"
}
```
Response:
```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
```

### Refresh Token

**POST** `/api/token/refresh/`

Request body:
```json
{
  "refresh": "<refresh_token>"
}
```
Response:
```json
{
  "access": "<new_access_token>"
}
```

Include the access token in the Authorization header for all requests to protected endpoints:
```
Authorization: Bearer <access_token>
```

## API Endpoints

### Create Church (Requires Authentication)

**POST** `/api/churches/create/`

Creates a new church. Requires a valid JWT access token in the Authorization header.

**Example request body:**
```json
{
  "name": "Test Church",
  "email": "test@church.com",
  "phone": "+14155552671",
  "website": "https://testchurch.com",
  "street_address": "123 Main St",
  "city": "Springfield",
  "state": "CA",
  "zipcode": "90210",
  "status": "active"
}
```

### Create User (Requires Authentication)

**POST** `/api/users/create/`

Creates a new user and assigns them to one or more groups and a church (if provided). Requires a valid JWT access token in the Authorization header.

**Example request body:**
```json
{
  "email": "user@church.org",
  "name": "Jane Doe",
  "password": "securepassword",
  "groups": ["Church User"],
  "church_id": 1,
  "status": "pending",
  "requires_password_change": true
}
```

### Create Invite Code (Requires Authentication)

**POST** `/api/invite-codes/create/`

Creates a new invite code. Requires a valid JWT access token in the Authorization header. The response includes the name of the user who created the code as `created_by_name`.

**Example request body:**
```json
{
  "code": "CHURCH2024",
  "event": "Spring 2024 Church Registration",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

**Example response:**
```json
{
  "id": 1,
  "code": "CHURCH2024",
  "event": "Spring 2024 Church Registration",
  "used_count": 0,
  "status": "active",
  "created_by": 1,
  "created_by_name": "Jane Doe",
  "expires_at": "2024-12-31T23:59:59Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### List Invite Codes (Requires Authentication)

**GET** `/api/invite-codes/`

Returns a list of all invite codes. Requires a valid JWT access token in the Authorization header. Each invite code includes the name of the user who created it as `created_by_name`.

**Example response:**
```json
[
  {
    "id": 1,
    "code": "CHURCH2024",
    "event": "Spring 2024 Church Registration",
    "used_count": 3,
    "status": "active",
    "created_by": 1,
    "created_by_name": "Jane Doe",
    "expires_at": "2024-12-31T23:59:59Z",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  // ... more invite codes ...
]
```

## Troubleshooting
- Ensure your `.env` file is correctly formatted and all required variables are set.
- If you change database settings, update them in `settings.py` and your local PostgreSQL instance.

## License
MIT 