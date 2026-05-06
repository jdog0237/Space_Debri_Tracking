"""Application bootstrap for the Space Debris Tracking dashboard."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from controller import DashboardController
from model import AnalysisConfiguration, DebrisTrackingModel
from view import DashboardView
from view.dashboard_presenter import DashboardPresenter
from view.dashboard_view import ALERT_SORT_COLUMNS


def _default_descending_for_sort(column: str) -> bool:
    """Worst-first defaults: risk and speed descending; rank, separation, and time ascending."""
    return column not in ("rank", "minimum_separation_meters", "tca")


class SpaceDebrisApplication:
    def __init__(self, view: DashboardPresenter) -> None:
        self.model = DebrisTrackingModel()
        self.view = view
        self.controller = DashboardController(self.model, self.view)

    @staticmethod
    def main(args: list[str]) -> None:
        repo_root = Path(__file__).resolve().parent
        default_catalog = repo_root / "tests" / "testing_csvs" / "simulated_debris.csv"

        parser = argparse.ArgumentParser(
            description="Space debris catalog screening with GUI or console dashboard."
        )
        parser.add_argument(
            "--cli",
            action="store_true",
            help="Use the text-only console dashboard (no Tk/matplotlib).",
        )
        parser.add_argument(
            "--catalog",
            default=str(default_catalog),
            help="Path to debris catalog CSV (columns: id,x,y,z,vx,vy,vz).",
        )
        parser.add_argument(
            "--export",
            default="",
            help="Optional path to write ranked encounter results as CSV after analysis.",
        )
        parser.add_argument(
            "--sort",
            default="risk_score",
            choices=list(ALERT_SORT_COLUMNS),
            help="Column used when rendering the sortable alert table.",
        )
        parser.add_argument(
            "--ascending",
            action="store_true",
            help="Force ascending sort; otherwise use operational defaults per column.",
        )
        ns = parser.parse_args(args)

        if ns.cli:
            view: DashboardPresenter = DashboardView()
            app = SpaceDebrisApplication(view)
            app.controller.initialize()
            app.view.show()
            _bootstrap_session(app, ns)
            return

        try:
            from view.gui_dashboard_view import GuiDashboardView
        except ImportError as exc:
            print(
                "GUI dependencies are missing. Install them with:\n"
                "  pip install -r requirements.txt\n"
                f"Original error: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)

        gui = GuiDashboardView()
        gui.set_catalog_path(ns.catalog)
        app = SpaceDebrisApplication(gui)
        app.controller.initialize()
        gui.set_startup_runner(lambda: _bootstrap_session(app, ns))
        gui.show()


def _bootstrap_session(app: SpaceDebrisApplication, ns: argparse.Namespace) -> None:
    descending = False if ns.ascending else _default_descending_for_sort(ns.sort)
    app.view.set_alert_table_sort(ns.sort, descending=descending)

    app.controller.handle_load_catalog(ns.catalog)

    app.controller.handle_set_spacecraft_parameters(
        0.0,
        0.0,
        0.0,
        0.0,
        7_650.0,
        0.0,
        50.0,
    )
    app.controller.handle_set_analysis_configuration(
        AnalysisConfiguration(
            time_window_start_iso8601="2026-03-30T00:00:00Z",
            time_window_end_iso8601="2026-03-30T00:45:00Z",
            time_step_seconds=60.0,
        )
    )

    app.controller.handle_run_analysis()

    export_path = ns.export.strip()
    if export_path:
        app.controller.handle_export_csv(export_path)
        if ns.cli:
            print(f"\nExported results to {export_path}")


if __name__ == "__main__":
    SpaceDebrisApplication.main(sys.argv[1:])

