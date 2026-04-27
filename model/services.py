"""Model services for ingestion, validation, analysis, and export."""

from __future__ import annotations

import csv
import math
import random
from datetime import datetime, timezone
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
                fieldnames = reader.fieldnames
                if not fieldnames:
                    raise CatalogValidationException("CSV is missing a header row.")

                normalized_to_actual: dict[str, str] = {
                    name.strip().lower(): name for name in fieldnames if name is not None
                }
                required_aliases: dict[str, tuple[str, ...]] = {
                    "id": ("id", "debris_id", "object_id"),
                    "x": ("x",),
                    "y": ("y",),
                    "z": ("z",),
                    "vx": ("vx",),
                    "vy": ("vy",),
                    "vz": ("vz",),
                }

                def resolve_column(canonical: str) -> str:
                    aliases = required_aliases[canonical]
                    for alias in aliases:
                        if alias in normalized_to_actual:
                            return normalized_to_actual[alias]
                    raise CatalogValidationException(
                        f"CSV header missing required column for '{canonical}'. "
                        f"Expected one of: {', '.join(aliases)}"
                    )

                col_id = resolve_column("id")
                col_x = resolve_column("x")
                col_y = resolve_column("y")
                col_z = resolve_column("z")
                col_vx = resolve_column("vx")
                col_vy = resolve_column("vy")
                col_vz = resolve_column("vz")

                def parse_float(raw: object, *, row_number: int, column: str) -> float:
                    text = "" if raw is None else str(raw).strip()
                    if text == "":
                        raise CatalogValidationException(
                            f"Row {row_number}: column '{column}' is empty."
                        )
                    try:
                        value = float(text)
                    except ValueError as exc:
                        raise CatalogValidationException(
                            f"Row {row_number}: column '{column}' must be a number (got {text!r})."
                        ) from exc
                    if not math.isfinite(value):
                        raise CatalogValidationException(
                            f"Row {row_number}: column '{column}' must be finite (got {text!r})."
                        )
                    return value

                # DictReader row numbers start after the header; header is line 1.
                for idx, row in enumerate(reader, start=2):
                    debris_id = "" if row.get(col_id) is None else str(row.get(col_id)).strip()
                    if debris_id == "":
                        raise CatalogValidationException(f"Row {idx}: column '{col_id}' is empty.")

                    position = Vector3(
                        parse_float(row.get(col_x), row_number=idx, column=col_x),
                        parse_float(row.get(col_y), row_number=idx, column=col_y),
                        parse_float(row.get(col_z), row_number=idx, column=col_z),
                    )
                    velocity = Vector3(
                        parse_float(row.get(col_vx), row_number=idx, column=col_vx),
                        parse_float(row.get(col_vy), row_number=idx, column=col_vy),
                        parse_float(row.get(col_vz), row_number=idx, column=col_vz),
                    )
                    objects.append(DebrisObject(debris_id=debris_id, position=position, velocity=velocity))
        except CatalogValidationException:
            raise
        except Exception as exc:  # pragma: no cover - unexpected parsing guard
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
        seen_ids: set[str] = set()
        for obj in catalog.get_objects():
            debris_id = obj.get_id()
            if debris_id.strip() == "":
                raise CatalogValidationException("Catalog contains a debris object with an empty id.")
            if debris_id in seen_ids:
                raise CatalogValidationException(f"Catalog contains duplicate debris id: {debris_id}")
            seen_ids.add(debris_id)

            for label, vector in (("position", obj.get_position()), ("velocity", obj.get_velocity())):
                components = (vector.x, vector.y, vector.z)
                if any(not isinstance(value, (float, int)) for value in components):
                    raise CatalogValidationException(
                        f"Catalog contains non-numeric {label} components for debris id: {debris_id}"
                    )
                if any(not math.isfinite(float(value)) for value in components):
                    raise CatalogValidationException(
                        f"Catalog contains non-finite {label} components for debris id: {debris_id}"
                    )

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
            start_utc = self._parse_iso8601_utc(config.time_window_start_iso8601)
            end_utc = self._parse_iso8601_utc(config.time_window_end_iso8601)
            window_seconds = (end_utc - start_utc).total_seconds()
            if window_seconds < 0:
                raise AnalysisException("Analysis time window end must be after start.")

            rel_position = Vector3(
                x=debris.position.x - spacecraft.position.x,
                y=debris.position.y - spacecraft.position.y,
                z=debris.position.z - spacecraft.position.z,
            )
            rel_velocity = Vector3(
                x=debris.velocity.x - spacecraft.velocity.x,
                y=debris.velocity.y - spacecraft.velocity.y,
                z=debris.velocity.z - spacecraft.velocity.z,
            )
            rel_speed_squared = (
                rel_velocity.x * rel_velocity.x
                + rel_velocity.y * rel_velocity.y
                + rel_velocity.z * rel_velocity.z
            )

            # Compute unconstrained TCA analytically for linear relative motion,
            # then clamp to the configured analysis window.
            if rel_speed_squared <= 0.0:
                tca_seconds = 0.0
            else:
                numerator = -(
                    rel_position.x * rel_velocity.x
                    + rel_position.y * rel_velocity.y
                    + rel_position.z * rel_velocity.z
                )
                tca_seconds = numerator / rel_speed_squared
            tca_seconds = max(0.0, min(window_seconds, tca_seconds))

            debris_at_tca = self.propagator.propagate(
                position=debris.position,
                velocity=debris.velocity,
                delta_t_seconds=tca_seconds,
            )
            spacecraft_at_tca = self.propagator.propagate(
                position=spacecraft.position,
                velocity=spacecraft.velocity,
                delta_t_seconds=tca_seconds,
            )

            dx = debris_at_tca.x - spacecraft_at_tca.x
            dy = debris_at_tca.y - spacecraft_at_tca.y
            dz = debris_at_tca.z - spacecraft_at_tca.z
            minimum_separation = (dx * dx + dy * dy + dz * dz) ** 0.5

            relative_velocity = rel_speed_squared**0.5
            tca_iso8601 = (start_utc + (end_utc - start_utc) * (tca_seconds / window_seconds)
                           if window_seconds > 0
                           else start_utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

            return EncounterResult(
                debris_id=debris.debris_id,
                minimum_separation_meters=minimum_separation,
                time_of_closest_approach_iso8601=tca_iso8601,
                relative_velocity_meters_per_second=relative_velocity,
                risk_score=0.0,
                rank=0,
            )
        except AnalysisException:
            raise
        except Exception as exc:
            raise AnalysisException("Failed to analyze debris encounter.", exc) from exc

    @staticmethod
    def _parse_iso8601_utc(value: str) -> datetime:
        iso_value = value.strip()
        if iso_value.endswith("Z"):
            iso_value = iso_value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(iso_value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)


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
