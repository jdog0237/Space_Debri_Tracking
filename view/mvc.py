"""View interface definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from controller.mvc import Controller


class View(ABC):
    @abstractmethod
    def set_controller(self, controller: "Controller") -> None:
        """Attach a controller."""

    @abstractmethod
    def show(self) -> None:
        """Render or show the view."""

    @abstractmethod
    def display_error(self, message: str) -> None:
        """Display an error message."""
