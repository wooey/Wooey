testenv:
	pip install -r requirements.txt
	pip install Django
	pip install -e .

test:
	nosetests --with-coverage --cover-erase --cover-package=wooey tests
	coverage run --branch --source=wooey `which django-admin.py` test --settings=wooey.test_settings wooey.tests
	coverage report
