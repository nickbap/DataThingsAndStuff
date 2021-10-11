dev:
	FLASK_ENV=development flask run

tests:
	python tests.py

coverage:
	coverage report -m

all-tests:
	coverage run -m unittest tests.py && coverage report -m && coverage html