dev:
	FLASK_ENV=development flask run

tests:
	python tests.py

test:
	python -m unittest -v $(path)

coverage:
	coverage report -m

all-tests:
	coverage run -m unittest -v && coverage report -m && coverage html

dev-sql:
	sqlite3 dtns.db

lint:
	flake8 dtns
	flake8 tests

pr: lint all-tests