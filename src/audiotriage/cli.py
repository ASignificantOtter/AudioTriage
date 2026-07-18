from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from audiotriage.classifier import IncidentClassifier
from audiotriage.collector import start_collector
from audiotriage.config import load_settings
from audiotriage.correlator import IncidentCorrelator, SystemEventWindowQuery
from audiotriage.db import get_connection, initialize_database
from audiotriage.orchestrator.controller import PipelineController
from audiotriage.reporter.service import ReportWriter


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="audiotriage")
    parser.add_argument(
        "--config",
        default="config/audiotriage.example.toml",
        help="Path to config TOML file",
    )

    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser("run", help="Start collector service")

    report_parser = subcommands.add_parser("report", help="Process new incidents and write reports")
    report_parser.add_argument("--since", default=None, help="ISO timestamp lower bound")
    report_parser.add_argument("--output-dir", default="var/reports", help="Directory for report files")

    summary_parser = subcommands.add_parser("summary", help="Write a summary for the last week or custom period")
    summary_parser.add_argument("--week", action="store_true", help="Summarize last 7 days")
    summary_parser.add_argument("--since", default=None, help="ISO timestamp lower bound")
    summary_parser.add_argument("--until", default=None, help="ISO timestamp upper bound")
    summary_parser.add_argument("--output-dir", default="var/reports", help="Directory for summary files")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    config_path = Path(args.config)
    settings = load_settings(config_path)
    initialize_database(settings.database_path)

    if args.command == "run":
        start_collector(config_path)
        return

    with get_connection(settings.database_path) as connection:
        controller = PipelineController(
            connection=connection,
            classifier=IncidentClassifier(confidence_threshold=settings.confidence_threshold),
            correlator=IncidentCorrelator(),
            event_query=SystemEventWindowQuery(settings.log_binary_path),
            report_writer=ReportWriter(),
            correlation_window_seconds=settings.correlation_window_seconds,
        )

        if args.command == "report":
            since = datetime.fromisoformat(args.since) if args.since else None
            count = controller.process_unreported(output_dir=args.output_dir, since=since)
            print(f"Processed {count} incident(s).")
            return

        if args.command == "summary":
            if args.week:
                since = datetime.now() - timedelta(days=7)
                until = datetime.now()
            else:
                since = datetime.fromisoformat(args.since) if args.since else datetime.now() - timedelta(days=7)
                until = datetime.fromisoformat(args.until) if args.until else datetime.now()
            md_path, json_path = controller.build_summary(
                output_dir=args.output_dir,
                since=since,
                until=until,
            )
            print(f"Wrote summary files: {md_path}, {json_path}")
            return

    parser.error("Unhandled command")


if __name__ == "__main__":
    main()
