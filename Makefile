run:
	python manage.py runserver

makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

test:
	python manage.py test api.tests

lint:
	ruff check .

fix:
	ruff check . --fix

format:
	ruff format .

allfix:
	ruff format .
	ruff check . --fix

freeze:
	pip freeze > requirements.txt 