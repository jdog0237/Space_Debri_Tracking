"""Mission-operations style text dashboard (Task 4 / FR-4.x)."""

from __future__ import annotations

import math
from typing import Any, Callable, Mapping, Sequence

from model.entities import (
    AnalysisConfiguration,
    DistanceTimeSeries,
    EncounterGeometry2D,
    EncounterResult,
    SpacecraftState,
)
from .mvc import View


_SORT_KEYS: dict[str, Callable[[EncounterResult], float | int | str]] = {
    "rank": lambda r: r.rank,
    "risk_score": lambda r: r.risk_score,
    "minimum_separation_meters": lambda r: r.minimum_separation_meters,
    "relative_velocity_meters_per_second": lambda r: r.relative_velocity_meters_per_second,
    "tca": lambda r: r.time_of_closest_approach_iso8601,
}

ALERT_SORT_COLUMNS: tuple[str, ...] = tuple(sorted(_SORT_KEYS.keys()))


def sort_encounters(rows: list[EncounterResult], column: str, descending: bool) -> list[EncounterResult]:
    normalized = column.strip().lower()
    if normalized not in _SORT_KEYS:
        raise ValueError(
            f"Unknown sort column {column!r}. Expected one of: {', '.join(sorted(_SORT_KEYS))}."
        )
    key = _SORT_KEYS[normalized]
    return sorted(rows, key=key, reverse=descending)


def _fmt_float(value: float, width: int, decimals: int) -> str:
    text = f"{value:.{decimals}f}"
    return text[:width].rjust(width)


def _fmt_str(text: str, width: int) -> str:
    return text[:width].ljust(width)


def _downsample_indices(sample_count: int, width: int) -> list[int]:
    if sample_count <= 0:
        return []
    if width <= 1 or sample_count <= width:
        return list(range(sample_count))
    return [int(round(i * (sample_count - 1) / (width - 1))) for i in range(width)]


def _ascii_distance_chart(series: DistanceTimeSeries, plot_width: int = 52, plot_height: int = 7) -> list[str]:
    values = list(series.distance_meters)
    if not values:
        return ["  (no distance samples)"]

    vmin = min(values)
    vmax = max(values)
    if math.isclose(vmin, vmax):
        vmax = vmin + 1.0

    idx = _downsample_indices(len(values), plot_width)
    sampled = [values[i] for i in idx]

    grid: list[list[str]] = [[" " for _ in range(plot_width)] for _ in range(plot_height)]

    for col, val in enumerate(sampled):
        row_from_bottom = int((val - vmin) / (vmax - vmin) * (plot_height - 1))
        row_from_bottom = max(0, min(plot_height - 1, row_from_bottom))
        row = plot_height - 1 - row_from_bottom
        grid[row][col] = "*"

    lines: list[str] = []
    for row_idx, row in enumerate(grid):
        prefix = _fmt_float(vmax - (vmax - vmin) * (row_idx / max(plot_height - 1, 1)), 10, 1)
        lines.append(f"{prefix} |{''.join(row)}|")
    lines.append(f"{' ' * 11}+{'-' * plot_width}+")
    lines.append(
        "           "
        f"t_start {_fmt_str(series.time_iso8601[0], 24)}"
        f"  ...  t_end {_fmt_str(series.time_iso8601[-1], 24)}"
    )
    return lines


def _ascii_xy_encounter(geo: EncounterGeometry2D, size: int = 21) -> list[str]:
    """Raster sketch of spacecraft (S) and debris (D) in the XY plane at TCA."""
    half = size // 2
    sx = geo.spacecraft_x_meters
    sy = geo.spacecraft_y_meters
    dx = geo.debris_x_meters
    dy = geo.debris_y_meters
    cx = (sx + dx) / 2.0
    cy = (sy + dy) / 2.0
    span = max(abs(sx - dx), abs(sy - dy), 1.0) * 1.15

    def to_cell(px: float, py: float) -> tuple[int, int]:
        u = int(round((px - cx) / span * half)) + half
        v = half - int(round((py - cy) / span * half))
        u = max(0, min(size - 1, u))
        v = max(0, min(size - 1, v))
        return u, v

    grid = [["." for _ in range(size)] for _ in range(size)]
    sc_col, sc_row = to_cell(sx, sy)
    db_col, db_row = to_cell(dx, dy)
    grid[sc_row][sc_col] = "S"
    if db_row == sc_row and db_col == sc_col:
        grid[db_row][db_col] = "X"
    else:
        grid[db_row][db_col] = "D"

    lines = [
        f"  XY projection at TCA for {geo.debris_id} (each cell ~ scaled meters):",
        f"    Spacecraft (S): ({sx:.1f}, {sy:.1f}) m",
        f"    Debris (D): ({dx:.1f}, {dy:.1f}) m",
        f"    Minimum separation (3D): {geo.minimum_separation_meters:.2f} m",
        "    +" + "-" * size + "+ Y ^",
    ]
    for r in range(size):
        lines.append(f"    |{''.join(grid[r])}|")
    lines.append("    +" + "-" * size + "+--> X")
    return lines


class DashboardView(View):
    """Console dashboard implementing FR-4.1–FR-4.5 without third-party UI libraries."""

    def __init__(self) -> None:
        self._controller = None
        self._alert_sort_column = "rank"
        self._alert_sort_descending = False

    def set_controller(self, controller: Any) -> None:
        self._controller = controller

    def set_alert_table_sort(self, column: str, descending: bool) -> None:
        normalized = column.strip().lower()
        if normalized not in _SORT_KEYS:
            raise ValueError(
                f"Unknown sort column {column!r}. Expected one of: {', '.join(sorted(_SORT_KEYS))}."
            )
        self._alert_sort_column = normalized
        self._alert_sort_descending = descending

    def get_alert_table_sort(self) -> tuple[str, bool]:
        return self._alert_sort_column, self._alert_sort_descending

    def show(self) -> None:
        print("Space Debris Tracking & Collision Risk Dashboard")
        print("Interpretable constant-velocity screening - console visualization mode.")

    def display_error(self, message: str) -> None:
        print(f"[ERROR] {message}")

    def display_catalog_count(self, count: int) -> None:
        print(f"Catalog loaded: {count} objects.")

    def display_spacecraft_parameters(self, state: SpacecraftState) -> None:
        pos = state.position
        vel = state.velocity
        print("Spacecraft parameters configured.")
        print(f"  Position (m): x={pos.x}, y={pos.y}, z={pos.z}")
        print(f"  Velocity (m/s): vx={vel.x}, vy={vel.y}, vz={vel.z}")
        print(f"  Safety radius (m): {state.get_safety_radius_meters()}")

    def display_analysis_configuration(self, config: AnalysisConfiguration) -> None:
        print(
            "Analysis configuration:",
            f"{config.time_window_start_iso8601} .. {config.time_window_end_iso8601}",
            f"step={config.time_step_seconds}s",
        )

    def refresh_alert_table(self, rows: list[EncounterResult]) -> None:
        column, descending = self.get_alert_table_sort()
        sorted_rows = sort_encounters(rows, column, descending)

        print("\n--- Alert table (sort: {}, {}) ---".format(column, "desc" if descending else "asc"))
        header = (
            f"{_fmt_str('rank', 6)} "
            f"{_fmt_str('debris_id', 14)} "
            f"{_fmt_str('min_sep_m', 14)} "
            f"{_fmt_str('TCA (UTC)', 24)} "
            f"{_fmt_str('|v_rel| m/s', 14)} "
            f"{_fmt_str('risk', 10)}"
        )
        print(header)
        print("-" * len(header))
        for row in sorted_rows:
            print(
                f"{row.rank:<6} "
                f"{_fmt_str(row.debris_id, 14)} "
                f"{_fmt_float(row.minimum_separation_meters, 14, 2)} "
                f"{_fmt_str(row.time_of_closest_approach_iso8601, 24)} "
                f"{_fmt_float(row.relative_velocity_meters_per_second, 14, 2)} "
                f"{_fmt_float(row.risk_score, 10, 4)}"
            )

    def refresh_timeline(self, events: list[EncounterResult]) -> None:
        ordered = sorted(events, key=lambda e: e.time_of_closest_approach_iso8601)
        print("\n--- Close approach timeline (chronological) ---")
        for ev in ordered:
            print(
                f"  {ev.time_of_closest_approach_iso8601}  "
                f"id={ev.debris_id}  "
                f"min_sep={ev.minimum_separation_meters:.1f} m  "
                f"risk={ev.risk_score:.4f}  "
                f"rank={ev.rank}"
            )

    def refresh_distance_plots(self, series_by_id: Mapping[str, DistanceTimeSeries]) -> None:
        print("\n--- Distance vs time (sampled separation, meters) ---")
        if not series_by_id:
            print("  (no series; run analysis with at least one debris object)")
            return
        for debris_id, series in series_by_id.items():
            print(f"\n[{debris_id}]")
            for line in _ascii_distance_chart(series):
                print(line)

    def refresh_encounter_geometry(self, geometries: Sequence[EncounterGeometry2D]) -> None:
        print("\n--- 2D encounter geometry (XY plane at TCA) ---")
        if not geometries:
            print("  (no geometries; run analysis first)")
            return
        for geo in geometries:
            for line in _ascii_xy_encounter(geo):
                print(line)

    def on_export_csv_requested(self, path: str) -> None:
        if self._controller is not None:
            self._controller.handle_export_csv(path)

    def on_run_analysis_requested(self) -> None:
        if self._controller is not None:
            self._controller.handle_run_analysis()
