testenv:
	pip install -r requirements.txt
	pip install Django
	pip install -e .

test:
	nosetests tests
	coverage run --branch --source=djangui --omit=djangui/conf*,djangui/migrations*,djangui/tests* `which django-admin.py` test --settings=djangui.test_settings djangui.tests
	coverage report
