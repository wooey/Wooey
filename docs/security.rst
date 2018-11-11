Security
========

Wooey is run with Django, which has a great record with respect to security, and the
production deployment settings utilizes many of the best practices espoused in
the `12-factor-app <https://12factor.net/>`__.

Scripts run by Wooey must be uploaded by users with administrator privileges. Thus,
only scripts you are comfortable users running should be available (and scripts
can be isolated to a given set of users).
