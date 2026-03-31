"""Core MVC interfaces and base model classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class ModelListener(ABC):
    """Interface for objects that react to model updates."""

    @abstractmethod
    def model_changed(self, event: "ModelEvent") -> None:
        """Handle a model change event."""


class Model(ABC):
    """Interface for model event registration and notifications."""

    @abstractmethod
    def add_model_listener(self, listener: ModelListener) -> None:
        """Register a listener."""

    @abstractmethod
    def remove_model_listener(self, listener: ModelListener) -> None:
        """Unregister a listener."""

    @abstractmethod
    def notify_listeners(self, event: "ModelEvent") -> None:
        """Notify listeners about an event."""


@dataclass(slots=True)
class ModelEvent:
    """Base model event."""

    source: Model
    event_type: str
    payload: Any = None
    timestamp_iso8601: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def get_source(self) -> Model:
        return self.source

    def get_event_type(self) -> str:
        return self.event_type

    def get_payload(self) -> Any:
        return self.payload


@dataclass(slots=True)
class AnalysisCompletedEvent(ModelEvent):
    """Model event emitted when analysis results are available."""

    def __init__(self, source: Model, results: list[Any]) -> None:
        super().__init__(
            source=source,
            event_type="analysis_completed",
            payload=results,
        )

    def get_results(self) -> list[Any]:
        return self.payload if isinstance(self.payload, list) else []


class AbstractModel(Model, ABC):
    """Abstract model with listener management."""

    def __init__(self) -> None:
        self._listeners: list[ModelListener] = []

    def add_model_listener(self, listener: ModelListener) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_model_listener(self, listener: ModelListener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def notify_listeners(self, event: ModelEvent) -> None:
        for listener in self._listeners:
            listener.model_changed(event)

    def _fire_event(self, event: ModelEvent) -> None:
        self.notify_listeners(event)
