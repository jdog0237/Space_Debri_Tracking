"""Tkinter + Matplotlib dashboard (SRS interactive visualization, open-source plotting stack)."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Mapping, Sequence

import matplotlib

matplotlib.use("TkAgg")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from model.entities import (
    AnalysisConfiguration,
    DistanceTimeSeries,
    EncounterGeometry2D,
    EncounterResult,
    SpacecraftState,
)

from .dashboard_view import ALERT_SORT_COLUMNS, sort_encounters
from .mvc import View


class GuiDashboardView(View):
    """Interactive GUI implementing FR-4 presentation layers."""

    def __init__(self) -> None:
        self._controller: Any = None
        # Python 3.12+ requires a Tk root before constructing Variable subclasses unless master= is set.
        self._root = tk.Tk()
        self._root.withdraw()

        self._startup_runner: Callable[[], None] | None = None

        self._alert_sort_column = "risk_score"
        self._alert_sort_descending = True
        self._last_alert_rows: list[EncounterResult] = []

        self._catalog_label: ttk.Label | None = None
        self._alert_tree: ttk.Treeview | None = None
        self._timeline_tree: ttk.Treeview | None = None
        self._plots_parent: ttk.Frame | None = None
        self._geo_parent: ttk.Frame | None = None
        self._sort_combo: ttk.Combobox | None = None
        self._desc_var = tk.BooleanVar(master=self._root, value=True)

        self._path_var = tk.StringVar(master=self._root, value="")
        self._px = tk.StringVar(master=self._root, value="0")
        self._py = tk.StringVar(master=self._root, value="0")
        self._pz = tk.StringVar(master=self._root, value="0")
        self._vx = tk.StringVar(master=self._root, value="0")
        self._vy = tk.StringVar(master=self._root, value="7650")
        self._vz = tk.StringVar(master=self._root, value="0")
        self._safety = tk.StringVar(master=self._root, value="50")
        self._t_start = tk.StringVar(master=self._root, value="2026-03-30T00:00:00Z")
        self._t_end = tk.StringVar(master=self._root, value="2026-03-30T00:45:00Z")
        self._dt = tk.StringVar(master=self._root, value="60")

    def set_catalog_path(self, path: str) -> None:
        self._path_var.set(path)

    def set_startup_runner(self, runner: Callable[[], None]) -> None:
        """Invoked on the Tk loop after the window is built (load catalog, run analysis, etc.)."""
        self._startup_runner = runner

    def set_controller(self, controller: Any) -> None:
        self._controller = controller

    def set_alert_table_sort(self, column: str, descending: bool) -> None:
        normalized = column.strip().lower()
        if normalized not in ALERT_SORT_COLUMNS:
            raise ValueError(f"Unknown sort column {column!r}.")
        self._alert_sort_column = normalized
        self._alert_sort_descending = descending
        if self._sort_combo is not None:
            self._sort_combo.set(normalized)
        self._desc_var.set(descending)
        self._redraw_alerts()

    def get_alert_table_sort(self) -> tuple[str, bool]:
        return self._alert_sort_column, self._alert_sort_descending

    def show(self) -> None:
        self._root.title("Space Debris Tracking - Collision Risk Dashboard")
        self._root.geometry("1100x780")
        self._build_ui()
        self._root.deiconify()
        if self._startup_runner is not None:
            self._root.after_idle(self._startup_runner)
        self._root.mainloop()

    def display_error(self, message: str) -> None:
        messagebox.showerror("Dashboard error", message, parent=self._root)

    def display_catalog_count(self, count: int) -> None:
        if self._catalog_label is not None:
            self._catalog_label.config(text=f"Catalog objects: {count}")

    def display_spacecraft_parameters(self, state: SpacecraftState) -> None:
        pos = state.position
        vel = state.velocity
        self._px.set(str(pos.x))
        self._py.set(str(pos.y))
        self._pz.set(str(pos.z))
        self._vx.set(str(vel.x))
        self._vy.set(str(vel.y))
        self._vz.set(str(vel.z))
        self._safety.set(str(state.get_safety_radius_meters()))

    def display_analysis_configuration(self, config: AnalysisConfiguration) -> None:
        self._t_start.set(config.time_window_start_iso8601)
        self._t_end.set(config.time_window_end_iso8601)
        self._dt.set(str(config.time_step_seconds))

    def refresh_alert_table(self, rows: list[EncounterResult]) -> None:
        self._last_alert_rows = list(rows)
        self._redraw_alerts()

    def refresh_timeline(self, events: list[EncounterResult]) -> None:
        if self._timeline_tree is None:
            return
        self._timeline_tree.delete(*self._timeline_tree.get_children())
        ordered = sorted(events, key=lambda e: e.time_of_closest_approach_iso8601)
        for ev in ordered:
            self._timeline_tree.insert(
                "",
                tk.END,
                values=(
                    ev.time_of_closest_approach_iso8601,
                    ev.debris_id,
                    f"{ev.minimum_separation_meters:.2f}",
                    f"{ev.risk_score:.4f}",
                    ev.rank,
                ),
            )

    def refresh_distance_plots(self, series_by_id: Mapping[str, DistanceTimeSeries]) -> None:
        if self._plots_parent is None:
            return
        for child in self._plots_parent.winfo_children():
            child.destroy()

        if not series_by_id:
            ttk.Label(self._plots_parent, text="No separation series (run analysis first).").pack(
                anchor=tk.W
            )
            return

        for debris_id, series in series_by_id.items():
            frame = ttk.Frame(self._plots_parent)
            frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

            fig = Figure(figsize=(5.5, 2.8), dpi=100)
            ax = fig.add_subplot(111)
            xs = list(range(len(series.distance_meters)))
            ys = list(series.distance_meters)
            ax.plot(xs, ys, color="#1f77b4", linewidth=1.5)
            ax.set_title(f"Separation vs sample index — {debris_id}")
            ax.set_xlabel("Sample index (per analysis time step)")
            ax.set_ylabel("Separation (m)")
            ax.grid(True, alpha=0.3)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            NavigationToolbar2Tk(canvas, frame).pack(side=tk.BOTTOM, fill=tk.X)

    def refresh_encounter_geometry(self, geometries: Sequence[EncounterGeometry2D]) -> None:
        if self._geo_parent is None:
            return
        for child in self._geo_parent.winfo_children():
            child.destroy()

        if not geometries:
            ttk.Label(self._geo_parent, text="No geometry data (run analysis first).").pack(anchor=tk.W)
            return

        for geo in geometries:
            frame = ttk.Frame(self._geo_parent)
            frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

            fig = Figure(figsize=(4.5, 4.0), dpi=100)
            ax = fig.add_subplot(111)
            ax.scatter(
                [geo.spacecraft_x_meters],
                [geo.spacecraft_y_meters],
                s=80,
                marker="s",
                color="#2ca02c",
                label="Spacecraft",
                zorder=3,
            )
            ax.scatter(
                [geo.debris_x_meters],
                [geo.debris_y_meters],
                s=70,
                marker="o",
                color="#d62728",
                label=f"Debris {geo.debris_id}",
                zorder=3,
            )
            ax.plot(
                [geo.spacecraft_x_meters, geo.debris_x_meters],
                [geo.spacecraft_y_meters, geo.debris_y_meters],
                "k--",
                alpha=0.45,
                linewidth=1,
            )
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlabel("X (m)")
            ax.set_ylabel("Y (m)")
            ax.set_title(f"XY encounter geometry @ TCA — {geo.debris_id}")
            ax.legend(loc="best", fontsize=8)
            ax.grid(True, alpha=0.3)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            NavigationToolbar2Tk(canvas, frame).pack(side=tk.BOTTOM, fill=tk.X)

    def on_export_csv_requested(self, path: str) -> None:
        if self._controller is not None:
            self._controller.handle_export_csv(path)

    def on_run_analysis_requested(self) -> None:
        if self._controller is not None:
            self._controller.handle_run_analysis()

    # --- UI wiring ---------------------------------------------------------

    def _build_ui(self) -> None:
        root = self._root

        top = ttk.Frame(root, padding=8)
        top.pack(side=tk.TOP, fill=tk.X)

        self._catalog_label = ttk.Label(top, text="Catalog objects: —")
        self._catalog_label.pack(side=tk.LEFT)

        ttk.Button(top, text="Browse CSV...", command=self._browse_catalog).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Button(top, text="Load catalog", command=self._load_catalog).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Entry(top, textvariable=self._path_var, width=70).pack(side=tk.RIGHT, fill=tk.X, expand=True)

        cfg = ttk.LabelFrame(root, text="Spacecraft & analysis window", padding=8)
        cfg.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0, 4))

        grid = ttk.Frame(cfg)
        grid.pack(fill=tk.X)

        def add_row(r: int, label: str, var: tk.StringVar) -> None:
            ttk.Label(grid, text=label).grid(row=r, column=0, sticky=tk.W, padx=(0, 6), pady=2)
            ttk.Entry(grid, textvariable=var, width=22).grid(row=r, column=1, sticky=tk.W, pady=2)

        add_row(0, "Position x (m)", self._px)
        add_row(1, "Position y (m)", self._py)
        add_row(2, "Position z (m)", self._pz)
        add_row(3, "Velocity vx (m/s)", self._vx)
        add_row(4, "Velocity vy (m/s)", self._vy)
        add_row(5, "Velocity vz (m/s)", self._vz)
        add_row(6, "Safety radius (m)", self._safety)
        add_row(7, "Window start (ISO8601)", self._t_start)
        add_row(8, "Window end (ISO8601)", self._t_end)
        add_row(9, "Time step (s)", self._dt)

        btn_row = ttk.Frame(cfg)
        btn_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btn_row, text="Apply to model", command=self._apply_parameters).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Run analysis", command=self._run_clicked).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(btn_row, text="Export results CSV...", command=self._export_clicked).pack(side=tk.LEFT, padx=(8, 0))

        sort_row = ttk.Frame(root, padding=(8, 0))
        sort_row.pack(fill=tk.X)
        ttk.Label(sort_row, text="Alert table sort:").pack(side=tk.LEFT)
        self._sort_combo = ttk.Combobox(
            sort_row, values=list(ALERT_SORT_COLUMNS), state="readonly", width=28
        )
        self._sort_combo.set(self._alert_sort_column)
        self._sort_combo.pack(side=tk.LEFT, padx=(6, 12))
        self._sort_combo.bind("<<ComboboxSelected>>", self._on_sort_changed)
        ttk.Checkbutton(sort_row, text="Descending", variable=self._desc_var, command=self._on_sort_changed).pack(
            side=tk.LEFT
        )

        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        alerts_tab = ttk.Frame(notebook, padding=4)
        timeline_tab = ttk.Frame(notebook, padding=4)
        plots_tab = ttk.Frame(notebook, padding=4)
        geo_tab = ttk.Frame(notebook, padding=4)
        notebook.add(alerts_tab, text="Alerts")
        notebook.add(timeline_tab, text="Timeline")
        notebook.add(plots_tab, text="Separation plots")
        notebook.add(geo_tab, text="Encounter geometry")

        cols = ("rank", "debris_id", "min_sep", "tca", "v_rel", "risk")
        self._alert_tree = ttk.Treeview(
            alerts_tab, columns=cols, show="headings", height=14, selectmode=tk.BROWSE
        )
        headings = {
            "rank": "Rank",
            "debris_id": "Debris ID",
            "min_sep": "Min sep (m)",
            "tca": "TCA (UTC)",
            "v_rel": "|v_rel| (m/s)",
            "risk": "Risk",
        }
        widths = {"rank": 50, "debris_id": 110, "min_sep": 100, "tca": 220, "v_rel": 100, "risk": 80}
        for c in cols:
            self._alert_tree.heading(c, text=headings[c])
            self._alert_tree.column(c, width=widths[c], anchor=tk.CENTER if c == "rank" else tk.W)
        scroll_a = ttk.Scrollbar(alerts_tab, orient=tk.VERTICAL, command=self._alert_tree.yview)
        self._alert_tree.configure(yscrollcommand=scroll_a.set)
        self._alert_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_a.pack(side=tk.RIGHT, fill=tk.Y)

        tcols = ("tca", "debris_id", "min_sep", "risk", "rank")
        self._timeline_tree = ttk.Treeview(
            timeline_tab, columns=tcols, show="headings", height=16, selectmode=tk.BROWSE
        )
        thead = {
            "tca": "TCA (UTC)",
            "debris_id": "Debris ID",
            "min_sep": "Min sep (m)",
            "risk": "Risk",
            "rank": "Rank",
        }
        tw = {"tca": 220, "debris_id": 110, "min_sep": 100, "risk": 80, "rank": 50}
        for c in tcols:
            self._timeline_tree.heading(c, text=thead[c])
            self._timeline_tree.column(c, width=tw[c], anchor=tk.W)
        scroll_t = ttk.Scrollbar(timeline_tab, orient=tk.VERTICAL, command=self._timeline_tree.yview)
        self._timeline_tree.configure(yscrollcommand=scroll_t.set)
        self._timeline_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_t.pack(side=tk.RIGHT, fill=tk.Y)

        plots_canvas = tk.Canvas(plots_tab, highlightthickness=0)
        plots_scroll = ttk.Scrollbar(plots_tab, orient=tk.VERTICAL, command=plots_canvas.yview)
        self._plots_parent = ttk.Frame(plots_canvas)
        self._plots_parent.bind(
            "<Configure>",
            lambda e: plots_canvas.configure(scrollregion=plots_canvas.bbox("all")),
        )
        plots_canvas.create_window((0, 0), window=self._plots_parent, anchor=tk.NW)
        plots_canvas.configure(yscrollcommand=plots_scroll.set)
        plots_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        plots_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        geo_canvas = tk.Canvas(geo_tab, highlightthickness=0)
        geo_scroll = ttk.Scrollbar(geo_tab, orient=tk.VERTICAL, command=geo_canvas.yview)
        self._geo_parent = ttk.Frame(geo_canvas)
        self._geo_parent.bind(
            "<Configure>", lambda e: geo_canvas.configure(scrollregion=geo_canvas.bbox("all"))
        )
        geo_canvas.create_window((0, 0), window=self._geo_parent, anchor=tk.NW)
        geo_canvas.configure(yscrollcommand=geo_scroll.set)
        geo_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        geo_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._sort_combo.set(self._alert_sort_column)
        self._desc_var.set(self._alert_sort_descending)

    def _browse_catalog(self) -> None:
        path = filedialog.askopenfilename(
            parent=self._root,
            title="Select debris catalog CSV",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self._path_var.set(path)

    def _load_catalog(self) -> None:
        path = self._path_var.get().strip()
        if not path:
            self.display_error("Choose a catalog CSV path first.")
            return
        if self._controller is not None:
            self._controller.handle_load_catalog(path)

    def _parse_float(self, raw: str, label: str) -> float:
        try:
            return float(raw.strip())
        except ValueError as exc:
            raise ValueError(f"{label} must be a number.") from exc

    def _apply_parameters(self) -> None:
        if self._controller is None:
            return
        try:
            x = self._parse_float(self._px.get(), "Position x")
            y = self._parse_float(self._py.get(), "Position y")
            z = self._parse_float(self._pz.get(), "Position z")
            vx = self._parse_float(self._vx.get(), "Velocity vx")
            vy = self._parse_float(self._vy.get(), "Velocity vy")
            vz = self._parse_float(self._vz.get(), "Velocity vz")
            safety = self._parse_float(self._safety.get(), "Safety radius")
            dt = self._parse_float(self._dt.get(), "Time step")
            cfg = AnalysisConfiguration(
                time_window_start_iso8601=self._t_start.get().strip(),
                time_window_end_iso8601=self._t_end.get().strip(),
                time_step_seconds=dt,
            )
            self._controller.handle_set_analysis_configuration(cfg)
            self._controller.handle_set_spacecraft_parameters(x, y, z, vx, vy, vz, safety)
        except ValueError as exc:
            self.display_error(str(exc))

    def _run_clicked(self) -> None:
        self._apply_parameters()
        self.on_run_analysis_requested()

    def _export_clicked(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self._root,
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
            title="Export ranked encounters",
        )
        if path:
            self.on_export_csv_requested(path)

    def _on_sort_changed(self, *_args: object) -> None:
        if self._sort_combo is None:
            return
        col = self._sort_combo.get().strip().lower()
        if col not in ALERT_SORT_COLUMNS:
            return
        self._alert_sort_column = col
        self._alert_sort_descending = bool(self._desc_var.get())
        self._redraw_alerts()

    def _redraw_alerts(self) -> None:
        if self._alert_tree is None:
            return
        self._alert_tree.delete(*self._alert_tree.get_children())
        if not self._last_alert_rows:
            return
        rows = sort_encounters(self._last_alert_rows, self._alert_sort_column, self._alert_sort_descending)
        for row in rows:
            self._alert_tree.insert(
                "",
                tk.END,
                values=(
                    row.rank,
                    row.debris_id,
                    f"{row.minimum_separation_meters:.2f}",
                    row.time_of_closest_approach_iso8601,
                    f"{row.relative_velocity_meters_per_second:.2f}",
                    f"{row.risk_score:.4f}",
                ),
            )
