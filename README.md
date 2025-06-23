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

## Troubleshooting
- Ensure your `.env` file is correctly formatted and all required variables are set.
- If you change database settings, update them in `settings.py` and your local PostgreSQL instance.

## License
MIT 