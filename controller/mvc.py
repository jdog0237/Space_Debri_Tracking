"""Controller interfaces and abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod

from model.mvc import Model
from view.mvc import View


class Controller(ABC):
    @abstractmethod
    def initialize(self) -> None:
        """Initialize controller wiring between model and view."""


class AbstractController(Controller, ABC):
    def __init__(self, model: Model, view: View) -> None:
        self._model = model
        self._view = view

    def get_model(self) -> Model:
        return self._model

    def get_view(self) -> View:
        return self._view

    def initialize(self) -> None:
        self._wire_view_actions()

    @abstractmethod
    def _wire_view_actions(self) -> None:
        """Connect view actions to controller handlers."""
