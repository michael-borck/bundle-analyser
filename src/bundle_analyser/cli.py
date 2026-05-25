from __future__ import annotations

import argparse
import json
import sys

from rich.console import Console
from rich.table import Table

from .core import analyse_bundle

console = Console()


def main() -> None:
    from lens_contract import run_contract_subcommands

    from .manifest import MANIFEST

    # `serve` and `manifest` are the family's shared subcommands (lens-contract).
    if run_contract_subcommands(
        MANIFEST,
        app_path="bundle_analyser.api:app",
        default_port=8008,
        env_prefix="BUNDLE_ANALYSER",
    ):
        return

    parser = argparse.ArgumentParser(
        prog="bundle-analyser",
        description="Analyse a collection of files in a folder or zip archive",
        epilog="subcommands: `serve` (run the HTTP API), `manifest` (print the capability manifest)",
    )
    parser.add_argument("path", nargs="?", help="Folder or zip file to analyse")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.path:
        parser.print_help()
        sys.exit(1)

    result = analyse_bundle(args.path)

    if args.json:
        print(json.dumps(result.model_dump(), indent=2))
        return

    if result.error:
        console.print(f"[red]Error:[/red] {result.error}")
        sys.exit(1)

    # Rich summary
    console.print(f"\n[bold]Bundle Analysis:[/bold] {result.source}")
    console.print(
        f"Type: {result.source_type}  |  "
        f"Total files: {result.total_files}  |  "
        f"Analysed: {result.analysed_files}"
    )
    if result.unrecognised_files:
        console.print(f"[yellow]Unrecognised:[/yellow] {len(result.unrecognised_files)} files")
    if result.errors:
        console.print(f"[red]Errors:[/red] {len(result.errors)}")

    # File type table
    table = Table(title="File Type Distribution")
    table.add_column("Extension")
    table.add_column("Count", justify="right")
    for ext, count in sorted(result.file_type_distribution.items(), key=lambda x: -x[1]):
        table.add_row(ext, str(count))
    console.print(table)


if __name__ == "__main__":
    main()
