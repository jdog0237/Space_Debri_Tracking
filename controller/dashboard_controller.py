"""Concrete dashboard controller implementation."""

from __future__ import annotations

from model import DebrisTrackingModel, ModelEvent, ModelListener
from model.exceptions import AnalysisException, CatalogValidationException, InvalidInputException
from view.dashboard_view import DashboardView

from .mvc import AbstractController


class DashboardController(AbstractController, ModelListener):
    def __init__(self, model: DebrisTrackingModel, view: DashboardView) -> None:
        super().__init__(model=model, view=view)
        self._debris_model = model
        self._dashboard_view = view

    def initialize(self) -> None:
        self._debris_model.add_model_listener(self)
        self._dashboard_view.set_controller(self)
        self._wire_view_actions()

    def _wire_view_actions(self) -> None:
        # Placeholder hook for GUI signal wiring in later iterations.
        return None

    def handle_load_catalog(self, path: str) -> None:
        try:
            self._debris_model.load_catalog_from_csv(path)
            self._dashboard_view.display_catalog_count(
                self._debris_model.get_catalog().get_object_count()
            )
        except (CatalogValidationException, InvalidInputException) as exc:
            self._dashboard_view.display_error(str(exc))

    def handle_generate_synthetic_catalog(self, count: int) -> None:
        try:
            self._debris_model.generate_synthetic_catalog(count)
            self._dashboard_view.display_catalog_count(
                self._debris_model.get_catalog().get_object_count()
            )
        except (CatalogValidationException, InvalidInputException) as exc:
            self._dashboard_view.display_error(str(exc))

    def handle_run_analysis(self) -> None:
        try:
            self._debris_model.run_collision_analysis()
        except AnalysisException as exc:
            self._dashboard_view.display_error(str(exc))

    def handle_export_csv(self, path: str) -> None:
        try:
            self._debris_model.export_results_csv(path)
        except AnalysisException as exc:
            self._dashboard_view.display_error(str(exc))

    def model_changed(self, event: ModelEvent) -> None:
        self.handle_model_event(event)

    def handle_model_event(self, event: ModelEvent) -> None:
        if event.get_event_type() == "analysis_completed":
            results = self._debris_model.get_ranked_encounters()
            self._dashboard_view.refresh_alert_table(results)
            self._dashboard_view.refresh_timeline(results)
