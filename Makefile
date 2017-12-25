testenv:
	pip install -r requirements.txt
	pip install -e .
	pip install sphinx mock

test:
	-rm -r test_project
	wooify -p test_project
	nosetests --with-coverage --cover-erase --cover-package=wooey tests
	coverage run --append --branch --source=wooey `which django-admin.py` test --settings=wooey.test_settings wooey.tests
	coverage report

.PHONY: docs
docs:
	cd docs && make html
