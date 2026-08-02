"""Run all canonical deterministic scenarios and write reviewable CSV evidence."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from filling_cell_simulator import SCENARIOS, FillingCellSimulator, SimulationConfig


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_and_write(output_dir: Path | None = None, config: SimulationConfig | None = None) -> list[object]:
    output_dir = output_dir or Path(__file__).resolve().parent / "outputs"
    trace_dir = output_dir / "traces"
    simulator = FillingCellSimulator(config)
    results = [simulator.run(name) for name in SCENARIOS]
    _write_csv(output_dir / "scenario_results.csv", [result.summary_row() for result in results])
    for result in results:
        _write_csv(trace_dir / f"{result.scenario}.csv", [sample.as_row() for sample in result.trace])
    metadata = {
        "evidence_type": "Independent deterministic Python plant/controller/interface simulation",
        "native_plcsim": "NOT RUN - PLCSIM/PLCSIM Advanced is not installed",
        "siemens_execution_claimed": False,
        "config": asdict(simulator.config),
        "scenario_count": len(results),
        "released_scenarios": [result.scenario for result in results if result.released],
        "invariant_violation_count": sum(len(result.invariant_violations) for result in results),
    }
    (output_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    return results


def main() -> int:
    results = run_and_write()
    output_dir = Path(__file__).resolve().parent / "outputs"
    print(f"Wrote {len(results)} scenario summaries to {output_dir / 'scenario_results.csv'}")
    print(f"Wrote time-step traces to {output_dir / 'traces'}")
    print("Evidence is independent simulation; Siemens/PLCSIM execution is not claimed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
