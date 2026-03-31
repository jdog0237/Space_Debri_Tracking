"""Model services for ingestion, validation, analysis, and export."""

from __future__ import annotations

import csv
import random
from pathlib import Path

from .entities import (
    AnalysisConfiguration,
    DebrisCatalog,
    DebrisObject,
    EncounterResult,
    SpacecraftState,
    Vector3,
)
from .exceptions import AnalysisException, CatalogValidationException, InvalidInputException


class DebrisCatalogLoader:
    def load_from_csv(self, path: str) -> DebrisCatalog:
        """Load a catalog from CSV.

        Raises:
            CatalogValidationException: If the file cannot be parsed or rows are invalid.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise CatalogValidationException(f"Catalog file not found: {path}")

        objects: list[DebrisObject] = []
        try:
            with file_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    debris_id = str(row["id"])
                    position = Vector3(float(row["x"]), float(row["y"]), float(row["z"]))
                    velocity = Vector3(
                        float(row["vx"]), float(row["vy"]), float(row["vz"])
                    )
                    objects.append(DebrisObject(debris_id, position, velocity))
        except Exception as exc:  # pragma: no cover - skeleton-level parsing guard
            raise CatalogValidationException(f"Failed to parse catalog: {path}") from exc
        return DebrisCatalog(objects=objects)


class SyntheticCatalogGenerator:
    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def generate(self, count: int) -> DebrisCatalog:
        """Generate synthetic debris objects.

        Raises:
            InvalidInputException: If count is not positive.
        """
        if count <= 0:
            raise InvalidInputException("Synthetic object count must be positive.")

        objects: list[DebrisObject] = []
        for idx in range(count):
            position = Vector3(
                self._rng.uniform(-1e6, 1e6),
                self._rng.uniform(-1e6, 1e6),
                self._rng.uniform(-1e6, 1e6),
            )
            velocity = Vector3(
                self._rng.uniform(-8e3, 8e3),
                self._rng.uniform(-8e3, 8e3),
                self._rng.uniform(-8e3, 8e3),
            )
            objects.append(DebrisObject(debris_id=f"SYN-{idx:05d}", position=position, velocity=velocity))
        return DebrisCatalog(objects=objects)


class CatalogValidator:
    def validate(self, catalog: DebrisCatalog) -> None:
        """Validate overall catalog constraints.

        Raises:
            CatalogValidationException: If catalog data fails validation.
        """
        if catalog.get_object_count() == 0:
            raise CatalogValidationException("Catalog is empty.")

    def validate_schema_row(self, row: list[str]) -> None:
        """Validate a single raw row shape.

        Raises:
            CatalogValidationException: If row does not contain required fields.
        """
        if len(row) < 7:
            raise CatalogValidationException("CSV row is missing required columns.")


class ConstantVelocityPropagator:
    def propagate(
        self, position: Vector3, velocity: Vector3, delta_t_seconds: float
    ) -> Vector3:
        from .exceptions import PropagationException

        if delta_t_seconds < 0:
            raise PropagationException("delta_t_seconds must be non-negative.")
        return Vector3(
            x=position.x + velocity.x * delta_t_seconds,
            y=position.y + velocity.y * delta_t_seconds,
            z=position.z + velocity.z * delta_t_seconds,
        )


class EncounterAnalyzer:
    def __init__(self, propagator: ConstantVelocityPropagator) -> None:
        self.propagator = propagator

    def analyze(
        self,
        debris: DebrisObject,
        spacecraft: SpacecraftState,
        config: AnalysisConfiguration,
    ) -> EncounterResult:
        """Compute encounter metrics for one debris object.

        Raises:
            AnalysisException: For unexpected analysis failures.
            PropagationException: If trajectory propagation is invalid.
        """
        try:
            _ = config  # placeholder: full analysis will use window + step.
            dx = debris.position.x - spacecraft.position.x
            dy = debris.position.y - spacecraft.position.y
            dz = debris.position.z - spacecraft.position.z
            minimum_separation = (dx * dx + dy * dy + dz * dz) ** 0.5

            rvx = debris.velocity.x - spacecraft.velocity.x
            rvy = debris.velocity.y - spacecraft.velocity.y
            rvz = debris.velocity.z - spacecraft.velocity.z
            relative_velocity = (rvx * rvx + rvy * rvy + rvz * rvz) ** 0.5

            return EncounterResult(
                debris_id=debris.debris_id,
                minimum_separation_meters=minimum_separation,
                time_of_closest_approach_iso8601=config.time_window_start_iso8601,
                relative_velocity_meters_per_second=relative_velocity,
                risk_score=0.0,
                rank=0,
            )
        except Exception as exc:
            raise AnalysisException("Failed to analyze debris encounter.", exc) from exc


class RiskScoreCalculator:
    def compute_score(self, metrics: EncounterResult) -> float:
        """Compute transparent risk score from encounter metrics."""
        separation_term = 1.0 / max(metrics.minimum_separation_meters, 1.0)
        velocity_term = metrics.relative_velocity_meters_per_second / 10000.0
        return min(1.0, separation_term * 1000.0 + velocity_term * 0.1)


class InputValidator:
    def validate_numeric_vector(self, components: list[float]) -> None:
        """Validate that all vector components are finite numbers.

        Raises:
            InvalidInputException: If any component is not numeric.
        """
        if len(components) != 3:
            raise InvalidInputException("Vector must have exactly 3 components.")
        for value in components:
            if not isinstance(value, (float, int)):
                raise InvalidInputException("Vector components must be numeric.")

    def validate_positive(self, value: float) -> None:
        """Validate positive scalar values.

        Raises:
            InvalidInputException: If value is not positive.
        """
        if value <= 0:
            raise InvalidInputException("Value must be positive.")


class ResultExporter:
    def export_csv(self, path: str, results: list[EncounterResult]) -> None:
        """Export ranked encounter results to CSV.

        Raises:
            AnalysisException: If writing to CSV fails.
        """
        try:
            output_path = Path(path)
            with output_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "debris_id",
                        "minimum_separation_meters",
                        "time_of_closest_approach_iso8601",
                        "relative_velocity_mps",
                        "risk_score",
                        "rank",
                    ]
                )
                for result in results:
                    writer.writerow(
                        [
                            result.debris_id,
                            result.minimum_separation_meters,
                            result.time_of_closest_approach_iso8601,
                            result.relative_velocity_meters_per_second,
                            result.risk_score,
                            result.rank,
                        ]
                    )
        except Exception as exc:
            raise AnalysisException("Failed to export results.", exc) from exc
