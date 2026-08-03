import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from filling_cell_simulator import FillingCellSimulator, MachineState, SCENARIOS, SimulationConfig


class DeterministicPropertyTests(unittest.TestCase):
    def test_repeat_runs_are_bit_for_bit_deterministic_at_summary_level(self):
        simulator = FillingCellSimulator()
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                self.assertEqual(simulator.run(scenario).summary_row(), simulator.run(scenario).summary_row())

    def test_safety_properties_hold_across_time_step_grid(self):
        for dt_ms in [10, 20, 40, 50]:
            simulator = FillingCellSimulator(SimulationConfig(dt_ms=dt_ms))
            for scenario in SCENARIOS:
                with self.subTest(dt_ms=dt_ms, scenario=scenario):
                    result = simulator.run(scenario)
                    self.assertEqual(result.invariant_violations, ())
                    self.assertEqual(result.released, scenario == "normal_two_bottle_cycle")
                    self.assertFalse(result.automatic_restart)
                    for sample in result.trace:
                        if sample.pump_cmd:
                            self.assertEqual(sample.state, MachineState.FILLING.value)
                        if sample.valve_1_cmd or sample.valve_2_cmd:
                            self.assertTrue(sample.pump_cmd)
                        if not sample.power_available:
                            self.assertFalse(sample.conveyor_cmd)
                            self.assertFalse(sample.pump_cmd)
                            self.assertFalse(sample.valve_1_cmd)
                            self.assertFalse(sample.valve_2_cmd)
                        if sample.released:
                            self.assertTrue(sample.capper_complete)

    def test_normal_cycle_scales_over_recipe_target_grid(self):
        # The simulated valve closure volume remains within the independent vision
        # tolerance over the supported 400-700 ml recipe envelope.
        for target in [400, 500, 700]:
            config = SimulationConfig(
                target_pulses=(target, target),
                target_volume_ml=float(target),
                max_time_ms=18_000,
            )
            result = FillingCellSimulator(config).run("normal_two_bottle_cycle")
            with self.subTest(target=target):
                self.assertTrue(result.released)
                self.assertGreaterEqual(result.pulse_1, target)
                self.assertGreaterEqual(result.pulse_2, target)
                self.assertEqual(result.invariant_violations, ())

    def test_transition_timestamps_are_monotonic_and_states_do_not_chatter(self):
        for scenario in SCENARIOS:
            result = FillingCellSimulator().run(scenario)
            with self.subTest(scenario=scenario):
                times = [time_ms for time_ms, _ in result.transitions]
                states = [state for _, state in result.transitions]
                self.assertEqual(times, sorted(times))
                self.assertTrue(all(left != right for left, right in zip(states, states[1:])))


if __name__ == "__main__":
    unittest.main()
