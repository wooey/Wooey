testenv:
	pip install -r requirements.txt
	pip install Django
	pip install -e .

test:
	nosetests tests
	coverage run --branch --source=wooey --omit=wooey/conf*,wooey/migrations*,wooey/tests*,wooey/backend/ast* `which django-admin.py` test --settings=wooey.test_settings wooey.tests
	coverage report
