testenv:
	pip install -e .[dev]

test:
	pytest --cov=wooey --cov-branch tests/*
	coverage run --append --branch --source=wooey -m django test --settings=wooey.test_settings wooey.tests
	python -m coverage report --omit='*migrations*','*wooey_scripts*','*tests/scripts*','*conf/*'
	python -m coverage xml --omit='*migrations*','*wooey_scripts*','*tests/scripts*','*conf/*'

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

dist: clean ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

release/major release/minor release/patch release/rc:
	bump2version $(@F)
	git push
	git push --tags

.PHONY: docs
docs:
	cd docs && make html
