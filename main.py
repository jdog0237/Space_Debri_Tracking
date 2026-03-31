"""Application bootstrap for the MVC skeleton."""

from __future__ import annotations

from controller import DashboardController
from model import AnalysisConfiguration, DebrisTrackingModel, SpacecraftState, Vector3
from view import DashboardView


class SpaceDebrisApplication:
    def __init__(self) -> None:
        self.model = DebrisTrackingModel()
        self.view = DashboardView()
        self.controller = DashboardController(self.model, self.view)

    @staticmethod
    def main(args: list[str]) -> None:
        _ = args
        app = SpaceDebrisApplication()
        app.controller.initialize()

        # Seed basic runtime state for first-iteration wiring tests.
        app.model.set_spacecraft_state(
            SpacecraftState(
                position=Vector3(0.0, 0.0, 0.0),
                velocity=Vector3(0.0, 0.0, 0.0),
                safety_radius_meters=50.0,
            )
        )
        app.model.set_analysis_configuration(
            AnalysisConfiguration(
                time_window_start_iso8601="2026-03-30T00:00:00Z",
                time_window_end_iso8601="2026-03-30T00:10:00Z",
                time_step_seconds=1.0,
            )
        )

        app.view.show()


if __name__ == "__main__":
    import sys

    SpaceDebrisApplication.main(sys.argv[1:])
