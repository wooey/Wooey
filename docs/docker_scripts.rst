Running a Script in Docker
==========================

Here is a simple example of a wrapper script to call a docker image using the `docker python library <https://docker-py.readthedocs.io/en/stable/index.html>`_.

::

    import argparse

    import docker

    parser = argparse.ArgumentParser(description="Docker test script")
    parser.add_argument("--phrase", type=str)

    if __name__ == "__main__":
        args = parser.parse_args()
        client = docker.from_env()
        print(client.containers.run("docker/whalesay", f"cowsay {args.phrase}").decode('utf-8'))

When running in this configuration, whatever environment the worker is running in must have access to docker.
