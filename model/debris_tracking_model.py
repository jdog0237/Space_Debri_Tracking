"""Concrete model implementation for collision-risk workflows."""

from __future__ import annotations

from .entities import (
    AnalysisConfiguration,
    DebrisCatalog,
    EncounterResult,
    SpacecraftState,
)
from .exceptions import AnalysisException, InvalidInputException
from .mvc import AbstractModel, AnalysisCompletedEvent
from .services import (
    CatalogValidator,
    DebrisCatalogLoader,
    EncounterAnalyzer,
    InputValidator,
    ResultExporter,
    RiskScoreCalculator,
    SyntheticCatalogGenerator,
    ConstantVelocityPropagator,
)


class DebrisTrackingModel(AbstractModel):
    """Main application model orchestrating ingestion and analysis."""

    def __init__(self) -> None:
        super().__init__()
        self.catalog: DebrisCatalog = DebrisCatalog()
        self.spacecraft: SpacecraftState | None = None
        self.analysis_config: AnalysisConfiguration | None = None
        self.last_results: list[EncounterResult] = []

        self._catalog_loader = DebrisCatalogLoader()
        self._catalog_validator = CatalogValidator()
        self._encounter_analyzer = EncounterAnalyzer(ConstantVelocityPropagator())
        self._risk_calculator = RiskScoreCalculator()
        self._input_validator = InputValidator()
        self._result_exporter = ResultExporter()
        self._synthetic_generator = SyntheticCatalogGenerator(seed=42)

    def load_catalog_from_csv(self, path: str) -> None:
        """Load and validate catalog from CSV.

        Raises:
            CatalogValidationException: If catalog is malformed.
            InvalidInputException: If path is empty.
        """
        if not path:
            raise InvalidInputException("Catalog path cannot be empty.")
        catalog = self._catalog_loader.load_from_csv(path)
        self._catalog_validator.validate(catalog)
        self.catalog = catalog

    def generate_synthetic_catalog(self, count: int) -> None:
        """Generate and validate synthetic catalog.

        Raises:
            InvalidInputException: If count is not positive.
        """
        catalog = self._synthetic_generator.generate(count)
        self._catalog_validator.validate(catalog)
        self.catalog = catalog

    def set_spacecraft_state(self, state: SpacecraftState) -> None:
        """Set spacecraft state.

        Raises:
            InvalidInputException: If safety radius is invalid.
        """
        self._input_validator.validate_positive(state.safety_radius_meters)
        self.spacecraft = state

    def set_analysis_configuration(self, config: AnalysisConfiguration) -> None:
        """Set analysis time-window and step configuration.

        Raises:
            InvalidInputException: If time step is not positive.
        """
        self._input_validator.validate_positive(config.time_step_seconds)
        self.analysis_config = config

    def run_collision_analysis(self) -> None:
        """Execute first-pass collision analysis and rank results.

        Raises:
            AnalysisException: If required model inputs are missing or analysis fails.
        """
        if self.spacecraft is None:
            raise AnalysisException("Spacecraft state must be configured.")
        if self.analysis_config is None:
            raise AnalysisException("Analysis configuration must be configured.")

        results: list[EncounterResult] = []
        for debris in self.catalog.get_objects():
            result = self._encounter_analyzer.analyze(
                debris=debris,
                spacecraft=self.spacecraft,
                config=self.analysis_config,
            )
            result.risk_score = self._risk_calculator.compute_score(result)
            results.append(result)

        results.sort(key=lambda item: item.risk_score, reverse=True)
        for rank, item in enumerate(results, start=1):
            item.rank = rank

        self.last_results = results
        self._fire_event(AnalysisCompletedEvent(source=self, results=results))

    def get_catalog(self) -> DebrisCatalog:
        return self.catalog

    def get_ranked_encounters(self) -> list[EncounterResult]:
        return list(self.last_results)

    def export_results_csv(self, path: str) -> None:
        """Export latest results.

        Raises:
            AnalysisException: If there are no results or writing fails.
        """
        if not self.last_results:
            raise AnalysisException("No analysis results available to export.")
        self._result_exporter.export_csv(path, self.last_results)
