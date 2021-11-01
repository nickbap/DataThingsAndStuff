dev:
	FLASK_ENV=development flask run

tests:
	python tests.py

coverage:
	coverage report -m

all-tests:
	coverage run -m unittest -v tests.py && coverage report -m && coverage html

dev-sql:
	sqlite3 dtns.db

lint:
	flake8 dtns
	flake8 tests.py

pr: lint all-tests