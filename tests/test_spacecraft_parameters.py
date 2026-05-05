import io
import unittest
from unittest.mock import patch

from controller import DashboardController
from model import (
    DebrisTrackingModel,
    InvalidInputException,
    SpacecraftState,
    Vector3,
)
from model.services import InputValidator


class TestSpacecraftParametersValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.model = DebrisTrackingModel()

    def test_valid_input_sets_spacecraft_state(self) -> None:
        state = SpacecraftState(
            position=Vector3(1.0, -2.5, 3.25),
            velocity=Vector3(100.0, 0.0, -50.0),
            safety_radius_meters=42.0,
        )
        self.model.set_spacecraft_state(state)
        self.assertIsNotNone(self.model.spacecraft)
        self.assertEqual(self.model.spacecraft, state)

    def test_negative_radius_raises_and_preserves_state(self) -> None:
        initial = SpacecraftState(
            position=Vector3(0.0, 0.0, 0.0),
            velocity=Vector3(1.0, 0.0, 0.0),
            safety_radius_meters=10.0,
        )
        self.model.set_spacecraft_state(initial)
        bad = SpacecraftState(
            position=Vector3(0.0, 0.0, 0.0),
            velocity=Vector3(1.0, 0.0, 0.0),
            safety_radius_meters=-1.0,
        )
        with self.assertRaises(InvalidInputException):
            self.model.set_spacecraft_state(bad)
        self.assertEqual(self.model.spacecraft, initial)

    def test_zero_radius_raises(self) -> None:
        with self.assertRaises(InvalidInputException):
            self.model.set_spacecraft_state(
                SpacecraftState(
                    position=Vector3(0.0, 0.0, 0.0),
                    velocity=Vector3(0.0, 0.0, 0.0),
                    safety_radius_meters=0.0,
                )
            )

    def test_nan_in_position_raises(self) -> None:
        with self.assertRaises(InvalidInputException):
            self.model.set_spacecraft_state(
                SpacecraftState(
                    position=Vector3(float("nan"), 0.0, 0.0),
                    velocity=Vector3(0.0, 0.0, 0.0),
                    safety_radius_meters=1.0,
                )
            )

    def test_nan_in_velocity_raises(self) -> None:
        with self.assertRaises(InvalidInputException):
            self.model.set_spacecraft_state(
                SpacecraftState(
                    position=Vector3(0.0, 0.0, 0.0),
                    velocity=Vector3(0.0, float("nan"), 0.0),
                    safety_radius_meters=1.0,
                )
            )

    def test_nan_safety_radius_raises(self) -> None:
        with self.assertRaises(InvalidInputException):
            self.model.set_spacecraft_state(
                SpacecraftState(
                    position=Vector3(0.0, 0.0, 0.0),
                    velocity=Vector3(0.0, 0.0, 0.0),
                    safety_radius_meters=float("nan"),
                )
            )

    def test_infinite_position_component_raises(self) -> None:
        with self.assertRaises(InvalidInputException):
            self.model.set_spacecraft_state(
                SpacecraftState(
                    position=Vector3(float("inf"), 0.0, 0.0),
                    velocity=Vector3(0.0, 0.0, 0.0),
                    safety_radius_meters=1.0,
                )
            )

    def test_infinite_velocity_component_raises(self) -> None:
        with self.assertRaises(InvalidInputException):
            self.model.set_spacecraft_state(
                SpacecraftState(
                    position=Vector3(0.0, 0.0, 0.0),
                    velocity=Vector3(-float("inf"), 0.0, 0.0),
                    safety_radius_meters=1.0,
                )
            )

    def test_infinite_safety_radius_raises(self) -> None:
        with self.assertRaises(InvalidInputException):
            self.model.set_spacecraft_state(
                SpacecraftState(
                    position=Vector3(0.0, 0.0, 0.0),
                    velocity=Vector3(0.0, 0.0, 0.0),
                    safety_radius_meters=float("inf"),
                )
            )


class TestInputValidatorVectors(unittest.TestCase):
    def test_validate_numeric_vector_rejects_wrong_length(self) -> None:
        v = InputValidator()
        with self.assertRaises(InvalidInputException):
            v.validate_numeric_vector([1.0, 2.0])


class TestDashboardControllerSpacecraft(unittest.TestCase):
    def test_handle_set_spacecraft_parameters_success_prints_state(self) -> None:
        from view import DashboardView

        model = DebrisTrackingModel()
        view = DashboardView()
        controller = DashboardController(model, view)
        controller.initialize()
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            controller.handle_set_spacecraft_parameters(
                1.0,
                2.0,
                3.0,
                4.0,
                5.0,
                6.0,
                10.0,
            )
        out = fake_out.getvalue()
        self.assertIn("Spacecraft parameters configured", out)
        self.assertIn("x=1.0", out)
        self.assertIn("Safety radius (m): 10.0", out)
        self.assertIsNotNone(model.spacecraft)

    def test_handle_set_spacecraft_parameters_invalid_shows_error(self) -> None:
        from view import DashboardView

        model = DebrisTrackingModel()
        view = DashboardView()
        controller = DashboardController(model, view)
        controller.initialize()
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            controller.handle_set_spacecraft_parameters(
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                -5.0,
            )
        self.assertIn("[ERROR]", fake_out.getvalue())
        self.assertIsNone(model.spacecraft)


if __name__ == "__main__":
    unittest.main()
