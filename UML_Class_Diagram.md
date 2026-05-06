# UML Class Diagram — Space Debris Tracking & Collision Risk Dashboard

This diagram reflects the [SRS](SRS.md) functional requirements (catalog ingestion, spacecraft parameters, constant-velocity analysis, ranked risk, dashboard visualization, CSV export) and an MVC separation with shared eventing. **Reverse-engineered from the Python codebase** (Task 4 console visualization). Method signatures mix Python identifiers (`snake_case`) with UML-style types where helpful; **throws** clauses are shown where operations can signal the listed domain exceptions.

Module-level helpers in `model/services.py` (`parse_iso8601_utc`, `compute_tca_seconds_in_window`, `sample_separation_time_series`, `build_encounter_geometry_xy`) implement shared timing/propagation math used by both `EncounterAnalyzer` and `DebrisTrackingModel.build_visualization_data`—shown below only via dependency notes.

---

## Class diagram (Mermaid)

```mermaid
classDiagram
  direction TB

  subgraph model["«package» model"]
    class Model {
      <<interface>>
      +addModelListener(listener: ModelListener) void
      +removeModelListener(listener: ModelListener) void
      +notifyListeners(event: ModelEvent) void
    }

    class ModelListener {
      <<interface>>
      +modelChanged(event: ModelEvent) void
    }

    class ModelEvent {
      -source: Model
      -eventType: String
      -timestampIso8601: String
      -payload: Object
      +ModelEvent(source, eventType, payload)
      +getSource() Model
      +getEventType() String
      +getPayload() Object
    }

    class AnalysisCompletedEvent {
      +AnalysisCompletedEvent(source: Model, results: List~EncounterResult~)
      +getResults() List~EncounterResult~
    }

    class AbstractModel {
      <<abstract>>
      -listeners: List~ModelListener~
      +AbstractModel()
      +addModelListener(listener) void
      +removeModelListener(listener) void
      +notifyListeners(event) void
      #fireEvent(event: ModelEvent) void
    }

    class DebrisTrackingModel {
      -catalog: DebrisCatalog
      -spacecraft: SpacecraftState
      -analysis_config: AnalysisConfiguration
      -last_results: List~EncounterResult~
      +DebrisTrackingModel()
      +load_catalog_from_csv(path: String) void
      +generate_synthetic_catalog(count: int) void
      +set_spacecraft_state(state: SpacecraftState) void
      +set_analysis_configuration(config: AnalysisConfiguration) void
      +run_collision_analysis() void
      +get_catalog() DebrisCatalog
      +get_ranked_encounters() List~EncounterResult~
      +build_visualization_data(max_distance_plots: int) Tuple
      +export_results_csv(path: String) void
    }

    class Vector3 {
      -x: double
      -y: double
      -z: double
      +Vector3(x, y, z)
      +get_x() double
      +get_y() double
      +get_z() double
    }

    class DebrisObject {
      -debris_id: String
      -position: Vector3
      -velocity: Vector3
      +DebrisObject(debris_id, position, velocity)
      +get_id() String
      +get_position() Vector3
      +get_velocity() Vector3
    }

    class SpacecraftState {
      -position: Vector3
      -velocity: Vector3
      -safety_radius_meters: double
      +SpacecraftState(position, velocity, safety_radius_meters)
      +get_safety_radius_meters() double
    }

    class AnalysisConfiguration {
      -time_window_start_iso8601: String
      -time_window_end_iso8601: String
      -time_step_seconds: double
      +AnalysisConfiguration(start, end, time_step_seconds)
    }

    class DebrisCatalog {
      -objects: List~DebrisObject~
      +DebrisCatalog(objects)
      +getObjectCount() int
      +getObjects() List~DebrisObject~
    }

    class EncounterResult {
      -debris_id: String
      -minimum_separation_meters: double
      -time_of_closest_approach_iso8601: String
      -relative_velocity_meters_per_second: double
      -risk_score: double
      -rank: int
      +EncounterResult(...)
      +get_risk_score() double
    }

    class DistanceTimeSeries {
      <<value object>>
      -debris_id: String
      -time_iso8601: Tuple~String~
      -distance_meters: Tuple~double~
      +DistanceTimeSeries(debris_id, time_iso8601, distance_meters)
    }

    class EncounterGeometry2D {
      <<value object>>
      -debris_id: String
      -spacecraft_x_meters: double
      -spacecraft_y_meters: double
      -debris_x_meters: double
      -debris_y_meters: double
      -minimum_separation_meters: double
      +EncounterGeometry2D(...)
    }

    class DebrisCatalogLoader {
      +DebrisCatalogLoader()
      +load_from_csv(path: String) DebrisCatalog
    }

    class SyntheticCatalogGenerator {
      +SyntheticCatalogGenerator(seed: long)
      +generate(count: int) DebrisCatalog
    }

    class CatalogValidator {
      +CatalogValidator()
      +validate(catalog: DebrisCatalog) void
      +validate_schema_row(row: String[]) void
    }

    class ConstantVelocityPropagator {
      +ConstantVelocityPropagator()
      +propagate(position: Vector3, velocity: Vector3, delta_t_seconds: double) Vector3
    }

    class EncounterAnalyzer {
      +EncounterAnalyzer(propagator: ConstantVelocityPropagator)
      +analyze(debris: DebrisObject, spacecraft: SpacecraftState, config: AnalysisConfiguration) EncounterResult
    }

    class RiskScoreCalculator {
      +RiskScoreCalculator()
      +compute_score(metrics: EncounterResult) double
    }

    class InputValidator {
      +InputValidator()
      +validate_numeric_vector(components: double[]) void
      +validate_positive(value: double) void
    }

    class ResultExporter {
      +ResultExporter()
      +export_csv(path: String, results: List~EncounterResult~) void
    }

    class CatalogValidationException {
      <<exception>>
      +CatalogValidationException(message: String)
    }

    class InvalidInputException {
      <<exception>>
      +InvalidInputException(message: String)
    }

    class AnalysisException {
      <<exception>>
      +AnalysisException(message: String, cause: Throwable)
    }

    class PropagationException {
      <<exception>>
      +PropagationException(message: String)
    }
  end

  subgraph view["«package» view"]
    class View {
      <<interface>>
      +set_controller(controller: Controller) void
      +show() void
      +display_error(message: String) void
    }

    class DashboardView {
      -controller: Controller
      -alert_sort_column: String
      -alert_sort_descending: bool
      +DashboardView()
      +set_controller(controller) void
      +set_alert_table_sort(column: String, descending: bool) void
      +get_alert_table_sort() Tuple
      +show() void
      +display_error(message) void
      +display_catalog_count(count: int) void
      +display_spacecraft_parameters(state: SpacecraftState) void
      +refresh_alert_table(rows: List~EncounterResult~) void
      +refresh_timeline(events: List~EncounterResult~) void
      +refresh_distance_plots(series_by_id: Map~String, DistanceTimeSeries~) void
      +refresh_encounter_geometry(geometries: List~EncounterGeometry2D~) void
      +on_export_csv_requested(path: String) void
      +on_run_analysis_requested() void
    }
  end

  subgraph controller["«package» controller"]
    class Controller {
      <<interface>>
      +initialize() void
    }

    class AbstractController {
      <<abstract>>
      -model: Model
      -view: View
      +AbstractController(model: Model, view: View)
      +get_model() Model
      +get_view() View
      +initialize() void
      #wire_view_actions() void
    }

    class DashboardController {
      -debris_model: DebrisTrackingModel
      -dashboard_view: DashboardView
      +DashboardController(model: DebrisTrackingModel, view: DashboardView)
      +initialize() void
      +handle_load_catalog(path: String) void
      +handle_generate_synthetic_catalog(count: int) void
      +handle_run_analysis() void
      +handle_export_csv(path: String) void
      +handle_set_spacecraft_parameters(x, y, z, vx, vy, vz, safety_radius_meters) void
      +model_changed(event: ModelEvent) void
      +handle_model_event(event: ModelEvent) void
    }

    note for DashboardController "Also realizes ModelListener via multiple inheritance (DashboardController(AbstractController, ModelListener))."

    class SpaceDebrisApplication {
      +SpaceDebrisApplication()
      +main(args: String[]) void
    }
  end

  %% MVC core — generalization / realization
  Model <|.. AbstractModel : realizes
  AbstractModel <|-- DebrisTrackingModel
  DebrisTrackingModel ..> ModelListener : notifies
  ModelEvent <|-- AnalysisCompletedEvent
  AbstractController ..|> Controller : realizes
  AbstractController ..> Model : uses
  AbstractController ..> View : uses
  DashboardView ..|> View : realizes
  DashboardController --|> AbstractController
  ModelListener <|.. DashboardController : realizes
  DashboardController ..> DebrisTrackingModel
  DashboardController ..> DashboardView
  DebrisTrackingModel ..|> Model : realizes
  SpaceDebrisApplication ..> DashboardController : creates
  SpaceDebrisApplication ..> DebrisTrackingModel : creates
  SpaceDebrisApplication ..> DashboardView : creates

  %% Model — composition / association
  DebrisTrackingModel *-- DebrisCatalog : catalog
  DebrisTrackingModel *-- SpacecraftState
  DebrisTrackingModel *-- AnalysisConfiguration
  DebrisTrackingModel o-- "0..*" EncounterResult : results
  DebrisCatalog o-- "1..*" DebrisObject
  DebrisObject *-- Vector3 : position
  DebrisObject *-- Vector3 : velocity
  SpacecraftState *-- Vector3 : position
  SpacecraftState *-- Vector3 : velocity

  DebrisTrackingModel ..> DebrisCatalogLoader : uses
  DebrisTrackingModel ..> SyntheticCatalogGenerator : uses
  DebrisTrackingModel ..> CatalogValidator : uses
  DebrisTrackingModel ..> EncounterAnalyzer : uses
  DebrisTrackingModel ..> RiskScoreCalculator : uses
  DebrisTrackingModel ..> InputValidator : uses
  DebrisTrackingModel ..> ResultExporter : uses
  EncounterAnalyzer *-- ConstantVelocityPropagator
  EncounterAnalyzer ..> EncounterResult : creates

  DebrisTrackingModel ..> DistanceTimeSeries : builds
  DebrisTrackingModel ..> EncounterGeometry2D : builds
  DashboardView ..> DistanceTimeSeries : renders
  DashboardView ..> EncounterGeometry2D : renders

  %% Exceptions — dependency (operations throw)
  DebrisCatalogLoader ..> CatalogValidationException : throws
  CatalogValidator ..> CatalogValidationException : throws
  SyntheticCatalogGenerator ..> InvalidInputException : throws
  InputValidator ..> InvalidInputException : throws
  DebrisTrackingModel ..> CatalogValidationException : throws
  DebrisTrackingModel ..> InvalidInputException : throws
  DebrisTrackingModel ..> AnalysisException : throws
  DebrisTrackingModel ..> PropagationException : throws
  EncounterAnalyzer ..> AnalysisException : throws
  EncounterAnalyzer ..> PropagationException : throws
  ResultExporter ..> AnalysisException : throws

  %% Listener pattern
  AbstractModel ..> ModelListener
  ModelEvent ..> Model : references source
```

---

## Operation ↔ exception mapping (code-aligned)

| Operation | Throws |
|-----------|--------|
| `DebrisCatalogLoader.load_from_csv` | `CatalogValidationException` |
| `CatalogValidator.validate` / `validate_schema_row` | `CatalogValidationException` |
| `SyntheticCatalogGenerator.generate` | `InvalidInputException` |
| `InputValidator.validate_numeric_vector` / `validate_positive` | `InvalidInputException` |
| `DebrisTrackingModel.load_catalog_from_csv` | `CatalogValidationException`, `InvalidInputException` |
| `DebrisTrackingModel.generate_synthetic_catalog` | `CatalogValidationException`, `InvalidInputException` |
| `DebrisTrackingModel.set_spacecraft_state` | `InvalidInputException` |
| `DebrisTrackingModel.set_analysis_configuration` | `InvalidInputException` |
| `DebrisTrackingModel.run_collision_analysis` | `AnalysisException`, `PropagationException` |
| `DebrisTrackingModel.build_visualization_data` | `AnalysisException` |
| `DebrisTrackingModel.export_results_csv` | `AnalysisException` |
| `EncounterAnalyzer.analyze` | `AnalysisException`, `PropagationException` |
| `sample_separation_time_series` | `AnalysisException` |
| `build_encounter_geometry_xy` | `AnalysisException` |
| `ConstantVelocityPropagator.propagate` | `PropagationException` (negative `delta_t_seconds`) |

---

## Notes

- **FR coverage:** catalog CSV/synthetic (FR-1.x), spacecraft vectors and validation (FR-2.x), constant-velocity simulation and metrics + risk + ranking (FR-3.x), console dashboard surfaces including sortable alerts, TCA timeline, sampled distance plots, XY encounter sketches, and CSV export (FR-4.x).
- **MVC:** `Model` / `AbstractModel` / `DebrisTrackingModel` hold state and notify `ModelListener`; `View` / `DashboardView` renders FR-4 outputs as text; `DashboardController` (`AbstractController` + `ModelListener`) bridges CSV/catalog actions, analysis runs, exports, and visualization refresh on `analysis_completed`. `SpaceDebrisApplication.main` wires MVC and parses CLI flags (`--catalog`, `--export`, `--sort`, `--ascending`).
- **Reverse engineering:** This diagram was updated to match the repository implementation (Python 3.10+, stdlib-only visualization). External diagram generators may still be used for alternate layouts, but names now track `snake_case` Python APIs.
