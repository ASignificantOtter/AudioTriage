from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from audiotriage.services import AudioTriageServices


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="audiotriage")
    parser.add_argument(
        "--config",
        default="config/audiotriage.example.toml",
        help="Path to config TOML file",
    )

    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser("run", help="Start collector service")
    subcommands.add_parser("gui", help="Launch the desktop GUI")

    report_parser = subcommands.add_parser(
        "report",
        help="Process new incidents and write reports",
    )
    report_parser.add_argument("--since", default=None, help="ISO timestamp lower bound")
    report_parser.add_argument(
        "--output-dir",
        default="var/reports",
        help="Directory for report files",
    )

    summary_parser = subcommands.add_parser(
        "summary",
        help="Write a summary for the last week or custom period",
    )
    summary_parser.add_argument("--week", action="store_true", help="Summarize last 7 days")
    summary_parser.add_argument("--since", default=None, help="ISO timestamp lower bound")
    summary_parser.add_argument("--until", default=None, help="ISO timestamp upper bound")
    summary_parser.add_argument(
        "--output-dir",
        default="var/reports",
        help="Directory for summary files",
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    config_path = Path(args.config)
    services = AudioTriageServices(config_path=config_path)

    if args.command == "run":
        services.run_collector_foreground()
        return

    if args.command == "gui":
        from audiotriage.gui import launch_desktop_app

        launch_desktop_app(config_path)
        return

    if args.command == "report":
        since = datetime.fromisoformat(args.since) if args.since else None
        services = AudioTriageServices(config_path=config_path, output_dir=args.output_dir)
        count = services.process_unreported(since=since)
        print(f"Processed {count} incident(s).")
        return

    if args.command == "summary":
        services = AudioTriageServices(config_path=config_path, output_dir=args.output_dir)
        if args.week:
            since = datetime.now() - timedelta(days=7)
            until = datetime.now()
        else:
            since = (
                datetime.fromisoformat(args.since)
                if args.since
                else datetime.now() - timedelta(days=7)
            )
            until = datetime.fromisoformat(args.until) if args.until else datetime.now()
        md_path, json_path = services.generate_summary(since=since, until=until)
        print(f"Wrote summary files: {md_path}, {json_path}")
        return

    parser.error("Unhandled command")


if __name__ == "__main__":
    main()
