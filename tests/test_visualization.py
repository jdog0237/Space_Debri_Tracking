import unittest

from model import AnalysisConfiguration, DebrisTrackingModel, SpacecraftState, Vector3
from model.entities import DebrisCatalog, DebrisObject
from model.services import ConstantVelocityPropagator, sample_separation_time_series


class TestVisualizationSampling(unittest.TestCase):
    def test_sampled_minimum_near_analytic_encounter(self) -> None:
        model = DebrisTrackingModel()
        spacecraft = SpacecraftState(
            position=Vector3(0.0, 0.0, 0.0),
            velocity=Vector3(1.0, 0.0, 0.0),
            safety_radius_meters=25.0,
        )
        config = AnalysisConfiguration(
            time_window_start_iso8601="2026-03-30T00:00:00Z",
            time_window_end_iso8601="2026-03-30T00:01:00Z",
            time_step_seconds=1.0,
        )
        debris = DebrisObject(
            debris_id="D1",
            position=Vector3(100.0, 0.0, 0.0),
            velocity=Vector3(-1.0, 0.0, 0.0),
        )
        model.catalog = DebrisCatalog(objects=[debris])
        model.spacecraft = spacecraft
        model.analysis_config = config

        model.run_collision_analysis()
        analytic = model.get_ranked_encounters()[0]

        series = sample_separation_time_series(
            debris,
            spacecraft,
            config,
            ConstantVelocityPropagator(),
        )
        sampled_min = min(series.distance_meters)
        self.assertAlmostEqual(sampled_min, analytic.minimum_separation_meters, places=3)


if __name__ == "__main__":
    unittest.main()
