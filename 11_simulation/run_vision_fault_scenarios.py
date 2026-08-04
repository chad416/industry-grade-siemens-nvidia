from __future__ import annotations

import csv
import json
from pathlib import Path

from revision_f_vision_sil import run_all


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
results = run_all()
rows = [result.as_row() for result in results]

with (OUT / "vision_fault_results.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

(OUT / "vision_fault_results.json").write_text(
    json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
)
print(
    f"vision_sil_scenarios={len(rows)} releases={sum(bool(row['product_released']) for row in rows)} "
    f"unsafe_outputs={sum(bool(row['pump_cmd'] or row['valve_1_cmd'] or row['valve_2_cmd']) for row in rows)}"
)
