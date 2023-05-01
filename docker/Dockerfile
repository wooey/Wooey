FROM python:3.7

RUN useradd -u 1000 wooey

ARG BUILD_DIR=/wooey_build
ENV BUILD_DIR=${BUILD_DIR}

WORKDIR ${BUILD_DIR}
RUN chown wooey:wooey ${BUILD_DIR}

RUN pip install psycopg2

COPY --chown=wooey:wooey setup.py MANIFEST.in Makefile README.md ${BUILD_DIR}/
COPY --chown=wooey:wooey scripts ${BUILD_DIR}/scripts
COPY --chown=wooey:wooey wooey ${BUILD_DIR}/wooey
COPY --chown=wooey:wooey tests ${BUILD_DIR}/tests


RUN pip install -e .[dev]

RUN chmod -R a+rwx ${BUILD_DIR}

ARG WOOEY_PROJECT=docker_wooey

USER wooey
RUN wooify -p ${WOOEY_PROJECT}

WORKDIR ${BUILD_DIR}/${WOOEY_PROJECT}

COPY docker/scripts/run-server run-server

# To prevent volumes from being made as root, we need to make the directory
# first and then create a volume. This will make docker inherit the permissions
# of the folder it is replacing. Otherwise, we will be unable to write to this
# folder as non-root
RUN mkdir -p $BUILD_DIR/$WOOEY_PROJECT/$WOOEY_PROJECT/user_uploads

CMD ["sh", "-c", "make -C ${BUILD_DIR} test"]
