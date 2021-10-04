dev:
	python run.py development

tests:
	python tests.py

coverage:
	coverage report -m

all-tests:
	coverage run -m unittest tests.py && coverage report -m && coverage html