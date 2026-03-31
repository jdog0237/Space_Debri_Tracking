# UML Class Diagram — Space Debris Tracking & Collision Risk Dashboard

This diagram reflects the [SRS](SRS.md) functional requirements (catalog ingestion, spacecraft parameters, constant-velocity analysis, ranked risk, dashboard visualization, CSV export) and an MVC separation with shared eventing. Method signatures use UML-style visibility; **throws** clauses are shown where operations can signal the listed domain exceptions.

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
      -analysisConfig: AnalysisConfiguration
      -lastResults: List~EncounterResult~
      +DebrisTrackingModel()
      +loadCatalogFromCsv(path: String) void
      +setSpacecraftState(state: SpacecraftState) void
      +setAnalysisConfiguration(config: AnalysisConfiguration) void
      +runCollisionAnalysis() void
      +getCatalog() DebrisCatalog
      +getRankedEncounters() List~EncounterResult~
      +exportResultsCsv(path: String) void
    }

    class Vector3 {
      -x: double
      -y: double
      -z: double
      +Vector3(x, y, z)
      +getX() double
      +getY() double
      +getZ() double
    }

    class DebrisObject {
      -id: String
      -position: Vector3
      -velocity: Vector3
      +DebrisObject(id, position, velocity)
      +getId() String
      +getPosition() Vector3
      +getVelocity() Vector3
    }

    class SpacecraftState {
      -position: Vector3
      -velocity: Vector3
      -safetyRadiusMeters: double
      +SpacecraftState(position, velocity, safetyRadiusMeters)
      +getSafetyRadiusMeters() double
    }

    class AnalysisConfiguration {
      -timeWindowStartIso8601: String
      -timeWindowEndIso8601: String
      -timeStepSeconds: double
      +AnalysisConfiguration(start, end, timeStepSeconds)
    }

    class DebrisCatalog {
      -objects: List~DebrisObject~
      +DebrisCatalog(objects)
      +getObjectCount() int
      +getObjects() List~DebrisObject~
    }

    class EncounterResult {
      -debrisId: String
      -minimumSeparationMeters: double
      -timeOfClosestApproachIso8601: String
      -relativeVelocityMetersPerSecond: double
      -riskScore: double
      -rank: int
      +EncounterResult(...)
      +getRiskScore() double
    }

    class DebrisCatalogLoader {
      +DebrisCatalogLoader()
      +loadFromCsv(path: String) DebrisCatalog
    }

    class SyntheticCatalogGenerator {
      -randomSeed: long
      +SyntheticCatalogGenerator(seed: long)
      +generate(count: int) DebrisCatalog
    }

    class CatalogValidator {
      +CatalogValidator()
      +validate(catalog: DebrisCatalog) void
      +validateSchemaRow(row: String[]) void
    }

    class ConstantVelocityPropagator {
      +ConstantVelocityPropagator()
      +propagate(position: Vector3, velocity: Vector3, deltaTSeconds: double) Vector3
    }

    class EncounterAnalyzer {
      +EncounterAnalyzer(propagator: ConstantVelocityPropagator)
      +analyze(debris: DebrisObject, spacecraft: SpacecraftState, config: AnalysisConfiguration) EncounterResult
    }

    class RiskScoreCalculator {
      +RiskScoreCalculator()
      +computeScore(metrics: EncounterResult) double
    }

    class InputValidator {
      +InputValidator()
      +validateNumericVector(components: double[]) void
      +validatePositive(value: double) void
    }

    class ResultExporter {
      +ResultExporter()
      +exportCsv(path: String, results: List~EncounterResult~) void
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
      +setController(controller: Controller) void
      +show() void
      +displayError(message: String) void
    }

    class DashboardView {
      -controller: Controller
      +DashboardView()
      +setController(controller) void
      +show() void
      +displayError(message) void
      +refreshAlertTable(rows: List~EncounterResult~) void
      +refreshTimeline(events: List~EncounterResult~) void
      +refreshDistancePlots(series: Object) void
      +refreshEncounterGeometry(viewModel: Object) void
      +onExportCsvRequested(path: String) void
      +onRunAnalysisRequested() void
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
      +getModel() Model
      +getView() View
      +initialize() void
      #wireViewActions() void
    }

    class DashboardController {
      -debrisModel: DebrisTrackingModel
      -dashboardView: DashboardView
      +DashboardController(model: DebrisTrackingModel, view: DashboardView)
      +initialize() void
      +handleLoadCatalog(path: String) void
      +handleRunAnalysis() void
      +handleExportCsv(path: String) void
      +handleModelEvent(event: ModelEvent) void
    }

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

  %% Exceptions — dependency (operations throw)
  DebrisCatalogLoader ..> CatalogValidationException : throws
  CatalogValidator ..> CatalogValidationException : throws
  SyntheticCatalogGenerator ..> InvalidInputException : throws
  InputValidator ..> InvalidInputException : throws
  DebrisTrackingModel ..> CatalogValidationException : throws
  DebrisTrackingModel ..> InvalidInputException : throws
  DebrisTrackingModel ..> AnalysisException : throws
  EncounterAnalyzer ..> AnalysisException : throws
  EncounterAnalyzer ..> PropagationException : throws
  ResultExporter ..> AnalysisException : throws

  %% Listener pattern
  AbstractModel ..> ModelListener
  ModelEvent ..> Model : references source
```

---

## Operation ↔ exception mapping (first pass)

| Operation | Throws |
|-----------|--------|
| `DebrisCatalogLoader.loadFromCsv` | `CatalogValidationException` |
| `CatalogValidator.validate` / `validateSchemaRow` | `CatalogValidationException` |
| `SyntheticCatalogGenerator.generate` | `InvalidInputException` |
| `InputValidator.validateNumericVector` / `validatePositive` | `InvalidInputException` |
| `DebrisTrackingModel.loadCatalogFromCsv` | `CatalogValidationException`, `InvalidInputException` |
| `DebrisTrackingModel.setSpacecraftState` | `InvalidInputException` |
| `DebrisTrackingModel.runCollisionAnalysis` | `AnalysisException`, `PropagationException` |
| `DebrisTrackingModel.exportResultsCsv` | `AnalysisException` |
| `EncounterAnalyzer.analyze` | `AnalysisException`, `PropagationException` |
| `ConstantVelocityPropagator.propagate` | `PropagationException` (e.g. invalid time step) |

---

## Notes

- **FR coverage:** catalog CSV/synthetic (FR-1.x), spacecraft vectors and validation (FR-2.x), constant-velocity simulation and metrics + risk + ranking (FR-3.x), dashboard surfaces and CSV export (FR-4.x).
- **MVC:** `Model` / `AbstractModel` / `DebrisTrackingModel` hold state and notify `ModelListener`; `View` / `DashboardView` present alerts, timeline, plots, and geometry; `Controller` / `AbstractController` / `DashboardController` coordinate user actions and model updates. `SpaceDebrisApplication.main` is the entry point that wires concrete MVC instances.
- **Reverse engineering:** When you implement packages in code, regenerate a diagram from the codebase (e.g. Pyreverse, PlantUML from annotations, or IDE UML export) and replace or supplement this document for consistency.
