FROM ubuntu:bionic
RUN apt-get update \
    && apt-get install -y git apt-utils python3.7 python3-pip python3-wheel build-essential python3.7-dev virtualenv libpq-dev sudo \
    && apt-get clean \
    && python3 -m pip install --upgrade pip

ARG USERID=1000
ARG GROUPID=1000

RUN groupadd -g $GROUPID ubuntu \
    && useradd -g ubuntu --no-log-init -u $USERID -s /bin/bash -d /home/user -m user \
    && mkdir -p /etc/sudoers.d/ \
    && ( umask 226 && echo "user ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/50_ubuntu )

#COPY users.json /home/user/
COPY . /home/user/wooey/
WORKDIR /home/user/wooey/

RUN virtualenv /home/user/py37_env --python=/usr/bin/python3.7 \
    && /home/user/py37_env/bin/pip install gunicorn psycopg2 \
    && /home/user/py37_env/bin/pip install .

WORKDIR /home/user/
RUN PATH="/home/user/py37_env/bin/:$PATH" /home/user/py37_env/bin/wooify_no_migrate -p support_portal

WORKDIR /home/user/support_portal/

#RUN /home/user/py37_env/bin/python /home/user/support_portal/manage.py loaddata /home/user/users.json \
RUN chown -R $USERID:$GROUPID /home/user

EXPOSE 8000
USER $USERID:$GROUPID
