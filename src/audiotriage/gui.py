from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from audiotriage.services import AudioTriageServices, IncidentDetail, SummaryFile


class AudioTriageMainWindow(QMainWindow):
    def __init__(self, services: AudioTriageServices) -> None:
        super().__init__()
        self._services = services
        self._incident_ids: list[int] = []
        self._summary_rows: list[SummaryFile] = []

        self.setWindowTitle("AudioTriage")
        self.resize(1100, 760)

        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)
        self.setStatusBar(QStatusBar(self))

        self._dashboard_label = QLabel()
        self._dashboard_label.setWordWrap(True)

        self._incident_filter = QComboBox()
        self._incident_sort = QComboBox()
        self._incident_table = QTableWidget(0, 5)
        self._incident_detail = QTextEdit()

        self._summary_since = QLineEdit((datetime.now() - timedelta(days=7)).date().isoformat())
        self._summary_until = QLineEdit(datetime.now().date().isoformat())
        self._summary_table = QTableWidget(0, 4)

        self._settings_text = QTextEdit()
        self._settings_text.setReadOnly(True)

        self._build_tabs()
        self.refresh_all()

    def _build_tabs(self) -> None:
        self._tabs.addTab(self._build_dashboard_tab(), "Dashboard")
        self._tabs.addTab(self._build_incidents_tab(), "Incidents")
        self._tabs.addTab(self._build_summaries_tab(), "Summaries")
        self._tabs.addTab(self._build_settings_tab(), "Settings")

    def _build_dashboard_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addLayout(self._build_toolbar())
        layout.addWidget(self._dashboard_label)
        layout.addStretch()
        return container

    def _build_toolbar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        for label, handler in [
            ("Refresh", self.refresh_all),
            ("Process Reports", self._process_reports),
            ("Generate Weekly Summary", self._generate_weekly_summary),
            ("Start Collector", self._start_collector),
            ("Stop Collector", self._stop_collector),
        ]:
            button = QPushButton(label)
            button.clicked.connect(handler)
            layout.addWidget(button)
        layout.addStretch()
        return layout

    def _build_incidents_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        controls = QHBoxLayout()
        self._incident_filter.addItems(
            [
                "all",
                "buffer_underrun",
                "device_disconnect",
                "sample_rate_mismatch",
                "driver_restart",
                "cpu_thermal_overload",
                "unknown",
            ]
        )
        self._incident_sort.addItems(["newest", "oldest", "category", "confidence"])
        self._incident_filter.currentTextChanged.connect(self.refresh_incidents)
        self._incident_sort.currentTextChanged.connect(self.refresh_incidents)
        controls.addWidget(QLabel("Filter"))
        controls.addWidget(self._incident_filter)
        controls.addWidget(QLabel("Sort"))
        controls.addWidget(self._incident_sort)
        controls.addStretch()
        layout.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        self._incident_table.setHorizontalHeaderLabels(
            ["Timestamp", "Category", "Confidence", "Cause", "Report"]
        )
        self._incident_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._incident_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._incident_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._incident_table.itemSelectionChanged.connect(self._on_incident_selected)
        self._incident_table.horizontalHeader().setStretchLastSection(True)
        splitter.addWidget(self._incident_table)

        self._incident_detail.setReadOnly(True)
        splitter.addWidget(self._incident_detail)
        splitter.setSizes([700, 400])

        actions = QHBoxLayout()
        for label, handler in [
            ("Open Latest Report Markdown", lambda: self._open_latest_report(".md")),
            ("Open Latest Report JSON", lambda: self._open_latest_report(".json")),
        ]:
            button = QPushButton(label)
            button.clicked.connect(handler)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)

        return container

    def _build_summaries_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        form = QFormLayout()
        form.addRow("Since", self._summary_since)
        form.addRow("Until", self._summary_until)
        layout.addLayout(form)

        button_row = QHBoxLayout()
        for label, handler in [
            ("Generate Custom Summary", self._generate_custom_summary),
            ("Open Markdown", lambda: self._open_selected_summary(".md")),
            ("Open JSON", lambda: self._open_selected_summary(".json")),
        ]:
            button = QPushButton(label)
            button.clicked.connect(handler)
            button_row.addWidget(button)
        button_row.addStretch()
        layout.addLayout(button_row)

        self._summary_table.setHorizontalHeaderLabels(["Label", "Updated", "Markdown", "JSON"])
        self._summary_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._summary_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._summary_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._summary_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._summary_table)

        return container

    def _build_settings_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        button = QPushButton("Validate Settings")
        button.clicked.connect(self.refresh_settings)
        layout.addWidget(button)
        layout.addWidget(self._settings_text)
        return container

    def refresh_all(self) -> None:
        validation = self._services.validate_settings()
        if not validation.valid:
            self.refresh_settings()
            self._set_status("Configuration invalid — fix settings before using other views")
            return
        self.refresh_dashboard()
        self.refresh_incidents()
        self.refresh_summaries()
        self.refresh_settings()
        self._set_status("Refreshed")

    def refresh_dashboard(self) -> None:
        dashboard = self._services.dashboard_data()
        category_lines = "\n".join(f"- {name}: {count}" for name, count in dashboard.top_categories)
        cause_lines = "\n".join(f"- {name}: {count}" for name, count in dashboard.top_causes)
        latest = (
            f"{dashboard.latest_incident.incident_timestamp} / {dashboard.latest_incident.category}"
            if dashboard.latest_incident
            else "None"
        )
        last_incident = dashboard.collector_status.last_incident_timestamp or "None"
        lines = [
            f"Collector: {dashboard.collector_status.message}",
            f"Last incident seen: {last_incident}",
            f"Incidents last 24h: {dashboard.incidents_last_24_hours}",
            f"Incidents last 7d: {dashboard.incidents_last_7_days}",
            f"Latest incident: {latest}",
            "",
            "Top categories:",
            category_lines or "- None",
            "",
            "Top causes:",
            cause_lines or "- None",
        ]
        self._dashboard_label.setText("\n".join(lines))

    def refresh_incidents(self) -> None:
        if self._incident_filter.currentText() == "all":
            category = None
        else:
            category = self._incident_filter.currentText()
        sort_by = "incident_timestamp"
        descending = True
        match self._incident_sort.currentText():
            case "oldest":
                descending = False
            case "category":
                sort_by = "category"
            case "confidence":
                sort_by = "confidence"

        incidents = self._services.list_incidents(
            limit=200,
            category=category,
            sort_by=sort_by,
            descending=descending,
        )
        self._incident_ids = [item.incident_id for item in incidents]
        self._incident_table.setRowCount(len(incidents))
        for row_index, item in enumerate(incidents):
            values = [
                item.incident_timestamp,
                item.category,
                f"{item.confidence:.2f}",
                item.correlated_cause or "",
                "yes" if item.has_report else "no",
            ]
            for column_index, value in enumerate(values):
                self._incident_table.setItem(row_index, column_index, QTableWidgetItem(value))

        if incidents:
            self._incident_table.selectRow(0)
        else:
            self._incident_detail.clear()

    def refresh_summaries(self) -> None:
        self._summary_rows = self._services.list_summary_files()
        self._summary_table.setRowCount(len(self._summary_rows))
        for row_index, item in enumerate(self._summary_rows):
            values = [
                item.label,
                item.updated_at or "",
                "yes" if item.markdown_path else "no",
                "yes" if item.json_path else "no",
            ]
            for column_index, value in enumerate(values):
                self._summary_table.setItem(row_index, column_index, QTableWidgetItem(value))

    def refresh_settings(self) -> None:
        validation = self._services.validate_settings()
        lines = [
            f"Config: {self._services.config_path}",
            f"Valid: {'yes' if validation.valid else 'no'}",
            "",
            "Errors:",
        ]
        if validation.errors:
            lines.extend(f"- {message}" for message in validation.errors)
        else:
            lines.append("- None")
        lines.extend(["", "Details:"])
        lines.extend(f"- {message}" for message in validation.details)
        self._settings_text.setPlainText("\n".join(lines))

    def _on_incident_selected(self) -> None:
        row = self._incident_table.currentRow()
        if row < 0 or row >= len(self._incident_ids):
            return
        self._show_incident_detail(self._services.get_incident(self._incident_ids[row]))

    def _show_incident_detail(self, incident: IncidentDetail | None) -> None:
        if incident is None:
            self._incident_detail.clear()
            return
        lines = [
            f"ID: {incident.incident_id}",
            f"Timestamp: {incident.incident_timestamp}",
            f"Category: {incident.category}",
            f"Confidence: {incident.confidence:.2f}",
            f"Correlated cause: {incident.correlated_cause or 'unknown'}",
            f"Created at: {incident.created_at}",
            "",
            "Raw context:",
            incident.raw_context or "(none)",
            "",
            "Report:",
            incident.report_text or "(not yet generated)",
        ]
        self._incident_detail.setPlainText("\n".join(lines))

    def _process_reports(self) -> None:
        count = self._services.process_unreported()
        self.refresh_all()
        self._set_status(f"Processed {count} incident(s)")

    def _generate_weekly_summary(self) -> None:
        until = datetime.now()
        since = until - timedelta(days=7)
        md_path, _ = self._services.generate_summary(since=since, until=until)
        self.refresh_summaries()
        self._set_status(f"Wrote {md_path.name}")

    def _generate_custom_summary(self) -> None:
        try:
            since = datetime.fromisoformat(self._summary_since.text())
            until_raw = datetime.fromisoformat(self._summary_until.text())
            # If the user entered a date-only value (no time component), advance to
            # end-of-day so that incidents occurring during that day are included.
            if until_raw.hour == 0 and until_raw.minute == 0 and until_raw.second == 0 and until_raw.microsecond == 0:
                until = until_raw.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                until = until_raw
        except ValueError:
            QMessageBox.critical(self, "Invalid date", "Use ISO dates like YYYY-MM-DD.")
            return
        md_path, _ = self._services.generate_summary(since=since, until=until)
        self.refresh_summaries()
        self._set_status(f"Wrote {md_path.name}")

    def _start_collector(self) -> None:
        status = self._services.start_collector_background()
        self.refresh_dashboard()
        self._set_status(status.message)

    def _stop_collector(self) -> None:
        status = self._services.stop_collector_background()
        self.refresh_dashboard()
        self._set_status(status.message)

    def _open_selected_summary(self, suffix: str) -> None:
        row = self._summary_table.currentRow()
        if row < 0 or row >= len(self._summary_rows):
            self._set_status("Select a summary first")
            return
        summary = self._summary_rows[row]
        path = summary.markdown_path if suffix == ".md" else summary.json_path
        if path is None or not self._services.open_path(path):
            self._set_status("Unable to open selected file")
            return
        self._set_status(f"Opened {path.name}")

    def _open_latest_report(self, suffix: str) -> None:
        markdown_path, json_path = self._services.latest_report_paths()
        path = markdown_path if suffix == ".md" else json_path
        if path is None or not self._services.open_path(path):
            self._set_status("Unable to open latest report file")
            return
        self._set_status(f"Opened {path.name}")

    def _set_status(self, message: str) -> None:
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage(message)


def build_application(
    config_path: Path | str,
    *,
    output_dir: Path | str = "var/reports",
) -> QApplication:
    existing_app = QApplication.instance()
    app = cast(QApplication, existing_app) if existing_app is not None else QApplication(sys.argv)
    services = AudioTriageServices(config_path=config_path, output_dir=output_dir)
    window = AudioTriageMainWindow(services)
    window.show()
    app.setProperty("audiotriage_window", window)
    return app


def launch_desktop_app(config_path: Path | str, *, output_dir: Path | str = "var/reports") -> None:
    app = build_application(config_path, output_dir=output_dir)
    app.exec()


def main() -> None:
    parser = argparse.ArgumentParser(prog="audiotriage-gui")
    parser.add_argument("--config", default="config/audiotriage.example.toml")
    parser.add_argument("--output-dir", default="var/reports")
    args = parser.parse_args()
    launch_desktop_app(Path(args.config), output_dir=args.output_dir)
