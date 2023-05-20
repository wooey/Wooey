import argparse

parser = argparse.ArgumentParser(description="A useless script with subparsers")
parser.add_argument(
    "--test-arg", type=float, default=2.3, help="a test arg for the main parser"
)

subparsers = parser.add_subparsers(help="commands")

subparser1 = subparsers.add_parser("subparser1", help="Subparser 1")
subparser1.add_argument("--sp1", type=int, default=1, help="sp1", required=True)

subparser2 = subparsers.add_parser("subparser2", help="Subparser 2")
subparser2.add_argument("--sp2", type=int, default=1, help="sp2", required=True)

if __name__ == "__main__":
    args = parser.parse_args()
