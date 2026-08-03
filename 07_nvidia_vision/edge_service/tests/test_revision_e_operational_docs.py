from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RevisionEOperationalDocumentationTests(unittest.TestCase):
    def test_offline_policy_forbids_queue_and_cross_transaction_replay(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        for required in [
            "no offline request, image or result queue",
            "one immutable result",
            "forces ready low",
            "never silently reused for another bottle",
        ]:
            self.assertIn(required, text)

    def test_rollback_is_bounded_and_fail_closed(self) -> None:
        text = (ROOT / "opcua_adapter_runbook.md").read_text(encoding="utf-8").lower()
        for required in [
            "controlled adapter rollback",
            "stop `fc01-vision-edge.service`",
            "restore the previously reviewed versioned adapter package",
            "revalidate application/user certificate identity",
            "validate all 27 nodeids",
            "no automatic production restart",
        ]:
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
