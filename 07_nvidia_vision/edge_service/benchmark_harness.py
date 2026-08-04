"""Development-only latency harness for a supplied callable.

Results are engineering observations for the named host/input/backend only. They
must not populate the production model card without target-hardware evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
import time
from typing import Callable


@dataclass(frozen=True)
class BenchmarkResult:
    iterations: int
    minimum_ms: float
    median_ms: float
    p95_ms: float
    maximum_ms: float
    throughput_per_second: float
    evidence_class: str = "DEVELOPMENT PIPELINE TIMING ONLY — NOT TARGET PERFORMANCE"


def _percentile(values: list[float], fraction: float) -> float:
    index = max(0, math.ceil(len(values) * fraction) - 1)
    return sorted(values)[index]


def benchmark(operation: Callable[[], object], *, warmup: int = 5,
              iterations: int = 50) -> BenchmarkResult:
    if type(warmup) is not int or warmup < 0 or type(iterations) is not int or iterations <= 0:
        raise ValueError("warmup must be nonnegative and iterations must be positive")
    for _ in range(warmup):
        operation()
    samples: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        operation()
        samples.append((time.perf_counter_ns() - start) / 1_000_000)
    total_seconds = sum(samples) / 1_000
    return BenchmarkResult(
        iterations=iterations,
        minimum_ms=min(samples),
        median_ms=statistics.median(samples),
        p95_ms=_percentile(samples, 0.95),
        maximum_ms=max(samples),
        throughput_per_second=iterations / total_seconds if total_seconds else float("inf"),
    )
