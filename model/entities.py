"""Domain entities and value objects for analysis state."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Vector3:
    x: float
    y: float
    z: float

    def get_x(self) -> float:
        return self.x

    def get_y(self) -> float:
        return self.y

    def get_z(self) -> float:
        return self.z


@dataclass(frozen=True, slots=True)
class DebrisObject:
    debris_id: str
    position: Vector3
    velocity: Vector3

    def get_id(self) -> str:
        return self.debris_id

    def get_position(self) -> Vector3:
        return self.position

    def get_velocity(self) -> Vector3:
        return self.velocity


@dataclass(frozen=True, slots=True)
class SpacecraftState:
    position: Vector3
    velocity: Vector3
    safety_radius_meters: float

    def get_safety_radius_meters(self) -> float:
        return self.safety_radius_meters


@dataclass(frozen=True, slots=True)
class AnalysisConfiguration:
    time_window_start_iso8601: str
    time_window_end_iso8601: str
    time_step_seconds: float


@dataclass(slots=True)
class DebrisCatalog:
    objects: list[DebrisObject] = field(default_factory=list)

    def get_object_count(self) -> int:
        return len(self.objects)

    def get_objects(self) -> list[DebrisObject]:
        return list(self.objects)


@dataclass(slots=True)
class EncounterResult:
    debris_id: str
    minimum_separation_meters: float
    time_of_closest_approach_iso8601: str
    relative_velocity_meters_per_second: float
    risk_score: float
    rank: int = 0

    def get_risk_score(self) -> float:
        return self.risk_score
