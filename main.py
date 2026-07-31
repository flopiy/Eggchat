import argparse
from node.core import Node
from cli.console import Console


def main():
    parser = argparse.ArgumentParser(description="DCP Node")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--name", default=None)
    parser.add_argument("--rendezvous-host", default=None)
    parser.add_argument("--rendezvous-port", type=int, default=7000)
    args = parser.parse_args()

    node = Node(
        host=args.host,
        port=args.port,
        name=args.name,
        rendezvous_host=args.rendezvous_host,
        rendezvous_port=args.rendezvous_port
    )
    node.start()

    console = Console(node)
    console.run()


if __name__ == "__main__":
    main()