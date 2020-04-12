FROM python:3.7

ARG BUILD_DIR=/wooey_build
ENV BUILD_DIR=${BUILD_DIR}

RUN pip install psycopg2

COPY setup.py MANIFEST.in Makefile README.md ${BUILD_DIR}/
COPY scripts ${BUILD_DIR}/scripts
COPY wooey ${BUILD_DIR}/wooey
COPY tests ${BUILD_DIR}/tests

WORKDIR ${BUILD_DIR}

RUN pip install -e .[dev]

RUN chmod -R a+rwx ${BUILD_DIR}

WORKDIR /
ARG WOOEY_PROJECT=docker_wooey

RUN wooify -p ${WOOEY_PROJECT}

WORKDIR ${WOOEY_PROJECT}

COPY docker/scripts/run-server run-server

# Make volumes and make sure the wooey directory is r/w by all. By default,
# docker will create volumes as root so this is needed.
RUN mkdir ${WOOEY_PROJECT}/user_uploads && \
    chmod -R a+rwx /${WOOEY_PROJECT}

EXPOSE 8080

CMD ["sh", "-c", "make -C ${BUILD_DIR} test"]
