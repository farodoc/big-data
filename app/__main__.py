from __future__ import annotations

import argparse

from . import analyze, download, import_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Projekt Big Data - GitHub Archive")
    commands = parser.add_subparsers(dest="command", required=True)

    download_parser = commands.add_parser("download", help="Download GitHub Archive files")
    download.add_arguments(download_parser)
    import_parser = commands.add_parser("import", help="Validate and import JSON to MongoDB")
    import_data.add_arguments(import_parser)
    analyze_parser = commands.add_parser("analyze", help="Run analyses and create charts")
    analyze.add_arguments(analyze_parser)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    {"download": download.main, "import": import_data.main, "analyze": analyze.main}[args.command](args)


if __name__ == "__main__":
    main()
