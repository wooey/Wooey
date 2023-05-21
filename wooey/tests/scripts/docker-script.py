import argparse

import docker

parser = argparse.ArgumentParser(description="Docker test script")
parser.add_argument("--phrase", type=str)

if __name__ == "__main__":
    args = parser.parse_args()
    client = docker.from_env()
    print(
        client.containers.run("docker/whalesay", f"cowsay {args.phrase}").decode(
            "utf-8"
        )
    )
