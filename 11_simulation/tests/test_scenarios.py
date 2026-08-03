import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from filling_cell_simulator import FillingCellSimulator, MachineState, SCENARIOS


class ScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = {name: FillingCellSimulator().run(name) for name in SCENARIOS}

    def test_all_canonical_scenarios_execute_with_no_invariant_violation(self):
        self.assertEqual(len(SCENARIOS), 32)
        for name, result in self.results.items():
            with self.subTest(name=name):
                self.assertGreater(len(result.trace), 10)
                self.assertEqual(result.invariant_violations, ())
                self.assertFalse(result.automatic_restart)
                self.assertFalse(result.pump_cmd)
                self.assertFalse(result.valve_1_cmd)
                self.assertFalse(result.valve_2_cmd)

    def test_only_normal_cycle_releases(self):
        released = [name for name, result in self.results.items() if result.released]
        self.assertEqual(released, ["normal_two_bottle_cycle"])

    def test_normal_cycle_has_required_intermediate_transitions(self):
        result = self.results["normal_two_bottle_cycle"]
        states = [state for _, state in result.transitions]
        required_order = [
            MachineState.STOPPED.value,
            MachineState.INITIALIZING.value,
            MachineState.READY.value,
            MachineState.INDEXING.value,
            MachineState.GATE_CLOSING.value,
            MachineState.CLAMPING.value,
            MachineState.ZEROING.value,
            MachineState.FILLING.value,
            MachineState.DRIP_SETTLE.value,
            MachineState.VISION_REQUEST.value,
            MachineState.VISION_WAIT.value,
            MachineState.TRANSFER.value,
            MachineState.CAPPER_WAIT_BUSY.value,
            MachineState.CAPPER_WAIT_COMPLETE.value,
            MachineState.READY.value,
        ]
        cursor = 0
        for state in states:
            if cursor < len(required_order) and state == required_order[cursor]:
                cursor += 1
        self.assertEqual(cursor, len(required_order), states)
        self.assertEqual(result.inspection_id, result.result_id)
        self.assertGreaterEqual(result.pulse_1, 500)
        self.assertGreaterEqual(result.pulse_2, 500)

    def test_channels_close_independently_before_common_pump_stops(self):
        trace = self.results["normal_two_bottle_cycle"].trace
        ch1_closed_while_ch2_fills = [
            sample
            for sample in trace
            if sample.state == MachineState.FILLING.value
            and sample.pump_cmd
            and not sample.valve_1_cmd
            and sample.valve_2_cmd
        ]
        self.assertTrue(ch1_closed_while_ch2_fills)
        self.assertGreater(ch1_closed_while_ch2_fills[0].pulse_1, 490)

    def test_fault_injections_produce_specific_first_out_diagnostics(self):
        expected = {
            "flow_channel_no_pulse": "FLOW_1_NO_PULSE",
            "flow_analog_pulse_disagreement": "FLOW_1_ANALOG_PULSE_DISAGREEMENT",
            "valve_fails_to_close": "VALVE_1_FAILS_TO_CLOSE",
            "pump_vfd_fault": "PUMP_VFD_FAULT",
            "conveyor_vfd_fault": "CONVEYOR_VFD_FAULT",
            "gate_timeout": "GATE_CLOSE_TIMEOUT",
            "clamp_timeout": "CLAMP_ENGAGE_TIMEOUT",
            "capper_busy_timeout": "CAPPER_BUSY_TIMEOUT",
        }
        for scenario, fault in expected.items():
            with self.subTest(scenario=scenario):
                self.assertEqual(self.results[scenario].fault_code, fault)

    def test_all_vision_uncertainty_or_failure_cases_hold(self):
        cases = [
            "underfill",
            "overfill",
            "vision_not_ready",
            "vision_result_timeout",
            "stale_inspection_id",
            "low_confidence_inspection",
            "one_bottle_fails",
            "vision_heartbeat_loss",
            "plc_heartbeat_loss",
        ]
        for scenario in cases:
            with self.subTest(scenario=scenario):
                result = self.results[scenario]
                self.assertEqual(result.final_state, MachineState.HOLDING.value)
                self.assertTrue(result.hold_reason)
                self.assertFalse(result.released)

    def test_recovery_and_reset_do_not_restart(self):
        for scenario in [
            "power_restoration",
            "power_loss_during_filling",
            "hmi_communications_loss",
            "reset_no_restart",
        ]:
            with self.subTest(scenario=scenario):
                result = self.results[scenario]
                self.assertEqual(result.final_state, MachineState.STOPPED.value)
                self.assertFalse(result.released)
                self.assertFalse(result.automatic_restart)
                terminal = result.trace[-1]
                self.assertFalse(terminal.pump_cmd)
                self.assertFalse(terminal.valve_1_cmd)
                self.assertFalse(terminal.valve_2_cmd)


if __name__ == "__main__":
    unittest.main()
