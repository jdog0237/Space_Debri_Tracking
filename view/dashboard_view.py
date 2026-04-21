"""Dashboard view skeleton."""

from __future__ import annotations

from typing import Any

from model.entities import EncounterResult
from .mvc import View


class DashboardView(View):
    def __init__(self) -> None:
        self._controller = None

    def set_controller(self, controller: Any) -> None:
        self._controller = controller

    def show(self) -> None:
        print("Space Debris Tracking Dashboard (skeleton)")

    def display_error(self, message: str) -> None:
        print(f"[ERROR] {message}")

    def display_catalog_count(self, count: int) -> None:
        print(f"Catalog loaded: {count} objects.")

    def refresh_alert_table(self, rows: list[EncounterResult]) -> None:
        print(f"Alert table refreshed with {len(rows)} rows.")

    def refresh_timeline(self, events: list[EncounterResult]) -> None:
        print(f"Timeline refreshed with {len(events)} events.")

    def refresh_distance_plots(self, series: object) -> None:
        _ = series
        print("Distance-versus-time plots refreshed.")

    def refresh_encounter_geometry(self, view_model: object) -> None:
        _ = view_model
        print("Encounter geometry visualization refreshed.")

    def on_export_csv_requested(self, path: str) -> None:
        if self._controller is not None:
            self._controller.handle_export_csv(path)

    def on_run_analysis_requested(self) -> None:
        if self._controller is not None:
            self._controller.handle_run_analysis()
