import unittest

from model import AnalysisConfiguration, DebrisTrackingModel, SpacecraftState, Vector3
from model.entities import DebrisCatalog, DebrisObject


class TestCollisionAnalysis(unittest.TestCase):
    def setUp(self) -> None:
        self.model = DebrisTrackingModel()
        self.model.set_spacecraft_state(
            SpacecraftState(
                position=Vector3(0.0, 0.0, 0.0),
                velocity=Vector3(1.0, 0.0, 0.0),
                safety_radius_meters=25.0,
            )
        )
        self.model.set_analysis_configuration(
            AnalysisConfiguration(
                time_window_start_iso8601="2026-03-30T00:00:00Z",
                time_window_end_iso8601="2026-03-30T00:01:00Z",
                time_step_seconds=1.0,
            )
        )

    def test_tca_and_minimum_separation_are_computed_in_window(self) -> None:
        self.model.catalog = DebrisCatalog(
            objects=[
                DebrisObject(
                    debris_id="D1",
                    position=Vector3(100.0, 0.0, 0.0),
                    velocity=Vector3(-1.0, 0.0, 0.0),
                )
            ]
        )

        self.model.run_collision_analysis()
        result = self.model.get_ranked_encounters()[0]

        self.assertEqual(result.time_of_closest_approach_iso8601, "2026-03-30T00:00:50Z")
        self.assertAlmostEqual(result.minimum_separation_meters, 0.0, places=6)
        self.assertAlmostEqual(result.relative_velocity_meters_per_second, 2.0, places=6)

    def test_results_are_ranked_by_risk_score_descending(self) -> None:
        self.model.catalog = DebrisCatalog(
            objects=[
                DebrisObject(
                    debris_id="HIGH-RISK",
                    position=Vector3(10.0, 0.0, 0.0),
                    velocity=Vector3(0.0, 0.0, 0.0),
                ),
                DebrisObject(
                    debris_id="LOW-RISK",
                    position=Vector3(10000.0, 0.0, 0.0),
                    velocity=Vector3(0.0, 0.0, 0.0),
                ),
            ]
        )

        self.model.run_collision_analysis()
        results = self.model.get_ranked_encounters()

        self.assertEqual(results[0].debris_id, "HIGH-RISK")
        self.assertEqual(results[0].rank, 1)
        self.assertEqual(results[1].rank, 2)
        self.assertGreaterEqual(results[0].risk_score, results[1].risk_score)


if __name__ == "__main__":
    unittest.main()
