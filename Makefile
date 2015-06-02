testenv:
	pip install -e .
	pip install -r requirements.txt
	pip install Django

test:
	nosetests tests
	coverage run --branch --source=djangui `which django-admin.py` test --settings=djangui.test_settings djangui.tests
	coverage report --omit=djangui/test*,djangui/migrations*,djangui/conf*