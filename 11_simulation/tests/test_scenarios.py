import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from filling_cell_simulator import FillingCellSimulator
from run_scenarios import SCENARIOS
class ScenarioTests(unittest.TestCase):
 def test_all_required_scenarios_are_safe(self):
  sim=FillingCellSimulator()
  for name in SCENARIOS:
   with self.subTest(name=name):
    result=sim.run(name)
    self.assertFalse(result.pump_cmd)
    self.assertFalse(result.valve_1_cmd)
    self.assertFalse(result.valve_2_cmd)
    self.assertFalse(result.automatic_restart)
    self.assertEqual(result.released,name=="normal_two_bottle_cycle")
 def test_vision_failures_hold(self):
  sim=FillingCellSimulator()
  for name in ["vision_not_ready","vision_result_timeout","stale_inspection_id","low_confidence_inspection","one_bottle_fails"]:
   self.assertEqual(sim.run(name).final_state,"HOLDING")
 def test_power_recovery_requires_start(self):
  result=FillingCellSimulator().run("power_restoration")
  self.assertEqual(result.final_state,"STOPPED"); self.assertFalse(result.released)
if __name__=="__main__": unittest.main()
