from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bundle-analyser",
        description="Bundle analyser — analyse a folder or zip archive of files (coming soon)",
    )
    parser.add_argument("path", nargs="?", help="Folder path or zip archive to analyse")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--version", action="version", version="0.1.0")

    subparsers = parser.add_subparsers(dest="command")
    serve = subparsers.add_parser("serve", help="Start API server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8008)

    args = parser.parse_args()

    if args.command == "serve":
        print("bundle-analyser serve — not yet implemented", file=sys.stderr)
        sys.exit(1)

    if not args.path:
        parser.print_help()
        sys.exit(1)

    print("bundle-analyser — not yet implemented", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
