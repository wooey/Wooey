import argparse
import os

import django

django.setup()
from django.conf import settings

import docker
from docker.types import Mount

parser = argparse.ArgumentParser(description="Docker test script")
parser.add_argument("--phrase", type=str)

if __name__ == "__main__":
    args = parser.parse_args()
    client = docker.from_env()
    volume = client.volumes.get("wooey_user_uploads")
    volume_mount = volume.attrs["Mountpoint"]
    current_dir = os.getcwd()
    wooey_data_dir = os.path.join(
        volume_mount.rstrip("/"),
        current_dir.replace(settings.MEDIA_ROOT, "").lstrip("/"),
    )
    print(
        client.containers.run(
            image="busybox",
            command=f"dd if=/dev/urandom of=/output/test.garbage bs=1M count=1",
            mounts=[Mount(target="/output", source=wooey_data_dir, type="bind")],
        ).decode("utf-8")
    )
