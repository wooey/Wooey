testenv:
	pip install -r requirements.txt
	pip install -e .
	pip install sphinx mock

dev-test:
	nosetests --with-coverage --cover-erase --cover-branches --cover-package=wooey tests/* -s
	coverage run --append --branch --source=wooey `which django-admin.py` test --settings=wooey.test_settings -s wooey.tests
	coverage report --omit='*migrations*','*wooey_scripts*','*tests/scripts*','*conf/*'

test:
	nosetests --with-coverage --cover-erase --cover-branches --cover-package=wooey tests/*
	coverage run --append --branch --source=wooey `which django-admin.py` test --settings=wooey.test_settings wooey.tests
	coverage report --omit='*migrations*','*wooey_scripts*','*tests/scripts*','*conf/*'

.PHONY: docs
docs:
	cd docs && make html
